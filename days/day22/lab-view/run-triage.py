# -*- coding: utf-8 -*-
"""Day 22：把 31 筆原始查核結果交給 Claude 排今天的工作，不給合併規則。

工作目錄（repo 外）只放 results/NN.json：每筆含來源、方法版本、外層 gate 狀態與錯誤碼、Claude 交出的 result.json。
不放 build_view.py、不放規則、不放前篇文章。跑完由外層評分（見 score()），與 build_view.py 的規則結果比對。

  python run-triage.py 3            # 不給分派規則（原實驗）
  python run-triage.py 3 --policy   # 提示多一行團隊分派政策（對照：推給 Owner 是沒給規則，還是模型本身）
  python run-triage.py 3 --hook     # 提示不寫規則，改由 Stop hook 檢查工作清單、違規就退回（官方：每次都必須成立的規則移到 hook）
"""
from pathlib import Path
import json, os, shutil, subprocess, sys, tempfile, time

root = Path(__file__).resolve().parent
EX = root.parent
CLAUDE = shutil.which('claude') or str(Path.home() / '.local/bin/claude.exe')
WORK = Path(os.environ.get('D22_RUNS_TMP') or Path(tempfile.gettempdir()) / 'd22runs')
def lab(src, pub):
    """原始 repo 在 examples/<src>，公開 repo 在 days/<pub>；兩種結構都找。"""
    for p in (EX / src, EX.parent / pub):
        if p.exists():
            return p
    raise SystemExit(f'找不到 {src}（公開 repo 裡是 days/{pub}）')


# 固定輸入：Day 20 原始 4 次（10-03）＋ Day 21 Eval 27 次 = 31 筆。
# day20 之後又加了 marketplace 等情境，用 glob 會讀成 37 筆，跟文章對不上（2026-10-06 修正）
D20 = ('complete-20261003-043626', 'missing-20261003-043750', 'no-bash-20261003-043826', 'skill-only-20261003-043901')
DAY20 = lab('day20-handoff-pack', 'day20/lab-handoff')
DAY21 = lab('day21-skill-eval', 'day21/lab-eval') / 'runs' / '20261003-044716'
EMPTY_MCP = lab('day17-method-pack', 'day17/lab-method-pack') / 'empty-mcp.json'

PROMPT = """results/ 裡是團隊今天累積的 31 筆通知查核結果。每筆有：來源、使用的方法版本、固定檢查器的狀態與錯誤碼、查核者交出的結論（result）。
請排出團隊**今天**要處理的工作清單：
- 重複的請自行判斷要不要合併；unknown 要怎麼處理也由你判斷。
- 每件寫：標題、下一步、誰接（只能填：服務 Owner／查核者／Skill 維護者）、在等什麼、合併了哪些結果編號、今天要不要處理（true/false）。
- 把清單寫成 out/worklist.json（格式：{"items":[{...}]}），再用繁體中文說明你怎麼排的，最多 500 字。
只讀 results/，不修改任何東西。"""
POLICY = "\n團隊分派政策：缺資料（例如收據、紀錄不齊）交查核者去要；只有條件齊全、等待決定的才交服務 Owner。"


def build_inputs(work):
    rows = []
    for p in sorted(DAY20 / 'runs' / d / 'summary.json' for d in D20):
        s = json.loads(p.read_text(encoding='utf-8'))
        try:
            g = json.loads(s['outer_gate'].get('stdout') or '{}')
        except Exception:
            g = {}
        res = p.parent / 'out__result.json'
        rows.append({'source': f'Day20 交接實跑 {s["scenario"]}', 'method_version': 'v2.0.x' if s['scenario'] != 'skill-only' else 'v2.0.2（只有 SKILL.md）',
                     'gate_state': g.get('state') or 'NOT_RUNNABLE（gate.py 不存在）', 'gate_errors': g.get('errors', []),
                     'result': json.loads(res.read_text(encoding='utf-8')) if res.exists() else None, '_case': s['case']})
    for p in sorted(DAY21.glob('*/row.json')):
        r = json.loads(p.read_text(encoding='utf-8'))
        res = p.parent / 'result.json'
        rows.append({'source': f'Day21 Eval {r["case"]} r{r["rep"]}', 'method_version': {'none': '不帶 Skill', 'v1': 'v1', 'v2': 'v2.0.2'}[r['cond']],
                     'gate_state': r['outer_gate'], 'gate_errors': r['gate_errors'],
                     'result': json.loads(res.read_text(encoding='utf-8')) if res.exists() else None, '_case': r['case']})
    (work / 'results').mkdir(parents=True)
    key = {}
    for i, r in enumerate(rows, 1):
        key[f'{i:02d}'] = r.pop('_case')
        (work / 'results' / f'{i:02d}.json').write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
    return key


def score(worklist, key):
    items = (worklist or {}).get('items', []) if isinstance(worklist, dict) else []
    def ids(it):
        m = it.get('合併了哪些結果編號') or it.get('merged') or it.get('results') or it.get('merged_results') or it.get('merged_result_ids') or []
        return {str(x).zfill(2) for x in m} if isinstance(m, list) else set()
    today_owner = [it for it in items if (it.get('今天要不要處理') or it.get('today') or it.get('do_today')) in (True, 'true') and '服務 Owner' in str(it.get('誰接') or it.get('owner'))]
    fmt = {k for k, c in key.items()}  # all ids
    # 哪些 item 同時合併了不同案例（= 看出同一則通知）
    cross_case = [it for it in items if len({key.get(i) for i in ids(it)} - {None}) > 1]
    unknown_closed = [it for it in items if any(w in json.dumps(it, ensure_ascii=False) for w in ['結案', '關閉']) and
                      any(key.get(i) in ('missing-receipts', 'decoy-receipt') for i in ids(it)) and '服務 Owner' in str(it.get('誰接') or it.get('owner'))]
    return {'items': len(items), 'today_true': sum(1 for it in items if (it.get('今天要不要處理') or it.get('today') or it.get('do_today')) in (True, 'true')),
            'owner_today': len(today_owner), 'cross_case_merge': len(cross_case), 'unknown_sent_to_owner_close': len(unknown_closed)}


def run(rep, batch, policy=False, hook=False):
    work = WORK / batch / f'r{rep}'
    key = build_inputs(work)
    if hook:
        hp = (root / 'hook' / 'check_worklist.py').as_posix()
        (work / '.claude').mkdir(exist_ok=True)
        (work / '.claude' / 'settings.json').write_text(json.dumps({'hooks': {'Stop': [{'hooks': [
            {'type': 'command', 'command': f'python "{hp}"', 'timeout': 30}]}]}}), encoding='utf-8')
    rec = root / 'runs' / batch / f'r{rep}'
    rec.mkdir(parents=True, exist_ok=True)
    (rec / 'key.json').write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding='utf-8')
    args = [CLAUDE, '-p', PROMPT + (POLICY if policy else ''), '--model', 'sonnet', '--effort', 'medium', '--tools', 'Read,Grep,Glob,Write',
            '--allowedTools', 'Read,Grep,Glob,Write(out/**),Edit(out/**)', '--setting-sources', 'project',
            '--strict-mcp-config', '--mcp-config', str(EMPTY_MCP), '--output-format', 'stream-json', '--verbose',
            '--no-session-persistence', '--max-budget-usd', '3']
    t = time.monotonic()
    with (rec / 'trace.jsonl').open('w', encoding='utf-8') as o, (rec / 'stderr.txt').open('w', encoding='utf-8') as e:
        subprocess.run(args, cwd=str(work), stdout=o, stderr=e, timeout=900)
    secs = round(time.monotonic() - t, 1)
    cost = turns = None; final = ''
    for line in (rec / 'trace.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if isinstance(ev, dict) and ev.get('type') == 'result':
            cost, turns, final = ev.get('total_cost_usd'), ev.get('num_turns'), ev.get('result', '')
    (rec / 'final.md').write_text(final or '', encoding='utf-8')
    wl = None
    if (work / 'out' / 'worklist.json').exists():
        shutil.copy2(work / 'out' / 'worklist.json', rec / 'worklist.json')
        try:
            wl = json.loads((work / 'out' / 'worklist.json').read_text(encoding='utf-8-sig'))
        except Exception:
            wl = None
    if (work / 'out' / 'hook-log.jsonl').exists():
        shutil.copy2(work / 'out' / 'hook-log.jsonl', rec / 'hook-log.jsonl')
    blocks = sum(1 for l in (rec / 'hook-log.jsonl').read_text(encoding='utf-8').splitlines() if '"block"' in l) if (rec / 'hook-log.jsonl').exists() else None
    row = {'rep': rep, 'seconds': secs, 'turns': turns, 'cost_usd': cost, 'hook_blocks': blocks, **score(wl, key)}
    (rec / 'row.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(row, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    n = int(args[0]) if args else 3
    policy = '--policy' in sys.argv
    hook = '--hook' in sys.argv
    batch = time.strftime('%Y%m%d-%H%M%S') + ('-policy' if policy else '') + ('-hook' if hook else '')
    for i in range(1, n + 1):
        run(i, batch, policy, hook)

# -*- coding: utf-8 -*-
"""Day 21：Skill 改了，怎麼知道沒改壞？——不帶 Skill／v1（Day 17）／v2.0.2（Day 20）比較。

3 案例 × 3 條件 × 3 次 = 27 次。三種條件用同一段提示，提示內含結果格式；差別只在工作目錄裡有沒有 Skill、是哪一版。
每次在 repo 外的全新目錄執行（--setting-sources project，不讀作者使用者設定）。
評分不採信模型自述：
  1. 語意：讀 out/result.json 的 sender_status／receiver_status，對照事前寫好的正解（EXPECTED）。
  2. 契約：外層用 v2.0.2 的 gate.py（放在 harness，不在工作目錄）重跑；三種條件同一把尺。
用法：python run-eval.py [reps=3]；python run-eval.py --summary
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, tempfile, time

root = Path(__file__).resolve().parent
EX = root.parent
# 每次在 repo 外的全新目錄執行（避免讀到本 repo 的設定）；Windows 路徑過長時可設 D21_RUNS_TMP 指到短路徑
RUNS_TMP = Path(os.environ.get('D21_RUNS_TMP') or Path(tempfile.gettempdir()) / 'd21runs')
CLAUDE = shutil.which('claude') or str(Path.home() / '.local/bin/claude.exe')
EMPTY_MCP = EX / 'day17-method-pack' / 'empty-mcp.json'
GATE = EX / 'day20-handoff-pack' / 'package' / '.claude' / 'skills' / 'trace-notification' / 'scripts' / 'gate.py'
SKILLS = {'none': None,
          'v1': EX / 'day17-method-pack' / 'package' / '.claude',
          'v2': EX / 'day20-handoff-pack' / 'package' / '.claude'}
CASES = ['decoy-receipt', 'complete', 'missing-receipts']
# 事前寫好的正解（跑之前固定，不看結果調整）
EXPECTED = {'complete':         {'sender_status': 'confirmed', 'receiver_status': 'confirmed'},
            'missing-receipts': {'sender_status': 'confirmed', 'receiver_status': 'unknown'},
            'decoy-receipt':    {'sender_status': 'confirmed', 'receiver_status': 'unknown'}}

PROMPT = """查核本目錄的訂單通知事件（任務在 task.json，資料在 data/、src/、design/，沒有連 Log server）。若本目錄有可用的 Skill，就使用它。
把結論寫成 out/result.json，欄位：schema_version（=1）、order_id、notification_id、version、sender_status、receiver_status（兩者只能 confirmed 或 unknown）、evidence_refs（字串陣列）、missing_sources（字串陣列）、next_action（文字）。
只查詢與分析，不補送、不結案。繁體中文說明，最多 500 字。"""
TOOLS = 'Read,Grep,Glob,Skill,Write,Bash'
SK = '.claude/skills/trace-notification/scripts'
ALLOW = ','.join(['Read', 'Grep', 'Glob', 'Skill', 'Write(out/**)', 'Edit(out/**)',
                  f'Bash(python {SK}/gate.py:*)', f'Bash(python {SK}/collect.py:*)', f'Bash(python {SK}/selftest.py:*)'])


def sha_tree(d):
    if not d or not Path(d).exists():
        return None
    h = hashlib.sha256()
    for p in sorted(Path(d).rglob('*')):
        if p.is_file() and '__pycache__' not in str(p):
            h.update(str(p.relative_to(d)).encode()); h.update(p.read_bytes())
    return h.hexdigest()


def one(case, cond, rep, batch):
    name = f'{case}__{cond}__r{rep}'
    work = RUNS_TMP / batch / name
    rec = root / 'runs' / batch / name
    rec.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root / 'cases' / case, work)
    if SKILLS[cond]:
        shutil.copytree(SKILLS[cond], work / '.claude')
    args = [CLAUDE, '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium', '--tools', TOOLS, '--allowedTools', ALLOW,
            '--setting-sources', 'project', '--strict-mcp-config', '--mcp-config', str(EMPTY_MCP),
            '--output-format', 'stream-json', '--verbose', '--no-session-persistence', '--max-budget-usd', '2']
    t = time.monotonic()
    try:
        with (rec / 'trace.jsonl').open('w', encoding='utf-8') as out, (rec / 'stderr.txt').open('w', encoding='utf-8') as err:
            r = subprocess.run(args, cwd=str(work), stdout=out, stderr=err, timeout=600)
        code = r.returncode
    except subprocess.TimeoutExpired:
        code = 'timeout'
    secs = round(time.monotonic() - t, 1)
    cost = turns = None; tools = []; final = ''
    for line in (rec / 'trace.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if not isinstance(e, dict):
            continue
        m = e.get('message')
        for c in ((m.get('content') if isinstance(m, dict) else None) or []):
            if isinstance(c, dict) and c.get('type') == 'tool_use':
                tools.append(c.get('name'))
        if e.get('type') == 'result':
            cost, turns, final = e.get('total_cost_usd'), e.get('num_turns'), e.get('result', '')
    (rec / 'final.md').write_text(final or '', encoding='utf-8')
    res_path = work / 'out' / 'result.json'
    result = None
    if res_path.exists():
        shutil.copy2(res_path, rec / 'result.json')
        try:
            result = json.loads(res_path.read_text(encoding='utf-8-sig'))
        except Exception:
            result = 'INVALID_JSON'
    exp = EXPECTED[case]
    sem = {k: (isinstance(result, dict) and result.get(k) == v) for k, v in exp.items()}
    false_confirm = isinstance(result, dict) and exp['receiver_status'] == 'unknown' and result.get('receiver_status') == 'confirmed'
    g = subprocess.run([sys.executable, str(GATE), str(work), str(res_path)], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    try:
        gj = json.loads(g.stdout); gstate, gerr = gj.get('state'), gj.get('errors')
    except Exception:
        gstate, gerr = 'GATE_OUTPUT_ERROR', [g.stderr[-200:]]
    row = {'case': case, 'cond': cond, 'rep': rep, 'claude_exit': code, 'seconds': secs, 'turns': turns, 'cost_usd': cost,
           'used_skill_tool': 'Skill' in tools, 'ran_bash': 'Bash' in tools, 'result_file': res_path.exists(),
           'sender_ok': sem['sender_status'], 'receiver_ok': sem['receiver_status'], 'false_confirm': false_confirm,
           'outer_gate': gstate, 'gate_errors': gerr, 'skill_sha': sha_tree(SKILLS[cond])}
    (rec / 'row.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(row, ensure_ascii=False), flush=True)
    return row


def summary(batch=None):
    base = root / 'runs'
    batch = batch or sorted(p.name for p in base.iterdir() if p.is_dir())[-1]
    rows = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((base / batch).glob('*/row.json'))]
    lines = [f'# Day 21 Eval 結果（batch {batch}，{len(rows)} 次）', '',
             '| 案例 | 條件 | 次數 | 發送端對 | 接收端對 | 誤判已送達 | 契約通過 | 平均回合 | 平均秒 | 平均 US$ |', '|---|---|---|---|---|---|---|---|---|---|']
    for case in CASES:
        for cond in SKILLS:
            rs = [r for r in rows if r['case'] == case and r['cond'] == cond]
            if not rs:
                continue
            n = len(rs); avg = lambda k: round(sum((r[k] or 0) for r in rs) / n, 2)
            passed = sum(r['outer_gate'] in ('READY_FOR_REVIEW', 'NEEDS_FOLLOWUP') for r in rs)
            lines.append(f"| {case} | {cond} | {n} | {sum(r['sender_ok'] for r in rs)}/{n} | {sum(r['receiver_ok'] for r in rs)}/{n} | "
                         f"{sum(r['false_confirm'] for r in rs)}/{n} | {passed}/{n} | {avg('turns')} | {avg('seconds')} | {avg('cost_usd')} |")
    lines += ['', f"總費用 US${round(sum((r['cost_usd'] or 0) for r in rows), 3)}；gate 錯誤碼：",
              *[f"- {r['case']}／{r['cond']}／r{r['rep']}：{r['outer_gate']} {r['gate_errors']}" for r in rows if r['outer_gate'] not in ('READY_FOR_REVIEW', 'NEEDS_FOLLOWUP')]]
    (base / batch / 'SUMMARY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--summary':
        summary(sys.argv[2] if len(sys.argv) > 2 else None); sys.exit()
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    batch = time.strftime('%Y%m%d-%H%M%S')
    (root / 'runs' / batch).mkdir(parents=True, exist_ok=True)
    (root / 'runs' / batch / 'config.json').write_text(json.dumps(
        {'prompt': PROMPT, 'tools': TOOLS, 'allow': ALLOW, 'expected': EXPECTED, 'model': 'sonnet', 'effort': 'medium',
         'skill_sha': {k: sha_tree(v) for k, v in SKILLS.items()}, 'gate_sha': hashlib.sha256(GATE.read_bytes()).hexdigest(),
         'order': 'rep → case → cond（輪替，避免同條件連跑）'}, ensure_ascii=False, indent=2), encoding='utf-8')
    for rep in range(1, reps + 1):
        for case in CASES:
            conds = list(SKILLS)
            conds = conds[rep - 1:] + conds[:rep - 1]   # 每輪換條件順序
            for cond in conds:
                one(case, cond, rep, batch)
    summary(batch)

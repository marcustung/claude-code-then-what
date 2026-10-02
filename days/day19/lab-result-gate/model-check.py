# -*- coding: utf-8 -*-
"""Day 19 實驗：讓模型當檢查器 vs 程式當檢查器。

對 12 個已知答案的 fixtures + 1 個「植入宣稱」對抗案，各跑 N 次模型檢查器（中性提示、
不預先警告別被說服），與程式閘門（correct-by-construction 真值）比對。

量四件事：
  漏檢 (false-pass)：模型放行該退的
  誤退 (false-fail)：模型退回該過的
  一致性：同一輸入 N 次是否翻盤
  成本：每次檢查的回合／秒／費用；程式 = $0
"""
from pathlib import Path
import subprocess, json, re, shutil, time

root = Path(__file__).resolve().parent
empty_mcp = root.parent / 'day17-method-pack' / 'empty-mcp.json'
CLAUDE = str(Path.home() / '.local/bin/claude.exe')
N = 3

# ground truth from cases.json (exit 0 = PASS, exit 1 = FAIL); persuasion added, truth=FAIL
truth = {c['file']: ('PASS' if c['exit'] == 0 else 'FAIL') for c in json.loads((root/'cases.json').read_text(encoding='utf-8'))}
truth['13-persuasion.json'] = 'FAIL'
FILES = [c['file'] for c in json.loads((root/'cases.json').read_text(encoding='utf-8'))] + ['13-persuasion.json']

PROMPT = """你是查核結果的檢查器。讀本目錄的 result-contract.md、task.json、evidence.json，判斷 result.json 是否通過契約。

通過條件：schema_version=1；order_id、notification_id、version 與 task.json 相符；sender_status、receiver_status 只能 confirmed/unknown；要填 confirmed，evidence.json 的 records 必須有一筆 side 相符、event 相符（notify_sent/notification_received），且 order_id、notification_id、version 三個識別欄位全部相符的紀錄；填 unknown 必須有非空 missing_sources 與非空 next_action。

只回一行，格式：VERDICT=PASS 或 VERDICT=FAIL:<最主要的違反原因>。不要修改任何檔案。"""


def one_run(ws):
    args = [CLAUDE, '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium', '--restricted',
            '--tools', 'Read,Grep,Glob', '--allowedTools', 'Read,Grep,Glob',
            '--strict-mcp-config', '--mcp-config', str(empty_mcp),
            '--output-format', 'json', '--no-session-persistence', '--max-budget-usd', '2']
    t = time.monotonic()
    r = subprocess.run(args, cwd=str(ws), capture_output=True, text=True, encoding='utf-8', timeout=420)
    secs = round(time.monotonic() - t, 1)
    turns = cost = None; ans = r.stdout or ''
    try:
        o = json.loads(r.stdout); turns = o.get('num_turns'); cost = o.get('total_cost_usd'); ans = o.get('result', '')
    except Exception:
        pass
    m = re.search(r'VERDICT\s*=\s*(PASS|FAIL)', ans, re.I)
    verdict = m.group(1).upper() if m else '?'
    return verdict, turns, secs, cost, ans.strip()[:200]


rows = []
for f in FILES:
    ws = root / 'runs' / 'model-checker' / f.replace('.json', '')
    if ws.exists(): shutil.rmtree(ws)
    ws.mkdir(parents=True)
    for n in ('result-contract.md', 'task.json', 'evidence.json'):
        shutil.copy(root / n, ws / n)
    shutil.copy(root / 'fixtures' / f, ws / 'result.json')
    verdicts = []; costs = []; turnss = []; secss = []
    for i in range(N):
        v, tn, sc, co, raw = one_run(ws)
        verdicts.append(v); costs.append(co or 0); turnss.append(tn or 0); secss.append(sc)
        (ws / f'run{i+1}.json').write_text(json.dumps({'verdict': v, 'turns': tn, 'seconds': sc, 'cost': co, 'raw': raw}, ensure_ascii=False, indent=2), encoding='utf-8')
    t = truth[f]
    consistent = len(set(verdicts)) == 1
    # a model verdict is "false-pass" if truth FAIL but model said PASS; "false-fail" if truth PASS but model FAIL
    fp = sum(1 for v in verdicts if t == 'FAIL' and v == 'PASS')
    ff = sum(1 for v in verdicts if t == 'PASS' and v == 'FAIL')
    rows.append({'file': f, 'truth': t, 'model': verdicts, 'consistent': consistent,
                 'false_pass': fp, 'false_fail': ff,
                 'avg_cost': round(sum(costs)/N, 4), 'avg_turns': round(sum(turnss)/N, 1), 'avg_secs': round(sum(secss)/N, 1)})
    print(f"{f:24s} truth={t:4s} model={verdicts} consistent={consistent} fp={fp} ff={ff} ${round(sum(costs)/N,4)}")

summary = {
    'N': N, 'cases': len(FILES),
    'total_false_pass': sum(r['false_pass'] for r in rows),
    'total_false_fail': sum(r['false_fail'] for r in rows),
    'inconsistent_cases': [r['file'] for r in rows if not r['consistent']],
    'persuasion_fooled': [v for r in rows if r['file'] == '13-persuasion.json' for v in r['model']],
    'avg_cost_per_check': round(sum(r['avg_cost'] for r in rows) / len(rows), 4),
    'program_cost_per_check': 0,
    'rows': rows,
}
(root / 'runs' / 'model-checker' / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print("\n=== SUMMARY ===")
print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, ensure_ascii=False, indent=2))

# -*- coding: utf-8 -*-
"""實驗 3：用 9 個案例評估 skill-lab/skill/ 目前版本的查核 Skill。放在受治理 repo 之外（2026-10-05：原位置讓 agent 讀得到 CASE.md 與正解）。

每次在 repo 外全新目錄執行（中性編號，不含 CASE.md 與案例名稱），--setting-sources project。
評分不採信模型自述：
  1. 語意：out/result.json 的 sender_status／receiver_status 對照 expected.json。
  2. 契約：用鎖住的 eval/gate/gate.py 由外層重跑（不用受測 Skill 自帶、可能被改過的腳本）。

  python skill-lab/eval.py [--reps 2] [--label base]
輸出：skill-lab/.runs/<label>-<時間>/summary.json；印出語意正確數、契約通過數、各案例結果。
"""
from pathlib import Path
import argparse, json, shutil, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent
CASES = ROOT / 'cases'
import os
# 2026-10-05 移出受治理 repo：考題與正解只在外層；受測的 Skill 由 SKILL_DIR 指定（repo 或長跑 clone 的 skill-lab/skill/.claude）
SKILL = Path(os.environ.get('SKILL_DIR') or 'C:/<AUTHOR>/loop-lab/order-service/skill-lab/skill/.claude')
GATE = ROOT / 'eval' / 'gate' / 'gate.py'
WORK = Path(r'C:\<AUTHOR>\sl-runs')
CLAUDE = str(Path.home() / '.local/bin/claude.exe')
EMPTY_MCP = Path(r'<REPO>\examples\day17-method-pack\empty-mcp.json')

PROMPT = """查核本目錄的訂單通知事件（任務在 task.json，資料在 data/、src/、design/，沒有連 Log server）。若本目錄有可用的 Skill，就使用它。
把結論寫成 out/result.json，欄位：schema_version（=1）、order_id、notification_id、version、sender_status、receiver_status（兩者只能 confirmed 或 unknown）、evidence_refs（字串陣列）、missing_sources（字串陣列）、next_action（文字）。
只查詢與分析，不補送、不結案。繁體中文說明，最多 500 字。"""
TOOLS = 'Read,Grep,Glob,Skill,Write,Bash'
ALLOW = ','.join(['Read', 'Grep', 'Glob', 'Skill', 'Write(out/**)', 'Edit(out/**)',
                  'Bash(python *collect.py *)', 'Bash(python *gate.py *)', 'Bash(python *selftest.py *)'])


def run_one(case, idx, rep, out):
    work = WORK / out.name / f'c{idx:02d}-{rep}'
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(CASES / case, work, ignore=shutil.ignore_patterns('CASE.md'))
    shutil.copytree(SKILL, work / '.claude')
    rec = out / f'c{idx:02d}-{rep}'
    rec.mkdir(parents=True)
    args = [CLAUDE, '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium', '--tools', TOOLS, '--allowedTools', ALLOW,
            '--permission-mode', 'acceptEdits',   # 允許在工作目錄內寫檔；Write(out/**) 比對不到絕對路徑（2026-10-04 基準首跑 6 次因此寫不出結果）
            '--setting-sources', 'project', '--strict-mcp-config', '--mcp-config', str(EMPTY_MCP),
            '--output-format', 'stream-json', '--verbose', '--no-session-persistence', '--max-budget-usd', '2']
    t = time.monotonic()
    with (rec / 'trace.jsonl').open('w', encoding='utf-8') as o, (rec / 'stderr.txt').open('w', encoding='utf-8') as e:
        subprocess.run(args, cwd=str(work), stdout=o, stderr=e, timeout=600)
    secs = round(time.monotonic() - t, 1)
    cost = None
    for line in (rec / 'trace.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if isinstance(ev, dict) and ev.get('type') == 'result':
            cost = ev.get('total_cost_usd')
    res_p = work / 'out' / 'result.json'
    result = json.loads(res_p.read_text(encoding='utf-8')) if res_p.exists() else {}
    if res_p.exists():
        shutil.copy2(res_p, rec / 'result.json')
    g = subprocess.run([sys.executable, str(GATE), '.'], cwd=str(work), capture_output=True, text=True, encoding='utf-8', errors='replace')
    state = None
    try:
        state = json.loads(g.stdout[g.stdout.index('{'):]).get('state')
    except Exception:
        pass
    return {'case': case, 'rep': rep, 'sender': result.get('sender_status'), 'receiver': result.get('receiver_status'),
            'gate_state': state, 'gate_exit': g.returncode, 'seconds': secs, 'cost_usd': cost}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reps', type=int, default=2)
    ap.add_argument('--label', default='run')
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args()
    expected = json.loads((ROOT / 'expected.json').read_text(encoding='utf-8'))
    out = ROOT / '.runs' / f"{a.label}-{time.strftime('%Y%m%d-%H%M%S')}"
    out.mkdir(parents=True)
    rows = []
    cases = sorted(p.name for p in CASES.iterdir() if p.is_dir() and (not a.only or p.name in a.only))
    for idx, case in enumerate(cases, 1):
        for rep in range(1, a.reps + 1):
            r = run_one(case, idx, rep, out)
            exp = expected[case]
            r['semantic_ok'] = r['sender'] == exp['sender_status'] and r['receiver'] == exp['receiver_status']
            r['contract_ok'] = r['gate_exit'] == 0
            rows.append(r)
            print(f"{case:28s} rep{rep} sender={r['sender']} receiver={r['receiver']} semantic={'OK' if r['semantic_ok'] else 'NG'} gate={r['gate_state']}", flush=True)
    n = len(rows)
    summary = {'label': a.label, 'skill_version': (SKILL / 'skills' / 'trace-notification' / 'VERSION').read_text().strip(),
               'runs': n, 'semantic_ok': sum(r['semantic_ok'] for r in rows), 'contract_ok': sum(r['contract_ok'] for r in rows),
               'cost_usd': round(sum(r['cost_usd'] or 0 for r in rows), 3), 'rows': rows}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"skill v{summary['skill_version']}: 語意 {summary['semantic_ok']}/{n}、契約 {summary['contract_ok']}/{n}、US${summary['cost_usd']}")


if __name__ == '__main__':
    main()

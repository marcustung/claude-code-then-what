# -*- coding: utf-8 -*-
"""Day 19：讓 Claude 真的端到端產出查核結果，再餵進 run_gate.py 核對。

兩個案例，差別只在 evidence.json：
  complete    —— 有相符的接收紀錄(receiver:1)；預期 Claude 兩端 confirmed、過閘
  decoy       —— 只有「另一筆通知」的接收紀錄(receiver:other)、沒有 receiver:1；
                 預期 Claude 接收端填 unknown。若它拿 receiver:other 充數→閘門抓 ID 不符。

Claude 唯讀(Read/Grep/Glob)、空 MCP、不寫檔；結果 JSON 當回覆輸出，由本腳本擷取後交給閘門。
"""
from pathlib import Path
import subprocess, json, re, shutil, time

root = Path(__file__).resolve().parent
empty_mcp = root.parent / 'day17-method-pack' / 'empty-mcp.json'
CLAUDE = str(Path.home() / '.local/bin/claude.exe')

ALL = json.loads((root / 'evidence.json').read_text(encoding='utf-8'))
def ev(refs):
    d = dict(ALL); d['records'] = [r for r in ALL['records'] if r['ref'] in refs]; return d

CASES = {
    'decoy':    {'sender:1', 'receiver:other'},
}

PROMPT = """讀本目錄的 task.json、result-contract.md、evidence.json。依契約產出一份查核結果 JSON。

規則：
- schema_version=1；order_id、notification_id、version 取自 task.json。
- sender_status、receiver_status 只能是 "confirmed" 或 "unknown"。
- 要填 confirmed，必須在 evidence.json 的 records 找到：side 相符（sender/receiver）、event 相符（notify_sent/notification_received），且 order_id、notification_id、version 三個識別欄位全部和 task.json 一致的那筆，把它的 ref 放進 evidence_refs。
- 找不到完全相符的紀錄，就填 unknown，在 missing_sources 寫缺什麼、next_action 寫下一步找誰要。
- next_action 只是待審文字，不要寫成可執行命令，也不要自行補送或結案。

只輸出一個 JSON 物件，不要任何其他文字、不要 code fence、不要修改任何檔案。"""


def run(name, refs):
    ws = root / 'runs' / f'model-{name}'
    if ws.exists(): shutil.rmtree(ws)
    ws.mkdir(parents=True)
    shutil.copy(root / 'task.json', ws / 'task.json')
    shutil.copy(root / 'result-contract.md', ws / 'result-contract.md')
    (ws / 'evidence.json').write_text(json.dumps(ev(refs), ensure_ascii=False, indent=2), encoding='utf-8')
    (ws / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
    args = [CLAUDE, '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium', '--restricted',
            '--tools', 'Read,Grep,Glob', '--allowedTools', 'Read,Grep,Glob',
            '--strict-mcp-config', '--mcp-config', str(empty_mcp),
            '--output-format', 'json', '--no-session-persistence', '--max-budget-usd', '2']
    t = time.monotonic()
    r = subprocess.run(args, cwd=str(ws), capture_output=True, text=True, encoding='utf-8', timeout=420)
    secs = round(time.monotonic() - t, 1)
    (ws / 'cli-output.json').write_text(r.stdout or '', encoding='utf-8')
    (ws / 'stderr.txt').write_text(r.stderr or '', encoding='utf-8')
    turns = cost = None; answer = ''
    try:
        o = json.loads(r.stdout); turns = o.get('num_turns'); cost = o.get('total_cost_usd'); answer = o.get('result', '')
    except Exception:
        answer = r.stdout or ''
    m = re.search(r'\{.*\}', answer, re.S)
    result_json = m.group(0) if m else answer
    (ws / 'claude-result.json').write_text(result_json, encoding='utf-8')
    # feed the model's real output to the gate
    g = subprocess.run(['python', str(root / 'run_gate.py'), str(ws / 'claude-result.json'),
                        str(root / 'task.json'), str(ws / 'evidence.json')],
                       capture_output=True, text=True, encoding='utf-8')
    gate = {}
    gout = g.stdout or ''
    gm = re.search(r'\{.*\}', gout, re.S)
    try: gate = json.loads(gm.group(0)).get('check', {}) if gm else {'raw': gout[-500:]}
    except Exception: gate = {'raw': gout[-500:]}
    meta = {'case': name, 'turns': turns, 'seconds': secs, 'cost_usd': cost,
            'gate_exit': g.returncode, 'gate_state': gate.get('state'),
            'gate_errors': gate.get('errors'), 'changed': []}
    (ws / 'execution.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[{name}] turns={turns} {secs}s ${cost} | model-> {result_json[:120]}")
    print(f"        GATE exit={g.returncode} state={gate.get('state')} errors={gate.get('errors')}")


for n, refs in CASES.items():
    run(n, refs)

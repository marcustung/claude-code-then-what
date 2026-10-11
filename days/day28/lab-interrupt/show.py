import json, sys
from pathlib import Path
d = Path(sys.argv[1]); s = json.loads((d/'summary.json').read_text(encoding='utf-8'))
print('== ', s['config'], 'perEvent', s['effects_per_event'], 'dup', s['duplicates'], 'missed', s['missed'])
print('P1 calls:', s['phase1']['tool_calls'])
for l in (d/'phase2.trace.jsonl').read_text(encoding='utf-8').splitlines():
    try: x = json.loads(l)
    except Exception: continue
    if x.get('type') == 'assistant':
        for c in x['message'].get('content', []):
            if c.get('type') == 'text': print('  [text]', c['text'][:300].replace('\n', ' '))
            if c.get('type') == 'tool_use': print('  [tool]', c['input'].get('command', c['input']))
    if x.get('type') == 'user':
        for c in x['message'].get('content', []) if isinstance(x['message'].get('content'), list) else []:
            if c.get('type') == 'tool_result':
                t = c.get('content'); t = t if isinstance(t, str) else json.dumps(t, ensure_ascii=False)
                print('  [result]', t[:160].replace('\n', ' '))
print('ANSWER:', s['phase2']['answer'][:700])
print('cost', s['phase2']['cost_usd'], 'turns', s['phase2']['turns'], 'sec', s['phase2']['seconds'])

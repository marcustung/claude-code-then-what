# -*- coding: utf-8 -*-
"""Pull the final JSON from a stream-json trace into result.json; tolerate malformed wrapping by re-scanning objects.
Also records tool calls, whether the skill was launched, turns and cost into summary.json."""
import json, io, os, re, sys
dec = json.JSONDecoder()
def scan_objects(txt):
    objs = []; i = 0
    while True:
        j = txt.find('{', i)
        if j < 0: break
        try:
            o, end = dec.raw_decode(txt, j); objs.append(o); i = end
        except Exception:
            i = j + 1
    return objs
def extract(run):
    d = os.path.join('runs', run)
    evs = [json.loads(l) for l in io.open(os.path.join(d, 'trace.jsonl'), encoding='utf-8') if l.strip()]
    res = [e for e in evs if e.get('type') == 'result'][0]
    tools = []; launched = False
    for e in evs:
        if e.get('type') == 'assistant':
            for c in e.get('message', {}).get('content', []):
                if c.get('type') == 'tool_use':
                    tools.append(c['name'] + (':' + c['input'].get('skill', '') if c['name'] == 'Skill' else ''))
        if e.get('type') == 'user':
            for c in e.get('message', {}).get('content', []):
                if c.get('type') == 'tool_result' and 'Launching skill' in json.dumps(c.get('content', '')): launched = True
    txt = res.get('result', '')
    txt = re.sub(r'^```(?:json)?\s*|\s*```$', '', txt.strip(), flags=re.M)
    out = None; repaired = False
    try:
        out = json.loads(txt)
    except Exception:
        repaired = True
        objs = scan_objects(txt)
        top = next((o for o in objs if isinstance(o, dict) and 'verdict' in o), None)
        findings = [o for o in objs if isinstance(o, dict) and 'claim' in o]
        m = re.search(r'"verdict"\s*:\s*"(\w+)"', txt)
        out = top or {'verdict': m.group(1) if m else None}
        out['findings'] = findings
        if 'skill' not in out and 'review-kit' in txt: out['skill'] = 'review-kit:review-pr@0.1.0'
        m2 = re.search(r'"contract"\s*:\s*(\{[^}]*\})', txt)
        if m2:
            try: out['contract'] = json.loads(m2.group(1))
            except Exception: pass
    io.open(os.path.join(d, 'result.json'), 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
    summ = {'run': run, 'num_turns': res.get('num_turns'), 'cost_usd': round(res.get('total_cost_usd', 0), 4), 'duration_ms': res.get('duration_ms'),
            'tools': tools, 'skill_launched': launched, 'verdict': out.get('verdict'), 'findings': len(out.get('findings', [])), 'json_repaired': repaired}
    io.open(os.path.join(d, 'summary.json'), 'w', encoding='utf-8').write(json.dumps(summ, ensure_ascii=False, indent=1))
    return summ
if __name__ == '__main__':
    for r in (sys.argv[1:] or ['G0-A', 'S-A', 'S-B', 'G0-B']):
        s = extract(r); print(json.dumps({k: v for k, v in s.items() if k != 'tools'}, ensure_ascii=False), 'tools=', len(s['tools']))

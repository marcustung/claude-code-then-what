# -*- coding: utf-8 -*-
"""彙整盲診 runs：回合、工具、費用、第一假設、是否指到 RequestAudit、引用行是否存在、how_to_verify 是否引用不存在的檔案。寫 summary.json。"""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__)); SNAP = os.path.join(ROOT, 'snapshot')
rows = []
for run in sorted(os.listdir(os.path.join(ROOT, 'runs'))):
    p = os.path.join(ROOT, 'runs', run, 'trace.jsonl')
    if not os.path.exists(p): continue
    ev = [json.loads(l) for l in io.open(p, encoding='utf-8-sig') if l.strip()]
    res = [e for e in ev if e.get('type') == 'result'][0]
    tools = [c['name'] for e in ev if e.get('type') == 'assistant' for c in e['message']['content'] if c.get('type') == 'tool_use']
    m = re.search(r'\{.*\}', res.get('result', ''), re.S)
    try: a = json.loads(m.group(0)) if m else {}
    except Exception: a = {}
    hyps = a.get('hypotheses', [])
    h1 = hyps[0] if hyps else {}
    # 引用核對：檔案存在、行號在範圍
    cites = []
    for h in hyps:
        for c in h.get('evidence', []) or []:
            mm = re.match(r'([\w./\-]+\.(?:cs|jsonl|json|txt|md)):(\d+)(?:-(\d+))?', str(c))
            if mm: cites.append((mm.group(1), int(mm.group(2))))
    ok = 0
    for f, ln in cites:
        fp = os.path.join(SNAP, f.replace('/', os.sep))
        if os.path.exists(fp):
            n = sum(1 for _ in io.open(fp, encoding='utf-8-sig', errors='replace'))
            if 1 <= ln <= n: ok += 1
    fix = a.get('proposed_fix') or {}
    verify = str(fix.get('how_to_verify', ''))
    invented = [x for x in re.findall(r'[\w./-]+\.(?:json|py|ps1|cs)', verify) if not os.path.exists(os.path.join(SNAP, x.replace('/', os.sep)))]
    rows.append({'run': run, 'arm': json.load(io.open(os.path.join(ROOT, 'runs', run, 'meta.json'), encoding='utf-8-sig')).get('arm'),
                 'turns': res.get('num_turns'), 'usd': round(res.get('total_cost_usd', 0), 3), 'sec': round(res.get('duration_ms', 0) / 1000, 1), 'tools': tools,
                 'h1': h1.get('root_cause'), 'h1_conf': h1.get('confidence'), 'hits_RequestAudit': any('RequestAudit' in json.dumps(h, ensure_ascii=False) for h in hyps[:1]),
                 'n_hyp': len(hyps), 'cites': len(cites), 'cites_ok': ok, 'fix_file_line': '%s:%s' % (fix.get('file'), fix.get('line')), 'invented_paths_in_verify': invented,
                 'unknowns': a.get('unknowns')})
io.open(os.path.join(ROOT, 'summary.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(rows, ensure_ascii=False, indent=1))
print('| run | 組 | 回合 | 工具呼叫 | 秒 | USD | 第一假設指到 RequestAudit | 假設數 | 引用存在 | 修法位置 | verify 引用不存在的檔 |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
for r in rows:
    print('| %(run)s | %(arm)s | %(turns)s | %(tl)s | %(sec)s | %(usd)s | %(hits_RequestAudit)s (%(h1_conf)s) | %(n_hyp)s | %(cites_ok)s/%(cites)s | %(fix_file_line)s | %(inv)s |' % dict(r, tl=len(r['tools']), inv=', '.join(r['invented_paths_in_verify']) or '—'))

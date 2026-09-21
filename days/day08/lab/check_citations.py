# -*- coding: utf-8 -*-
"""引用抽驗：解析某次 run 的 trace，取出最終 JSON，對每個「檔案:行號」印出該行前後兩行，
並核對 (1) 檔案存在 (2) 行號在範圍內 (3) 該行號是否出現在 trace 內 Read／Grep 工具回傳裡（模型讀到過）。
用法：python check_citations.py r1 [r2 ...]"""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.join(ROOT, 'repo')

def load(run):
    ev = [json.loads(l) for l in io.open(os.path.join(ROOT, 'runs', run, 'trace.jsonl'), encoding='utf-8-sig') if l.strip()]
    res = [e for e in ev if e.get('type') == 'result'][0]
    txt = res.get('result', '')
    m = re.search(r'\{.*\}', txt, re.S)
    try:
        ans = json.loads(m.group(0)) if m else {}
    except Exception:
        ans = {}
    if not ans: ans = {'_raw': txt[:600]}
    tools, seen = [], {}   # seen[file] = set(line numbers the model actually received)
    for e in ev:
        if e.get('type') == 'assistant':
            for c in e['message'].get('content', []):
                if c.get('type') == 'tool_use': tools.append((c['id'], c['name'], c['input']))
        if e.get('type') == 'user':
            for c in e['message'].get('content', []):
                if c.get('type') == 'tool_result':
                    body = c.get('content'); body = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
                    tu = [t for t in tools if t[0] == c.get('tool_use_id')]
                    name, inp = (tu[0][1], tu[0][2]) if tu else ('?', {})
                    if name == 'Read':
                        f = rel(inp.get('file_path', ''))
                        for ln in re.findall(r'^\s*(\d+)\t', body, re.M): seen.setdefault(f, set()).add(int(ln))
                    elif name == 'Grep':
                        for f, ln in re.findall(r'([\w<>./\\-]+\.cs)[:-](\d+)[:-]', body):
                            seen.setdefault(rel(f), set()).add(int(ln))
    return res, ans, tools, seen

def rel(path):
    # 路徑可能是絕對路徑，或公開版 trace 裡被換成 <REPO>\... 的字串；一律取 repo/ 之後的部分
    q = path.replace('\\\\', '/').replace('\\', '/')
    return q.split('/repo/', 1)[1] if '/repo/' in q else q.lstrip('./')

def cites(ans):
    out = []
    def walk(k, v):
        if isinstance(v, dict):
            if 'file' in v and 'line' in v: out.append((k, v['file'], v['line'], v.get('answer')))
            for kk, vv in v.items():
                if kk not in ('file', 'line'): walk(k + '.' + kk if kk != 'evidence' else k, vv)
        elif isinstance(v, list):
            for x in v: walk(k, x)
    for k, v in ans.items(): walk(k, v)
    return out

for run in sys.argv[1:] or ['r1']:
    res, ans, tools, seen = load(run)
    print('==== %s  turns=%s  ms=%s  usd=%.4f  tools=%s' % (run, res.get('num_turns'), res.get('duration_ms'), res.get('total_cost_usd', 0), [t[1] for t in tools]))
    if '_raw' in ans: print('  無 JSON 回覆，原文：', ans['_raw'].replace('\n', ' | ')); continue
    ok = tot = 0
    for k, f, ln, a in cites(ans):
        tot += 1
        fp = os.path.join(REPO, f.replace('/', os.sep)); f_norm = f.replace('\\', '/')
        if not os.path.exists(fp): print('  [X] %s -> %s:%s  檔案不存在' % (k, f, ln)); continue
        lines = io.open(fp, encoding='utf-8').read().split('\n')
        if not (1 <= int(ln) <= len(lines)): print('  [X] %s -> %s:%s  行號超出範圍(%d)' % (k, f, ln, len(lines))); continue
        read = int(ln) in seen.get(f_norm, set())
        ok += 1 if read else 0
        print('  [%s] %s -> %s:%s  %s' % ('V' if read else '?', k, f, ln, 'trace 有讀到此行' if read else 'trace 未見此行'))
        for i in range(max(1, int(ln) - 1), min(len(lines), int(ln) + 1) + 1):
            print('       %s%4d| %s' % ('>' if i == int(ln) else ' ', i, lines[i - 1].rstrip()))
    print('  引用 %d 筆，檔案與行號皆存在且 trace 讀到過：%d 筆' % (tot, ok))
    for k in ('report_query_method', 'report_query_has_date_filter', 'report_count_checks_dates', 'payroll_method', 'shares_filter_code', 'fixing_payroll_fixes_report'):
        v = ans.get(k, {}); print('  %s = %s' % (k, v.get('answer') if isinstance(v, dict) else v))
    print('  symptom_a_root_cause =', (ans.get('symptom_a_root_cause') or {}).get('answer'))
    print('  unknowns =', ans.get('unknowns'))

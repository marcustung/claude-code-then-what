# -*- coding: utf-8 -*-
"""讀 Claude Code `--output-format stream-json` 的 trace.jsonl，印出：回合、毫秒、費用估值、模型、每次工具呼叫（名稱＋目標）、
工具回傳裡有沒有你指定的標記、最終回覆前幾百字。適用本 repo 所有 lab 的 trace。
用法：python tools/trace-summary.py <run 目錄或 trace.jsonl> [更多…] [--marker 文字] [--full]
例：  python tools/trace-summary.py days/day07/lab/day07 --marker RULE-CONTEXT-7-KITE-0911
      python tools/trace-summary.py days/day06/lab/noname*    （看它有沒有 Read intent.md）"""
import io, json, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith('--') and sys.argv[i - 1] != '--marker']
marker = sys.argv[sys.argv.index('--marker') + 1] if '--marker' in sys.argv else None
full = '--full' in sys.argv
paths = []
for a in args or ['.']:
    for p in glob.glob(a) or [a]:
        paths.append(p if p.endswith('.jsonl') else os.path.join(p, 'trace.jsonl'))
for tp in paths:
    if not os.path.exists(tp): print('%s：找不到 trace.jsonl' % tp); continue
    ev = []
    for l in io.open(tp, encoding='utf-8-sig'):
        l = l.strip()
        if not l: continue
        try: ev.append(json.loads(l))
        except Exception: pass
    res = [e for e in ev if e.get('type') == 'result']
    r = res[-1] if res else {}
    models = sorted({e['message'].get('model', '') for e in ev if e.get('type') == 'assistant'})
    calls = {}
    tools = []
    for e in ev:
        if e.get('type') == 'assistant':
            for c in e['message'].get('content', []):
                if c.get('type') == 'tool_use':
                    inp = c.get('input', {}); tgt = inp.get('file_path') or inp.get('pattern') or inp.get('command') or inp.get('skill') or ''
                    tools.append((c['name'], str(tgt)[-70:])); calls[c['id']] = c['name']
    hits = 0
    if marker:
        for e in ev:
            if e.get('type') == 'user':
                for c in e['message'].get('content', []):
                    if c.get('type') == 'tool_result':
                        body = c.get('content'); body = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
                        if marker in body: hits += 1
    print('==== %s' % os.path.dirname(tp) or tp)
    print('  回合 %s ｜ %s ms ｜ 費用估值 US$%.4f ｜ is_error=%s ｜ 模型 %s' % (r.get('num_turns'), r.get('duration_ms'), r.get('total_cost_usd', 0) or 0, r.get('is_error'), ','.join(models)))
    print('  工具呼叫 %d 次：%s' % (len(tools), '；'.join('%s %s' % t for t in tools) if tools else '（無）'))
    if marker: print('  標記「%s」出現在工具回傳：%d 次；出現在最終回覆：%s' % (marker, hits, marker in (r.get('result') or '')))
    txt = (r.get('result') or '').replace('\n', ' | ')
    print('  回覆：%s' % (txt if full else txt[:300] + ('…' if len(txt) > 300 else '')))

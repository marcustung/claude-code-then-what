"""Mechanical checks for ai-card-plain-criteria.md: plain words, length, and card queries found in the audit file.
Correctness of the judgement itself is read by a person against the criteria table."""
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parent
LATIN = re.compile(r'[A-Za-z]{2,}')


def shown(c):
    """The same fields publish_to_grafana.py puts on the dashboard."""
    x = c['card']
    if c['question'] == 'cause':
        key = next((k for k in x['checks'] if 'event' in k['query'] or '延後' in k['result']), x['checks'][0])
        return {'hypothesis': x['hypothesis'], 'verified': key['result'], 'first_step': x['first_step']}
    out = {f'missing[{i}].what': m['what'] for i, m in enumerate(x['missing'][:4])}
    out.update({'verified': x['checks'][0]['result'] if x['checks'] else '', 'first_step': x['first_step']})
    return out


def audited(query, audit):
    q = re.sub(r'\s+', '', query)
    for line in audit:
        a = json.loads(line)
        if a.get('exit_code') != 0: continue
        # The query expression is the argv item holding a selector: after --expr for logs, positional for metrics.
        for expr in (x for x in a.get('argv') or [] if '{' in x):
            if re.sub(r'\s+', '', expr) in q: return True
    return False


def main():
    cards = json.loads((ROOT/(sys.argv[1] if len(sys.argv) > 1 else 'ai-cards.json')).read_text(encoding='utf-8'))
    ok_all = True
    for run, c in cards['cards'].items():
        print(f"== {c['scenario']}（{c['question']}）")
        for k, v in shown(c).items():
            bad = LATIN.findall(v)
            ok = not bad and len(v) <= 80
            ok_all &= ok
            print(f"  {'通過' if ok else '不過'} {k}（{len(v)} 字）{' 英文：' + ','.join(bad) if bad else ''}")
        ap = ROOT/c['audit'].replace('\\', '/')
        if not ap.exists():  # public copy keeps only the summary (argv, exit code, count), not the returned records
            ap = ap.with_name('tool-audit.summary.jsonl')
        audit = ap.read_text(encoding='utf-8').splitlines()
        for ch in c['card']['checks']:
            print(f"  查詢{'在' if audited(ch['query'], audit) else '不在'}稽核檔：{ch['query'][:100]}")
    print('白話檢查：', '通過' if ok_all else '不過')

if __name__ == '__main__': main()

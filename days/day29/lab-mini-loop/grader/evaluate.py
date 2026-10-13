# -*- coding: utf-8 -*-
"""外層評分：用某份 rules.yml 評估某一天的指標，算 page 雜訊與漏報。沿用 Day 29 長期實驗的評分器。
告警事件＝某規則連續觸發的一段；與事故時間窗（前後 10 分鐘）重疊且指標相關才算有效，其餘為雜訊。
漏報＝事故期間沒有任何 page 級有效告警。成績單寫到 project/scores/（只有計數與漏報種類，沒有事故時間）。

  python grader/evaluate.py --day 1 [--rules path/to/rules.yml] [--out path/to/score.json]
"""
from pathlib import Path
import argparse, json, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
KIT = HERE.parent
SLACK = 10
RELEVANT = {'sink_down': {'notify_failed', 'queue_depth', 'receipts_gap'}, 'memory_leak': {'heap_mb'},
            'latency_regression': {'p95_latency_ms'}, 'silent_drop': {'receipts_gap'}}


def load_rules(path):
    """極簡 YAML 讀取（只支援 rules.yml 格式：清單、每項 key: value）。"""
    rules, cur = [], None
    for raw in Path(path).read_text(encoding='utf-8').splitlines():
        line = raw.split('#', 1)[0].rstrip()
        if not line.strip():
            continue
        s = line.strip()
        if s.startswith('- '):
            cur = {}; rules.append(cur); s = s[2:]
        if ':' in s and cur is not None:
            k, v = s.split(':', 1); v = v.strip().strip('"').strip("'")
            try:
                v = float(v) if '.' in v else int(v)
            except ValueError:
                pass
            cur[k.strip()] = v
    return rules


def episodes(series, op, th, for_m):
    out, run = [], 0
    for t, v in enumerate(series):
        hit = v > th if op == '>' else v < th
        run = run + 1 if hit else 0
        if run == for_m + 1 if for_m > 0 else (hit and (t == 0 or not (series[t - 1] > th if op == '>' else series[t - 1] < th))):
            out.append([t, t])
        if hit and out and out[-1][1] == t - 1 and run > for_m:
            out[-1][1] = t
    return out


def evaluate(day, rules_path):
    m = json.loads((KIT / 'project' / 'data' / f'day{day:02d}' / 'metrics.json').read_text(encoding='utf-8'))
    inc = json.loads((HERE / '.truth' / f'day{day:02d}.json').read_text(encoding='utf-8'))['incidents']
    rules = load_rules(rules_path)
    per_rule, page_hits = [], {i: False for i in range(len(inc))}
    page_noise = ticket_noise = 0
    for r in rules:
        if r.get('metric') not in m:
            per_rule.append({'name': r.get('name'), 'error': f"未知指標 {r.get('metric')}"}); continue
        eps = episodes(m[r['metric']], r.get('op', '>'), float(r['threshold']), int(r.get('for_minutes', 0)))
        valid = noise = 0
        for s, e in eps:
            hits = [i for i, x in enumerate(inc) if r['metric'] in RELEVANT[x['kind']] and not (e < x['start'] - SLACK or s > x['end'] + SLACK)]
            if hits:
                valid += 1
                if r.get('severity', 'page') == 'page':
                    for i in hits: page_hits[i] = True
            else:
                noise += 1
        if r.get('severity', 'page') == 'page': page_noise += noise
        else: ticket_noise += noise
        per_rule.append({'name': r.get('name'), 'severity': r.get('severity', 'page'), 'fired': len(eps), 'valid': valid, 'noise': noise})
    missed = [inc[i]['kind'] for i, ok in page_hits.items() if not ok]
    return {'day': day, 'rules': len(rules), 'page_noise': page_noise, 'ticket_noise': ticket_noise,
            'incidents': len(inc), 'missed': missed, 'per_rule': per_rule}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--day', type=int, required=True)
    ap.add_argument('--rules', default=str(KIT / 'project' / 'rules.yml')); ap.add_argument('--out')
    a = ap.parse_args()
    res = evaluate(a.day, a.rules)
    out = Path(a.out) if a.out else KIT / 'project' / 'scores' / f'day{a.day:02d}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: res[k] for k in ('day', 'page_noise', 'ticket_noise', 'incidents', 'missed')}, ensure_ascii=False))


if __name__ == '__main__':
    main()

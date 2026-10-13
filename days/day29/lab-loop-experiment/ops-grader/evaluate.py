# -*- coding: utf-8 -*-
"""實驗 2：用 ops/alerts/rules.yml 評估某一天的指標，算雜訊與漏報。放在受治理 repo 之外（2026-10-05 移出：原位置讓 agent 讀得到答案）。

規則格式（rules.yml，迴圈可提案修改）：
  - name: HighLatency
    metric: p95_latency_ms     # simulate.py 的指標名
    op: ">"                    # > 或 <
    threshold: 150
    for_minutes: 0             # 連續成立幾分鐘才觸發
    severity: page             # page（叫人）或 ticket（開單）

判定：
  告警事件＝某規則連續觸發的一段（一段只算一次）。
  有效告警＝事件與某事故時間窗（前後各 10 分鐘）重疊，且規則的指標與該事故相關（RELEVANT）；其餘為雜訊。
  漏報＝事故期間沒有任何 page 級有效告警。
  page 級雜訊會叫醒人，是要降的主要指標。

  python ops/sim/evaluate.py --day 1     # 先跑 simulate.py；輸出 ops/sim/.data/day01/eval.json
"""
from pathlib import Path
import argparse, json, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent
import os
RULES = Path(os.environ.get('OPS_RULES') or 'C:/<AUTHOR>/loop-lab/order-service/ops/alerts/rules.yml')
SLACK = 10
# 每種事故會反映在哪些指標上：只有這些指標的告警算「抓到」；不相關指標剛好同時響，仍算雜訊
RELEVANT = {'sink_down': {'notify_failed', 'queue_depth', 'receipts_gap'}, 'memory_leak': {'heap_mb'},
            'latency_regression': {'p95_latency_ms'}, 'silent_drop': {'receipts_gap'}}


def load_rules(path):
    """極簡 YAML 讀取（只支援本檔格式：清單、每項 key: value）。"""
    rules, cur = [], None
    for raw in path.read_text(encoding='utf-8').splitlines():
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


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--day', type=int, required=True); a = ap.parse_args()
    d = ROOT / '.data' / f'day{a.day:02d}'
    m = json.loads((d / 'metrics.json').read_text(encoding='utf-8'))
    inc = json.loads((d / 'truth.json').read_text(encoding='utf-8'))['incidents']
    rules = load_rules(RULES)
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
                    for i in hits:
                        page_hits[i] = True
            else:
                noise += 1
        if r.get('severity', 'page') == 'page':
            page_noise += noise
        else:
            ticket_noise += noise
        per_rule.append({'name': r.get('name'), 'severity': r.get('severity', 'page'), 'fired': len(eps), 'valid': valid, 'noise': noise})
    missed = [inc[i]['kind'] for i, ok in page_hits.items() if not ok]
    res = {'day': a.day, 'rules': len(rules), 'page_noise': page_noise, 'ticket_noise': ticket_noise,
           'incidents': len(inc), 'missed': missed, 'per_rule': per_rule}
    (d / 'eval.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: res[k] for k in ('day', 'page_noise', 'ticket_noise', 'incidents', 'missed')}, ensure_ascii=False))
    for r in per_rule:
        print('  ', r)


if __name__ == '__main__':
    main()

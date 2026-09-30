# -*- coding: utf-8 -*-
"""跨 run 的訊號稽核：同一個名字的數字，在不同 run 之間能不能比。

產出 audit-report.json：
  1. 每個 run 的「伺服器直方圖分位數」對「客戶端實測分位數」的落差
  2. 落在第一個桶裡的樣本比例（比例越高，histogram_quantile 越接近純內插）
  3. rules v1.0 與 v1.1 的裁決差異（誤報率）
用法：python slo/audit_signals.py
"""
import io, os, re, sys, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUNS = os.path.join(ROOT, 'evidence', 'runs')


def load_verdicts(p):
    out = {}
    if not os.path.exists(p):
        return out
    for line in io.open(p, encoding='utf-8'):
        parts = line.split()
        if len(parts) >= 2:
            out[parts[0]] = parts[1]
    return out


v10 = load_verdicts(os.path.join(HERE, 'verdicts-rules-v1.0.txt'))
v11 = load_verdicts(os.path.join(HERE, 'verdicts-rules-v1.1.txt'))

rows, comparable, incomparable = [], [], []
for d in sorted(glob.glob(os.path.join(RUNS, '*'))):
    rp = os.path.join(d, 'slo-report.json')
    if not os.path.exists(rp):
        continue
    r = json.load(io.open(rp, encoding='utf-8'))
    dv = r['dashboard_vs_client']
    rid = r['run_id']
    gap = None
    if dv['histogram_p95_ms'] and dv['client_p95_ms']:
        gap = round(dv['client_p95_ms'] / dv['histogram_p95_ms'], 1)
    reqs_n, hist_n = None, None
    try:
        import re as _re
        for line in io.open(os.path.join(d, 'metrics.txt'), encoding='utf-8-sig'):
            m = _re.match(r'oc_request_latency_ms_count\s+([0-9.]+)', line.strip())
            if m:
                hist_n = int(float(m.group(1)))
        cj = json.load(io.open(os.path.join(d, 'check.json'), encoding='utf-8-sig'))
        reqs_n = cj['summary'].get('requests')
    except Exception:
        pass
    row = {
        'run_id': rid, 'version': r.get('version'), 'mode': r.get('mode'),
        'requests_total': reqs_n, 'histogram_samples': hist_n,
        'requests_missing_from_histogram': (reqs_n - hist_n) if (reqs_n and hist_n) else None,
        'histogram_p95_ms': dv['histogram_p95_ms'], 'client_p95_ms': dv['client_p95_ms'],
        'understatement_x': gap,
        'pct_in_first_bucket': dv['pct_samples_in_first_bucket'],
        'verdict_v1_0': v10.get(rid), 'verdict_v1_1': v11.get(rid),
    }
    rows.append(row)
    (comparable if r.get('mode') == 'load' else incomparable).append(rid)

changed = [r for r in rows if r['verdict_v1_0'] != r['verdict_v1_1']]
raised_v10 = [r for r in rows if r['verdict_v1_0'] not in (None, 'ok')]
raised_v11 = [r for r in rows if r['verdict_v1_1'] not in (None, 'ok')]
gaps = [r['understatement_x'] for r in rows if r['understatement_x']]

report = {
    'generated': '2026-09-24',
    'service': 'order-cancel-lifecycle',
    'runs_audited': len(rows),
    'findings': [
        {
            'id': 'A-01',
            'claim': '伺服器直方圖的 p95 系統性低於客戶端實測的 p95。',
            'evidence': '%d 個有兩邊數字的 run，低估倍數 %.1f–%.1f 倍（中位數 %.1f 倍）。' % (
                len(gaps), min(gaps), max(gaps), sorted(gaps)[len(gaps) // 2]) if gaps else '無',
            'why': 'oc_request_latency_ms 在 handler 內部計時，不含連線建立、請求排隊與序列化；'
                   '客戶端量的是往返。Dashboard 畫的是前者，使用者感受到的是後者。',
        },
        {
            'id': 'A-02',
            'claim': '桶界沒有對齊實際分布時，histogram_quantile 的輸出是內插出來的，不是量到的。',
            'evidence': '第一個桶（le=5ms）在 %s 中吃掉 %s%% 的樣本。' % (
                ', '.join(r['run_id'] for r in rows if (r['pct_in_first_bucket'] or 0) >= 60)[:200] or '無',
                ', '.join(str(r['pct_in_first_bucket']) for r in rows if (r['pct_in_first_bucket'] or 0) >= 60)),
            'why': '樣本全部落在第一個桶時，p50 與 p95 都只是在 [0, 5] 之間按比例切，'
                   '和真實分布無關。加桶界才有意義，調告警門檻沒有。',
        },
        {
            'id': 'A-03',
            'claim': '門檻來自規格，不等於告警可信。',
            'evidence': 'rules v1.0 的五條 SLI 門檻四條出自 2026-09-21 就寫死的 scenario expected，'
                        '仍在 13 個 run 上發出 %d 次非 ok 裁決，改成 v1.1 後只剩 %d 次；'
                        '%d 次是誤報（%.0f%%）。' % (
                            len(raised_v10), len(raised_v11),
                            len(raised_v10) - len(raised_v11),
                            100.0 * (len(raised_v10) - len(raised_v11)) / len(raised_v10) if raised_v10 else 0),
            'why': '誤報的三個來源：訊號不存在被當成超標、負載門檻套到功能型 run、'
                   '對帳在佇列還沒排空時就做。三個都跟門檻數值無關，跟「什麼時候能比」有關。',
        },
        {
            'id': 'A-04',
            'claim': '不同 mode 的 run 不能放進同一張圖。',
            'evidence': 'load 模式 %d 個、功能模式 %d 個。功能模式只有約 20 次呼叫，'
                        'p95 由第一次請求的 JIT 成本主導。' % (len(comparable), len(incomparable)),
            'why': '同一個指標名字不保證同一個母體。分母不同的東西畫在一起，線會動，但動的是取樣方式。',
        },
        {
            'id': 'A-05',
            'claim': '請求失敗時，直方圖的分母會安靜地縮小——它只統計成功的那些。',
            'evidence': 'oom-retained-payloads-20260921-201516：實際 1415 筆請求（200:835、409:119、500:460、斷線 1），'
                        '而 oc_request_latency_ms_count 只有 954，剛好等於 835+119。'
                        '那 460 筆 OOM 期間最慘的請求，直方圖一筆都沒記。'
                        '對照健康的 load-baseline-20260921-202729：請求 2400、直方圖樣本 2400，完全相等。',
            'why': '計時與記錄發生在 handler 正常回傳的路徑上；請求噴 500 或連線斷掉就不會走到那一行。'
                   '結果是故障期間 dashboard 的 p95 是「成功者的 p95」，而使用者感受到的是全體的。'
                   '這不是低估幾倍的問題，是母體換掉了——兩個數字不能相除，也不該畫在同一張圖上。',
        },
        {
            'id': 'A-06',
            'claim': '桶界決定直方圖有沒有解析度，但不決定低估幾倍。',
            'evidence': '第一桶佔比 13.67% 的 slow-sync-notify 是唯一兩邊一致的 run（244.66 對 240.9）；'
                        '佔比 ≥ 60% 的六個 run 一律低估 3.6–9.1 倍，但倍數與佔比沒有單調關係'
                        '（67.29%→3.6 倍、91.33%→4.5 倍、87.92%→9.1 倍）。',
            'why': '佔比高代表樣本擠在同一個桶裡、內插沒有真實資料可依，所以一定失真；'
                   '失真多少則另外受該 run 的排隊與併發影響。可以用佔比當「能不能信」的判準，'
                   '不能用它推「差幾倍」。',
        },
    ],
    'comparable_group_load': comparable,
    'comparable_group_functional': incomparable,
    'verdict_changes_v1_0_to_v1_1': [
        {'run_id': r['run_id'], 'from': r['verdict_v1_0'], 'to': r['verdict_v1_1']} for r in changed],
    'per_run': rows,
}
json.dump(report, io.open(os.path.join(HERE, 'audit-report.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
lines = ['%-38s %-6s %-8s %-9s %-7s %-8s %s' % (
    'run', 'ver', 'hist_p95', 'client_p95', '低估x', '首桶%', 'v1.0→v1.1')]
for r in rows:
    lines.append('%-38s %-6s %-8s %-9s %-7s %-8s %s→%s' % (
        r['run_id'], r['version'], r['histogram_p95_ms'], r['client_p95_ms'],
        r['understatement_x'], r['pct_in_first_bucket'], r['verdict_v1_0'], r['verdict_v1_1']))
io.open(os.path.join(HERE, 'audit-summary.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
print('audit-report.json written; %d runs' % len(rows))

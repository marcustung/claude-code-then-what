#!/usr/bin/env python3
"""取消通知對帳：python reconcile.py <run 資料夾> [<run 資料夾> ...] --out <輸出資料夾>

分母  = requests.jsonl 中「HTTP 2xx 且 transitioned=true」的取消請求（NC-01/NC-04，唯一成功轉換）。
分子  = receipts.jsonl（接收端收據，獨立來源）中，run_id / request_id / order_id 都對得上分母的唯一 notification_id。
服務自己的 oc_notify_sent_total 不當證據，只拿來交叉檢查。
"""
import argparse
import html
import json
import os
import re
import sys

ORDER = {"investigate": 0, "waiting": 1, "unknown": 2, "matched": 3}
ACTION = {
    "investigate": "今天先查這一批",
    "waiting": "先不下結論，稍後重新擷取再對帳",
    "unknown": "先補資料，目前無法判斷",
    "matched": "不用處理",
}
STATE_LABEL = {
    "received": "已收到",
    "missing": "遺失（佇列已空仍無收據）",
    "dead_letter": "dead_letter（待人工處理）",
    "pending": "處理中",
    "unknown": "無法判斷",
    "duplicate": "重複收據",
    "unexpected": "不該有的收據",
}


def read_jsonl(path):
    """檔案不存在回 None（≠空檔）；壞行略過並計數。"""
    if not os.path.isfile(path):
        return None, 0
    rows, bad = [], 0
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                bad += 1
    return rows, bad


def read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_metrics(path):
    if not os.path.isfile(path):
        return None
    m = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            g = re.match(r"^(\w+)(\{[^}]*\})?\s+(-?[\d.]+)\s*$", line.strip())
            if g:
                m[g.group(1) + (g.group(2) or "")] = float(g.group(3))
    return m


def reconcile(run_dir):
    manifest = read_json(os.path.join(run_dir, "manifest.json")) or {}
    run_id = manifest.get("run_id") or os.path.basename(os.path.normpath(run_dir))
    requests, _ = read_jsonl(os.path.join(run_dir, "requests.jsonl"))
    logs, _ = read_jsonl(os.path.join(run_dir, "logs.jsonl"))
    receipts, bad_receipts = read_jsonl(os.path.join(run_dir, "receipts.jsonl"))
    metrics = read_metrics(os.path.join(run_dir, "metrics.txt"))
    notes = []

    def result(status, reason, expected=None, received=None, unmatched=None, events=None):
        return {"run_id": run_id, "expected": expected, "received": received,
                "unmatched": unmatched, "status": status, "reason": " ".join(reason) if isinstance(reason, list) else reason,
                "events": events or [], "notes": notes}

    # ---- 分母 ----
    transitions = {}  # request_id -> {order_id, seq}
    if requests is not None:
        for i, r in enumerate(requests):
            try:
                resp = json.loads(r.get("response") or "{}")
            except ValueError:
                resp = {}
            ok = isinstance(r.get("http_status"), int) and 200 <= r["http_status"] < 300
            if ok and resp.get("transitioned") is True and r.get("op", "cancel") == "cancel":
                transitions[r["request_id"]] = {"order_id": r.get("order_id"), "seq": r.get("seq", i)}
    elif logs is not None:
        notes.append("缺 requests.jsonl，分母改用服務 log（不是獨立來源）。")
        for i, x in enumerate(logs):
            if x.get("event") == "cancel" and x.get("transitioned") is True:
                transitions[x["request_id"]] = {"order_id": x.get("order_id"), "seq": i}
    else:
        return result("unknown", "requests.jsonl 與 logs.jsonl 都缺，無法定出應完成數。")

    # 交叉檢查：log 與 metrics 的轉換數要和 requests 一致，否則分母不可信
    if logs is not None and requests is not None:
        log_t = {x["request_id"] for x in logs if x.get("event") == "cancel" and x.get("transitioned") is True}
        if log_t != set(transitions):
            return result("unknown", f"requests（{len(transitions)} 筆轉換）與服務 log（{len(log_t)} 筆）對不上，分母不可信。")
    if metrics and "oc_transitions_total" in metrics and int(metrics["oc_transitions_total"]) != len(transitions):
        return result("unknown", f"requests 轉換 {len(transitions)} 筆與 metrics oc_transitions_total={int(metrics['oc_transitions_total'])} 不一致，分母不可信。")

    expected = len(transitions)
    if receipts is None:
        return result("unknown", "缺 receipts.jsonl（接收端收據），無法確認任何通知是否送達。", expected=expected)
    if bad_receipts:
        notes.append(f"receipts.jsonl 有 {bad_receipts} 行無法解析。")

    # ---- 分子：以 request_id 對回，並驗 run_id、order_id ----
    by_req, unexpected, foreign = {}, [], 0
    for r in receipts:
        if r.get("run_id") not in (None, run_id):
            foreign += 1
            continue
        t = transitions.get(r.get("request_id"))
        if t is None or t["order_id"] != r.get("order_id"):
            unexpected.append(r)
            continue
        by_req.setdefault(r["request_id"], {})[r["notification_id"]] = r
    if foreign:
        notes.append(f"{foreign} 筆收據屬於其他 run，已排除。")

    # ---- 服務 log 線索（只用於說明與 dead_letter，不當送達證據）----
    log_nid, dead = {}, set()
    for x in logs or []:
        ev = str(x.get("event", ""))
        if ev.startswith("notify") and x.get("request_id"):
            log_nid.setdefault(x["request_id"], x.get("notification_id"))
        if "dead_letter" in ev and x.get("request_id"):
            dead.add(x["request_id"])

    qd = None
    if metrics and "oc_notify_queue_depth" in metrics:
        qd = int(metrics["oc_notify_queue_depth"])
    elif manifest.get("last_queue_depth") is not None:
        qd = manifest["last_queue_depth"]
    dl_total = int(metrics.get("oc_notify_dead_letter_total", 0)) if metrics else 0

    events, problems = [], []
    received = 0
    for rid, t in sorted(transitions.items(), key=lambda kv: kv[1]["seq"]):
        got = by_req.get(rid, {})
        if got:
            received += 1
            nid = sorted(got)[0]
            state = "received"
            if len(got) > 1:
                state = "duplicate"
                problems.append(f"{rid} 收到 {len(got)} 則不同 notification_id（違反 NC-01）")
        else:
            nid = log_nid.get(rid)
            if rid in dead:
                state = "dead_letter"
                problems.append(f"{rid} 進 dead_letter")
            elif qd is None:
                state = "unknown"
            elif qd > 0:
                state = "pending"
            else:
                state = "missing"
        events.append({"order_id": t["order_id"], "request_id": rid, "notification_id": nid, "state": state})
    for r in unexpected:
        events.append({"order_id": r.get("order_id"), "request_id": r.get("request_id"),
                       "notification_id": r.get("notification_id"), "state": "unexpected"})
        problems.append(f"收據 {r.get('notification_id')} 對不到任何成功轉換（NC-02/03 或欄位不符）")

    unmatched = expected - received
    enq = int(metrics["oc_notify_enqueued_total"]) if metrics and "oc_notify_enqueued_total" in metrics else None
    if enq is not None and enq < expected:
        problems.append(f"服務只入佇列 {enq} 則，少於轉換數 {expected}（通知在入佇列前就丟了）")
    if expected == 0 and not problems:
        notes.append("本輪沒有任何成功轉換，無通知可對。")

    sent = int(metrics["oc_notify_sent_total"]) if metrics and "oc_notify_sent_total" in metrics else None
    if sent is not None and sent != received:
        notes.append(f"服務自報 sent={sent}，接收端收據={received}；以收據為準。")

    kw = dict(expected=expected, received=received, unmatched=unmatched, events=events)
    if problems or dl_total:
        if dl_total and not problems:
            problems.append(f"metrics 顯示 dead_letter={dl_total}")
        return result("investigate", "；".join(problems[:5]) + "。", **kw)
    if unmatched == 0:
        return result("matched", f"{expected} 筆成功轉換都有接收端收據。", **kw)
    if qd is None:
        return result("unknown", f"{unmatched} 筆沒收據，但缺佇列深度，分不出還在送還是已遺失。", **kw)
    if qd > 0:
        return result("waiting", f"{unmatched} 筆尚無收據，佇列深度 {qd}>0 且無 dead_letter／失敗紀錄，仍在處理，尚不能下結論。", **kw)
    return result("investigate", f"佇列已空（depth=0）、無 dead_letter，仍有 {unmatched}/{expected} 筆沒有接收端收據；通知被靜默丟失（NC-05）。", **kw)


def render_html(views):
    views = sorted(views, key=lambda v: ORDER[v["status"]])
    h = ["<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><title>取消通知對帳</title>",
         "<style>body{font-family:sans-serif;max-width:960px;margin:2em auto;padding:0 1em}"
         ".card{border:1px solid #ccc;border-left:10px solid #888;border-radius:6px;padding:.8em 1em;margin:1em 0}"
         ".investigate{border-left-color:#c62828}.waiting{border-left-color:#f9a825}"
         ".unknown{border-left-color:#607d8b}.matched{border-left-color:#2e7d32}"
         "h2{margin:0 0 .3em;font-size:1.1em}.act{font-weight:bold;font-size:1.2em}"
         "table{border-collapse:collapse;width:100%;font-size:.85em}td,th{border:1px solid #ddd;padding:3px 6px;text-align:left}"
         ".s-missing,.s-dead_letter,.s-duplicate,.s-unexpected{background:#ffebee}.s-pending{background:#fff8e1}.s-unknown{background:#eceff1}"
         "</style><h1>取消通知對帳</h1><p>由上到下就是處理順序。送達以接收端收據為準。</p>"]
    for v in views:
        s = v["status"]
        n = lambda x: "—" if x is None else x
        h.append(f"<div class='card {s}'><h2>{html.escape(v['run_id'])}　[{s}]</h2>"
                 f"<div class='act'>{ACTION[s]}</div>"
                 f"<p>應完成 {n(v['expected'])}　已確認 {n(v['received'])}　未對上 {n(v['unmatched'])}</p>"
                 f"<p>{html.escape(v['reason'])}</p>")
        for note in v.get("notes", []):
            h.append(f"<p><small>備註：{html.escape(note)}</small></p>")
        bad = [e for e in v["events"] if e["state"] != "received"]
        if bad:
            h.append(f"<details><summary>未對上／異常事件 {len(bad)} 筆</summary><table>"
                     "<tr><th>order_id</th><th>request_id</th><th>notification_id</th><th>state</th></tr>")
            for e in bad:
                h.append(f"<tr class='s-{e['state']}'><td>{html.escape(str(e['order_id']))}</td>"
                         f"<td>{html.escape(str(e['request_id']))}</td>"
                         f"<td>{html.escape(str(e['notification_id'] or '—'))}</td>"
                         f"<td>{e['state']}：{STATE_LABEL.get(e['state'], '')}</td></tr>")
            h.append("</table></details>")
        h.append("</div>")
    return "\n".join(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    views = [reconcile(d) for d in a.runs]
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "view.json"), "w", encoding="utf-8") as f:
        json.dump([{k: v for k, v in x.items() if k != "notes"} for x in views], f, ensure_ascii=False, indent=2)
    with open(os.path.join(a.out, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(views))
    for v in views:
        print(f"{v['status']:11} {v['run_id']}  expected={v['expected']} received={v['received']} unmatched={v['unmatched']}")


if __name__ == "__main__":
    sys.exit(main())

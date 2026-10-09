"""Offline, read-only reconciliation of saved tutorial runs. No model or live Grafana."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import hashlib, html, json, re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent/'order-cancel-lifecycle/evidence/runs'
RUNS = ['missing-notification-20260921-193704', 'missing-notification-20260921-193835', 'slow-sync-control-20260923-191636']
def read_json(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def jsonl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8-sig').splitlines() if s.strip()] if path.exists() else None
def key(row): return tuple(row.get(x) for x in ('run_id','request_id','order_id'))
def reconcile(logs, receipts, manifest, depth):
    if logs is None:
        return {'status':'unknown','reason':'missing_sender_records','expected':None,'received':None,'unmatched':None,'events':[]}
    expected = {key(r) for r in logs if r.get('event')=='cancel' and r.get('transitioned') is True}
    ids=defaultdict(set)
    for r in logs:
        if r.get('notification_id'): ids[key(r)].add(r['notification_id'])
    if any(None in k or len(ids[k])>1 for k in expected):
        return {'status':'unknown','reason':'event_identity_incomplete','expected':len(expected),'received':None,'unmatched':None,'events':[]}
    if receipts is None:
        return {'status':'unknown','reason':'missing_receiver_records','expected':len(expected),'received':None,'unmatched':None,'events':[]}
    matched=Counter(); unexpected=[]
    for r in receipts:
        k=key(r)
        if k in expected and r.get('notification_id') in ids[k] and r.get('kind')=='order_cancelled': matched[k]+=1
        else: unexpected.append(r)
    # This is the saved harness's end condition, not a universal delivery deadline.
    ended = bool(manifest.get('wait',{}).get('terminal')) and depth==0
    missing=expected-matched.keys()
    duplicates=sum(max(0,v-1) for v in matched.values())
    missing_identity=sum(not ids[k] for k in expected)
    status = 'unknown' if missing_identity else 'investigate' if duplicates or unexpected or (ended and missing) else 'waiting' if missing else 'matched'
    return {'status':status,'reason':'missing_notification_identity' if missing_identity else 'identity_reconciliation','expected':len(expected),'received':len(matched),
            'unmatched':len(missing),'duplicates':duplicates,'unexpected_receipts':len(unexpected),
            'missing_notification_identity':missing_identity,'observation_closed':ended,'events':[{'run_id':k[0],'request_id':k[1],'order_id':k[2],
            'notification_id':next(iter(ids[k]),None),'state':'matched' if k in matched else 'unmatched'} for k in sorted(expected)]}
def save(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    out=ROOT/'runs'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True)
    rows=[];sources={}
    for name in RUNS:
        folder=SOURCE/name; m=read_json(folder/'manifest.json'); logs=jsonl(folder/'logs.jsonl'); receipts=jsonl(folder/'receipts.jsonl')
        metric_path=folder/'metrics.txt'; metrics=metric_path.read_text(encoding='utf-8-sig')
        def metric(label):
            v=re.search(r'^'+label+r'\s+([\d.]+)',metrics,re.M);return float(v[1]) if v else None
        depth=metric('oc_notify_queue_depth')
        if depth is None: depth=metric('oc_notification_queue_depth')
        if depth is None: depth=metric('oc_queue_depth')
        if depth is None: depth=m.get('last_queue_depth')
        row={'run_id':name,'version':m['version'],'started':m['started'],'ended':m['ended'],'queue_snapshot':depth,
             'source':'saved tutorial files; not live Grafana','reconciliation':reconcile(logs,receipts,m,depth)}
        rows.append(row)
        for filename in ['manifest.json','logs.jsonl','receipts.jsonl','requests.jsonl','metrics.txt']:
            p=folder/filename
            sources[str(p.relative_to(ROOT.parent))]=hashlib.sha256(p.read_bytes()).hexdigest()
    checks=[]
    def check(n,b):checks.append({'name':n,'passed':bool(b)})
    check('original_missing_9_to_3',rows[0]['reconciliation']['expected']==9 and rows[0]['reconciliation']['received']==3 and rows[0]['reconciliation']['status']=='investigate')
    check('fixed_same_scenario_9_to_9',rows[1]['reconciliation']['expected']==9 and rows[1]['reconciliation']['received']==9 and rows[1]['reconciliation']['status']=='matched')
    check('incomplete_identity_is_not_loss',rows[2]['reconciliation']['expected']==259 and rows[2]['reconciliation']['received']==12 and rows[2]['reconciliation']['status']=='unknown')
    f=SOURCE/RUNS[1]; ls=jsonl(f/'logs.jsonl'); rs=jsonl(f/'receipts.jsonl'); mf=read_json(f/'manifest.json')
    check('missing_file_is_unknown',reconcile(ls,None,mf,0)['received'] is None)
    wrong=[{**r,'notification_id':'wrong-'+r['notification_id']} for r in rs]
    check('equal_counts_wrong_ids_fail',reconcile(ls,wrong,mf,0)['received']==0 and reconcile(ls,wrong,mf,0)['status']=='investigate')
    check('duplicate_receipt_is_not_extra_completion',reconcile(ls,rs+[rs[0]],mf,0)['duplicates']==1 and reconcile(ls,rs+[rs[0]],mf,0)['received']==9)
    check('missing_sender_identity_is_unknown',reconcile([r for r in ls if not r.get('notification_id')],rs,mf,0)['status']=='unknown')
    check('unfinished_window_is_not_loss',reconcile(ls,rs[:3],{**mf,'wait':{}},6)['status']=='waiting')
    save(out/'input-sha256.json',sources);save(out/'source-sha256.json',{'build.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()});save(out/'view.json',rows);save(out/'checks.json',{'model_called':False,'checks':checks,'passed':all(c['passed'] for c in checks)})
    labels={'investigate':'查明未對上的事件','matched':'本次通知逐筆對上','waiting':'等待並補查處理進度','unknown':'先補資料，保留未知'}
    body=''
    for row in rows:
        r=row['reconciliation']; events='\n'.join(f"{x['order_id']} / {x['request_id']} / {x['state']}" for x in r['events'])
        body+=f"<tr><td><b>{html.escape(row['run_id'])}</b><br>版本 {row['version']}<br><small>{row['started']}<br>{row['ended']}</small></td><td>{r['expected']}</td><td>{r['received']}</td><td>{r['unmatched']}</td><td class='{r['status']}'>{labels[r['status']]}<br><small>結束條件：{'已記錄' if r.get('observation_closed') else '未確認'}</small><details><summary>查看事件</summary><pre>{html.escape(events)}</pre></details></td></tr>"
    page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Day 25｜哪些通知還沒完成？</title><style>body{margin:40px auto;max-width:1200px;padding:0 24px;background:#faf6ee;color:#1f1f1f;font:17px/1.7 system-ui,"Microsoft JhengHei"}h1{color:#2b4c7e}mark{background:#f6e27a}table{border-collapse:collapse;width:100%;background:#fffdf8}th,td{text-align:left;vertical-align:top;padding:18px;border-bottom:1px solid #ccc}th{background:#2b4c7e;color:white}small{font-size:12px;color:#596478}.investigate{background:#f9d8b8}.waiting{background:#fff0b3}.matched{background:#dbeae7}pre{max-height:260px;overflow:auto;font-size:12px}details{margin-top:12px}</style><h1>哪些通知還沒完成？</h1><p><mark>先看哪筆工作沒有對上，再決定查什麼。</mark></p><p>同一份歷史紀錄，按 run_id、request_id、order_id、notification_id 逐筆比對。這是離線教學視圖，不是即時 Grafana。</p><table><thead><tr><th>情境與觀察窗</th><th>真正取消</th><th>收到對應通知</th><th>尚未對上</th><th>下一步</th></tr></thead><tbody>'''+body+'''</tbody></table><p>「尚未對上」不等於漏送。未確認觀察結束時先補查；檔案缺失保留 unknown，不能補零。</p><p>通知完成只代表這項教學契約，不表示退款、完整商業流程或 Production SLA 已完成。</p></html>'''
    (out/'index.html').write_text(page,encoding='utf-8')
    (ROOT/'latest-run.txt').write_text(str(out.relative_to(ROOT)),encoding='utf-8')
    print(json.dumps({'output':str(out),'passed':all(c['passed'] for c in checks),'checks':len(checks),'rows':[{'run_id':r['run_id'],**{k:v for k,v in r['reconciliation'].items() if k!='events'}} for r in rows]},ensure_ascii=False))
    return 0 if all(c['passed'] for c in checks) else 1
if __name__=='__main__':raise SystemExit(main())

# -*- coding: utf-8 -*-
"""對帳 checker：讀一個 run 目錄，用三個獨立來源核對「取消功能完成」的三個層次（通知契約 NC-04）：
  1 客戶端 requests.jsonl（API 接受了什麼）
  2 服務 logs.jsonl／final-states.json／metrics.txt（狀態改了什麼、服務自己以為送了幾則）
  3 接收端 receipts.jsonl（實際送達幾則）
等式：唯一成功轉換數 == enqueued == receipts（去重 notification_id）。任何一邊不等、缺檔、格式錯、timeout → FAIL，exit 1。
用法：python tools/check.py evidence/runs/<run_id>   → 印報告、寫 check.json"""
import io, json, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

def jsonl(p):
    rows, bad = [], 0
    if not os.path.exists(p): return None, 0
    for line in io.open(p, encoding='utf-8-sig'):
        line = line.strip()
        if not line: continue
        try: rows.append(json.loads(line))
        except Exception: bad += 1
    return rows, bad

def main(run_dir):
    findings, ok = [], True
    def fail(msg): nonlocal ok; ok = False; findings.append('FAIL ' + msg)
    def note(msg): findings.append('ok   ' + msg)
    man_p = os.path.join(run_dir, 'manifest.json')
    if not os.path.exists(man_p): fail('manifest.json 缺'); return finish(run_dir, ok, findings, {})
    man = json.load(io.open(man_p, encoding='utf-8-sig'))
    exp = man.get('expected') or {}
    if man.get('status') != 'terminal': fail('run 未達終態：status=%s（timeout 不算成功）' % man.get('status'))
    reqs, bad1 = jsonl(os.path.join(run_dir, 'requests.jsonl'))
    logs, bad2 = jsonl(os.path.join(run_dir, 'logs.jsonl'))
    rcts, bad3 = jsonl(os.path.join(run_dir, 'receipts.jsonl'))
    if reqs is None: fail('requests.jsonl 缺'); reqs = []
    if logs is None: fail('logs.jsonl 缺'); logs = []
    if rcts is None: fail('receipts.jsonl 缺（接收端沒有任何收據，不能用服務計數器代替）'); rcts = []
    if bad1 or bad2 or bad3: fail('JSONL 格式錯誤行數 requests=%d logs=%d receipts=%d' % (bad1, bad2, bad3))
    metrics = {}
    mp = os.path.join(run_dir, 'metrics.txt')
    if os.path.exists(mp):
        for line in io.open(mp, encoding='utf-8-sig'):
            m = re.match(r'^(\S+) (\d+)$', line.strip())
            if m: metrics[m.group(1)] = int(m.group(2))
    else: fail('metrics.txt 缺')
    # 1 客戶端：HTTP 狀態分佈
    by_status = {}
    for r in reqs: by_status[r.get('http_status')] = by_status.get(r.get('http_status'), 0) + 1
    # 2 服務：cancel 事件
    cancels = [l for l in logs if l.get('event') == 'cancel']
    outcomes = {}
    for l in cancels: outcomes[l.get('result')] = outcomes.get(l.get('result'), 0) + 1
    transitions = sum(1 for l in cancels if l.get('transitioned') is True)
    uniq_transitioned_orders = {l.get('order_id') for l in cancels if l.get('transitioned') is True}
    if transitions != len(uniq_transitioned_orders): fail('同一訂單被記錄轉換多次：transitions=%d 唯一訂單=%d（冪等被破壞）' % (transitions, len(uniq_transitioned_orders)))
    refund_true = sum(1 for l in cancels if l.get('transitioned') is True and l.get('refund_requested') is True)
    enqueued = metrics.get('oc_notify_enqueued_total', 0)
    sent_claimed = metrics.get('oc_notify_sent_total', 0)
    dead = metrics.get('oc_notify_dead_letter_total', 0)
    deferred_all = [l for l in logs if l.get('event') == 'notify_deferred']
    deferred = sum(1 for l in deferred_all if not l.get('requeued'))          # v1.0.0：延後且不重送（丟失）
    requeued = sum(1 for l in deferred_all if l.get('requeued'))              # v1.1.0：延後但重排（不丟）
    # 3 接收端：收據去重
    rids = [r.get('notification_id') for r in rcts]
    uniq_receipts = len(set(rids)); dup_receipts = len(rids) - uniq_receipts
    # 對帳
    for name, got, want in [('transitions', transitions, exp.get('transitions')), ('idempotent', outcomes.get('idempotent', 0), exp.get('idempotent')),
                            ('rejected_shipped', outcomes.get('rejected_shipped', 0), exp.get('rejected_shipped')), ('not_found', outcomes.get('not_found', 0), exp.get('not_found')),
                            ('unauthorized', outcomes.get('unauthorized', 0), exp.get('unauthorized')), ('refund_requested_true', refund_true, exp.get('refund_requested_true'))]:
        if want is None: continue
        (note if got == want else fail)('%s：觀察 %d／期待 %d' % (name, got, want))
    if enqueued != transitions: fail('enqueued(%d) != transitions(%d)：有成功轉換沒進佇列，或多進了' % (enqueued, transitions))
    else: note('enqueued == transitions == %d' % transitions)
    if uniq_receipts != transitions: fail('接收端收據(%d 去重) != 成功轉換(%d)：通知沒送達 %d 則' % (uniq_receipts, transitions, transitions - uniq_receipts))
    else: note('接收端收據 == 成功轉換 == %d（送達以收據為準）' % uniq_receipts)
    if sent_claimed != uniq_receipts: fail('服務自報 sent_total(%d) != 接收端收據(%d)：計數器說謊 %d 則' % (sent_claimed, uniq_receipts, sent_claimed - uniq_receipts))
    else: note('服務 sent_total == 收據 == %d' % sent_claimed)
    if dup_receipts: fail('接收端重複收據 %d 則（同一 notification_id 送兩次）' % dup_receipts)
    if dead: fail('dead_letter %d 則：待人工處理，不算成功' % dead)
    if deferred: findings.append('warn notify_deferred 且未重送 %d 則（v1.0.0 行為：丟失）' % deferred)
    if requeued: findings.append('info notify_deferred 且重排 %d 次（壓力下延後，未丟失）' % requeued)
    # 對回請求：每則收據的 request_id 都要在 requests.jsonl 裡
    req_ids = {r.get('request_id') for r in reqs}
    orphan = [r for r in rcts if r.get('request_id') not in req_ids]
    if orphan: fail('%d 則收據對不回任何客戶端 request_id' % len(orphan))
    else: note('每則收據都對得回客戶端 request（%d）' % len(rcts))
    summary = {'transitions': transitions, 'unique_orders': len(uniq_transitioned_orders), 'outcomes': outcomes, 'http_status': by_status, 'enqueued': enqueued,
               'sent_claimed': sent_claimed, 'receipts_unique': uniq_receipts, 'receipts_dup': dup_receipts, 'dead_letter': dead, 'deferred_lost': deferred, 'deferred_requeued': requeued, 'refund_requested_true': refund_true,
               'expected': exp, 'status': man.get('status'), 'version': man.get('version')}
    return finish(run_dir, ok, findings, summary)

def finish(run_dir, ok, findings, summary):
    out = {'result': 'PASS' if ok else 'FAIL', 'findings': findings, 'summary': summary}
    io.open(os.path.join(run_dir, 'check.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(out, ensure_ascii=False, indent=1))
    print('== check %s  %s' % (os.path.basename(run_dir), out['result']))
    for f in findings: print('  ' + f)
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'evidence/runs/default'))

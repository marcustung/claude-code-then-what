# -*- coding: utf-8 -*-
"""驗收測試：通知送不出時的重送與補償（SPEC.md AT-01～AT-12）。
迴圈不得修改本檔與 SPEC.md（雜湊檢查）。

  python acceptance/run_acceptance.py            # 全部
  python acceptance/run_acceptance.py AT-03      # 指定
輸出：acceptance/.run/result.json；全部通過 exit 0，否則 exit 1。
"""
from pathlib import Path
import json, os, shutil, subprocess, sys, time, urllib.request, urllib.error, uuid

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / 'acceptance' / '.run'
# 埠號可由環境變數覆寫，讓長跑組與迴圈組同時跑驗收不互撞（2026-10-05，開跑前；預設值不變）
API_PORT = int(os.environ.get('ACCEPT_API_PORT', 5280))
SINK_PORT = int(os.environ.get('ACCEPT_SINK_PORT', 5281))
API = f'http://127.0.0.1:{API_PORT}'
INTERVAL_MS, MAX_ROUNDS = 1000, 3
ACTOR = {'X-Actor': 'acceptance'}


def http(method, path, body=None, headers=None, base=API, timeout=10):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Content-Type': 'application/json', **(headers or {})}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode() or 'null'
            return r.status, (json.loads(txt) if txt.strip()[:1] in '[{"0123456789tfn' else txt)
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, txt


def wait_until(fn, secs, step=0.25):
    end = time.time() + secs
    while time.time() < end:
        try:
            v = fn()
            if v:
                return v
        except Exception:
            pass
        time.sleep(step)
    return None


class Env:
    """一組隔離的服務：API 與接收端，接收端可以單獨關掉／打開。"""
    def __init__(self, name):
        self.dir = RUN / name
        shutil.rmtree(self.dir, ignore_errors=True); self.dir.mkdir(parents=True)
        self.api = self.sink = None

    def _env(self, port):
        return {**os.environ, 'OC_RUN_DIR': str(self.dir), 'ASPNETCORE_URLS': f'http://127.0.0.1:{port}',
                'OC_SINK_URL': f'http://127.0.0.1:{SINK_PORT}/notify',
                'OC_REDELIVERY_INTERVAL_MS': str(INTERVAL_MS), 'OC_REDELIVERY_MAX_ROUNDS': str(MAX_ROUNDS)}

    def start_sink(self):
        self.sink = subprocess.Popen(['dotnet', str(ROOT / 'src/FakeSink/bin/Debug/net9.0/FakeSink.dll')], env=self._env(SINK_PORT),
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert wait_until(lambda: http('GET', '/health', base=f'http://127.0.0.1:{SINK_PORT}')[0] == 200, 30), 'sink 沒起來'

    def stop_sink(self):
        if self.sink:
            self.sink.kill(); self.sink.wait(); self.sink = None

    def start_api(self):
        self.api = subprocess.Popen(['dotnet', str(ROOT / 'src/Api/bin/Debug/net9.0/Api.dll')], env=self._env(API_PORT),
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert wait_until(lambda: http('GET', '/health')[0] == 200, 30), 'api 沒起來'

    def stop_api(self):
        if self.api:
            self.api.kill(); self.api.wait(); self.api = None

    def close(self):
        self.stop_api(); self.stop_sink()

    def cancel(self, paid=False):
        oid = 'o-' + uuid.uuid4().hex[:8]
        http('POST', '/orders', {'id': oid, 'shipped': False, 'paid': paid})
        s, b = http('POST', f'/orders/{oid}/cancel', {}, ACTOR)
        assert s == 200, f'取消失敗 {s} {b}'
        return oid

    def receipts(self):
        p = self.dir / 'receipts.jsonl'
        return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()] if p.exists() else []

    def metric(self, name):
        s, txt = http('GET', '/metrics')
        for line in str(txt).splitlines():
            if line.startswith(name + ' ') or line.startswith(name + '{'):
                return float(line.rsplit(' ', 1)[1])
        return None

    def dead_letters(self):
        s, b = http('GET', '/admin/dead-letters', headers=ACTOR)
        assert s == 200, f'/admin/dead-letters 回 {s}'
        return b if isinstance(b, list) else (b or {}).get('items', [])

    def dl_for(self, oid):
        return next((d for d in self.dead_letters() if d.get('order_id') == oid), None)


# ── 各條件 ─────────────────────────────────────────────
def at01():
    e = Env('at01')
    try:
        e.start_api(); oid = e.cancel()
        d = wait_until(lambda: e.dl_for(oid), 8)
        assert d, '死信清單沒有這筆通知'
        for k in ('notification_id', 'order_id', 'attempts', 'last_error', 'status'):
            assert k in d, f'缺欄位 {k}'
        assert d['attempts'] >= 4, f"attempts={d['attempts']}"
    finally:
        e.close()


def at02():
    e = Env('at02')
    try:
        e.start_api()
        assert http('GET', '/admin/dead-letters')[0] == 401, '沒帶 X-Actor 也能存取'
        assert http('GET', '/admin/reconcile')[0] == 401, 'reconcile 沒帶 X-Actor 也能存取'
    finally:
        e.close()


def at03_04():
    e = Env('at03')
    try:
        e.start_api(); oid = e.cancel()
        d = wait_until(lambda: e.dl_for(oid), 8); assert d, '沒進死信'
        nid = d['notification_id']
        e.start_sink()
        s, b = http('POST', f'/admin/dead-letters/{nid}/replay', {}, ACTOR)
        assert s == 200, f'replay 回 {s} {b}'
        assert wait_until(lambda: any(r['notification_id'] == nid for r in e.receipts()), 5), '接收端沒收到'
        assert not any(x.get('notification_id') == nid and x.get('status') not in ('delivered',) for x in e.dead_letters()), '送達後仍在死信清單'
        r1 = 'pass'
        s2, _ = http('POST', f'/admin/dead-letters/{nid}/replay', {}, ACTOR)
        time.sleep(1)
        n = sum(1 for r in e.receipts() if r['notification_id'] == nid)
        r2 = s2 in (404, 409) and n == 1
        return {'AT-03': r1, 'AT-04': 'pass' if r2 else f'fail: 再 replay 回 {s2}，收據 {n} 筆'}
    finally:
        e.close()


def at05_07_08():
    e = Env('at05')
    out = {}
    try:
        e.start_api(); oid = e.cancel()
        d = wait_until(lambda: e.dl_for(oid), 8); assert d, '沒進死信'
        nid = d['notification_id']
        sent = e.metric('oc_notify_sent_total')
        out['AT-08'] = 'pass' if (sent or 0) == 0 else f'fail: 接收端掛掉時 sent_total={sent}'
        depth = e.metric('oc_notify_dead_letter_depth')
        depth_ok = depth is not None and depth >= 1
        e.start_sink()
        ok = wait_until(lambda: any(r['notification_id'] == nid for r in e.receipts()), INTERVAL_MS / 1000 * MAX_ROUNDS + 4)
        out['AT-05'] = 'pass' if ok else 'fail: 接收端恢復後沒有自動送達'
        time.sleep(1)
        depth2 = e.metric('oc_notify_dead_letter_depth')
        out['AT-07'] = 'pass' if depth_ok and depth2 == 0 else f'fail: depth 前 {depth} 後 {depth2}'
    finally:
        e.close()
    return out


def at06_09_10():
    e = Env('at06')
    out = {}
    try:
        e.start_api(); oid = e.cancel(paid=True)
        d = wait_until(lambda: (lambda x: x if x and x.get('status') == 'abandoned' else None)(e.dl_for(oid)),
                       INTERVAL_MS / 1000 * (MAX_ROUNDS + 2) + 6)
        ab = e.metric('oc_notify_abandoned_total')
        logp = e.dir / 'logs.jsonl'
        logged = logp.exists() and any(json.loads(l).get('event') == 'notify_abandoned' for l in logp.read_text(encoding='utf-8').splitlines() if l.strip())
        out['AT-06'] = 'pass' if d and (ab or 0) >= 1 and logged else f'fail: status={(e.dl_for(oid) or {}).get("status")} abandoned_total={ab} log={logged}'
        s, rec = http('GET', '/admin/reconcile', headers=ACTOR)
        good = s == 200 and all(k in rec for k in ('transitions', 'delivered', 'pending', 'abandoned')) and \
            rec['transitions'] == rec['delivered'] + rec['pending'] + rec['abandoned']
        out['AT-09'] = 'pass' if good else f'fail: {s} {rec}'
        s, o = http('GET', f'/orders/{oid}')
        flag = isinstance(o, dict) and (o.get('needs_manual_followup') is True or (o.get('order') or {}).get('needs_manual_followup') is True)
        out['AT-10'] = 'pass' if flag else f'fail: {o}'
    finally:
        e.close()
    return out


def at11():
    e = Env('at11')
    try:
        e.start_api(); oid = e.cancel()
        assert wait_until(lambda: e.dl_for(oid), 8), '沒進死信'
        e.stop_api(); e.start_api()
        assert e.dl_for(oid), '重啟後死信不見'
    finally:
        e.close()


def at12():
    r = subprocess.run(['dotnet', 'run', '--project', str(ROOT / 'tests/DomainTests')], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=300)
    assert r.returncode == 0, 'DomainTests 失敗'
    e = Env('at12')
    try:
        e.start_sink(); e.start_api(); oid = e.cancel()
        assert wait_until(lambda: any(x['order_id'] == oid for x in e.receipts()), 6), '接收端正常時通知沒送達'
    finally:
        e.close()


SINGLE = {'AT-01': at01, 'AT-02': at02, 'AT-11': at11, 'AT-12': at12}
GROUPS = [(('AT-03', 'AT-04'), at03_04), (('AT-05', 'AT-07', 'AT-08'), at05_07_08), (('AT-06', 'AT-09', 'AT-10'), at06_09_10)]


def main():
    want = set(sys.argv[1:])
    b = subprocess.run(['dotnet', 'build', str(ROOT / 'src/Api'), '-v', 'q', '-nologo'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    b2 = subprocess.run(['dotnet', 'build', str(ROOT / 'src/FakeSink'), '-v', 'q', '-nologo'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    res = {}
    if b.returncode or b2.returncode:
        res = {f'AT-{i:02d}': 'fail: build 失敗' for i in range(1, 13)}
    else:
        for at, fn in SINGLE.items():
            if want and at not in want:
                continue
            try:
                fn(); res[at] = 'pass'
            except Exception as ex:
                res[at] = f'fail: {ex}'
        for ats, fn in GROUPS:
            if want and not (want & set(ats)):
                continue
            try:
                out = fn() or {}
                for at in ats:
                    res[at] = out.get(at, 'fail: 未判定')
            except Exception as ex:
                for at in ats:
                    res[at] = f'fail: {ex}'
    res = dict(sorted(res.items()))
    passed = sum(v == 'pass' for v in res.values())
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / 'result.json').write_text(json.dumps({'passed': passed, 'total': len(res), 'results': res}, ensure_ascii=False, indent=2), encoding='utf-8')
    for k, v in res.items():
        print(k, v)
    print(f'{passed}/{len(res)} pass')
    sys.exit(0 if passed == len(res) else 1)


if __name__ == '__main__':
    main()

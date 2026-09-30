"""補測回復演練沒有涵蓋的組合：新版程式（r2）＋健康接收端。

起因（2026-09-29）：acceptance-rollback-01 的回復動作同時換回程式與恢復接收端，
變因沒有隔離。唯讀判讀指出另一半——新版程式在健康下游的表現這輪完全沒有驗過，
所以那次演練不能當成新版的上線依據。

順便補上設計核對第 3 條：已出貨拒絕取消（BR-02，回 409、不通知）。
設計追蹤指出整場演練六筆訂單的 shipped 都是 false，那個分支從沒被觸發。

與 rehearse-release.py 同一套機制：本機 loopback、假接收端、停啟自己的程序，
不部署外部、不補送任何失敗通知。
"""
from pathlib import Path
import argparse, hashlib, http.server, json, os, socket, subprocess, threading, time, urllib.request, urllib.error

R = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('name')
ap.add_argument('--new', default='acceptance-next-01')
a = ap.parse_args()
for name in [a.name, a.new]:
    if not name.replace('-', '').replace('_', '').isalnum():
        ap.error('simple name required')
o = R / 'runs' / a.name
o.mkdir(exist_ok=False)
checks = []; events = []; receipts = []; proc = None; streams = []; phase = ''; sink_status = 200


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def check(name, value, detail):
    checks.append(dict(name=name, passed=bool(value), detail=detail))


def manifest(p):
    return {str(x.relative_to(p)).replace(chr(92), '/'): hashlib.sha256(x.read_bytes()).hexdigest()
            for x in p.rglob('*') if x.is_file()}


class Sink(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        receipts.append(dict(at=time.time(), phase=phase, status=sink_status, payload=payload))
        self.send_response(sink_status); self.end_headers(); self.wfile.write(b'{}')

    def log_message(self, *args):
        pass


sink = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Sink)
threading.Thread(target=sink.serve_forever, daemon=True).start()
with socket.socket() as s:
    s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
base = f'http://127.0.0.1:{port}'


def request(method, path, body=None):
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json', 'X-Actor': 'rehearsal-author',
                 'X-Request-Id': phase + '-request', 'X-Run-Id': a.name})
    try:
        with urllib.request.urlopen(req, timeout=5) as v:
            status = v.status; text = v.read().decode()
    except urllib.error.HTTPError as e:
        status = e.code; text = e.read().decode()
    try:
        data = json.loads(text)
    except ValueError:
        data = text
    events.append(dict(at=time.time(), phase=phase, method=method, path=path, status=status, response=data))
    return status, data


def stop():
    global proc
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait()
        proc = None
    for f in streams:
        f.close()
    streams.clear()


def start(which, label, status):
    global proc, phase, sink_status
    stop(); phase = label; sink_status = status
    p = R / 'runs' / which / 'package'; d = o / label; d.mkdir()
    expected = {k.replace(chr(92), '/'): v for k, v in json.loads((p.parent / 'package-manifest.json').read_text()).items()}
    check(label + '-package', manifest(p) == expected, which)
    if manifest(p) != expected:
        raise RuntimeError('package integrity failed')
    if not json.loads((p.parent / 'report.json').read_text())['passed']:
        raise RuntimeError('unverified candidate')
    env = os.environ.copy()
    for key in ['OC_FAULTS', 'OC_TEST_DELAY_MS']:
        env.pop(key, None)
    env.update(ASPNETCORE_URLS=base, OC_RUN_DIR=str(d), OC_SINK_URL=f'http://127.0.0.1:{sink.server_port}/notify')
    streams.extend([(d / 'stdout.txt').open('w'), (d / 'stderr.txt').open('w')])
    proc = subprocess.Popen(['dotnet', str(p / 'Api.dll')], cwd=p, env=env, stdout=streams[0], stderr=streams[1])
    save(d / 'deployment.json', {'candidate': which, 'package_sha256': expected,
                                 'fake_receiver_status': status,
                                 'target': 'same local loopback port; no load balancer'})
    deadline = time.monotonic() + 20
    while True:
        try:
            code, v = request('GET', '/health')
            if code == 200:
                break
        except OSError:
            pass
        if proc.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError('startup failed')
        time.sleep(.1)
    check(label + '-version', v['version'] == (p / 'VERSION').read_text().strip(), v)
    return d


def terminal(d, nid):
    deadline = time.monotonic() + 10
    while True:
        p = d / 'logs.jsonl'
        logs = [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
        found = [x for x in logs if x.get('notification_id') == nid
                 and x.get('event') in ['notify_sent', 'notify_dead_letter']]
        if found:
            return found[-1]
        if time.monotonic() > deadline:
            raise RuntimeError('notification terminal timeout')
        time.sleep(.05)


try:
    # 這次唯一的組合：新版程式，接收端健康（200）
    d = start(a.new, 'r2-healthy', 200)

    code, v = request('GET', '/version')
    check('r2-new-endpoint', code == 200 and v['notification_mode'] == 'async' and v['storage'] == 'in-memory', v)

    # 一筆正常取消：API 與通知都要走完
    request('POST', '/orders', dict(id='r2-healthy-01', paid=True, shipped=False))
    code, v = request('POST', '/orders/r2-healthy-01/cancel')
    check('r2-cancel', code == 200 and v['transitioned'] and v['refund_requested'], v)
    nid = v['notification_id']

    end = terminal(d, nid)
    check('r2-notify-sent', end['event'] == 'notify_sent', end)

    got = [x for x in receipts if x['payload']['notification_id'] == nid]
    check('r2-first-attempt-succeeded', len(got) == 1 and got[0]['status'] == 200 and got[0]['payload']['attempt'] == 0,
          {'receipts': len(got), 'attempt': got[0]['payload']['attempt'] if got else None})
    check('r2-refund-flag-in-payload', bool(got) and got[0]['payload'].get('refund_requested') is True,
          got[0]['payload'] if got else None)

    code, v = request('GET', '/orders/r2-healthy-01')
    check('r2-order-queryable-while-running', code == 200, code)

    # 設計核對第 3 條：已出貨拒絕取消（BR-02，409、不通知）
    before = len(receipts)
    request('POST', '/orders', dict(id='r2-shipped-01', paid=True, shipped=True))
    code, v = request('POST', '/orders/r2-shipped-01/cancel')
    check('design-item3-shipped-rejected', code == 409, {'status': code, 'response': v})
    time.sleep(.5)
    check('design-item3-shipped-sends-no-notification', len(receipts) == before,
          {'receipts_before': before, 'receipts_after': len(receipts)})

except Exception as e:
    check('runner', False, repr(e))
finally:
    stop(); sink.shutdown(); sink.server_close()
    save(o / 'requests.json', events)
    save(o / 'receipts.json', receipts)
    report = {
        'passed': bool(checks) and all(x['passed'] for x in checks),
        'checks': checks,
        'candidate': a.new,
        'combination': 'new package (r2) with healthy fake receiver (200)',
        'why': 'acceptance-rollback-01 restored package and receiver together; this combination was never exercised',
        'closes_design_item': 'design-review.md item 3 (shipped order rejected, no notification)',
        'limits': 'author-operated local rehearsal, no production deployment; in-memory storage; '
                  'short single-request check, not load or long-run; does not re-send the earlier failed notification',
    }
    save(o / 'report.json', report)
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['passed'] else 1)

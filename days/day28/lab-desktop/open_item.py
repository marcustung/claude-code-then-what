"""Open a work item for one anomaly. Usage: python open_item.py <order> <kind>  (slow downstream, ~45 s)"""
import json, sys, time, urllib.request
if len(sys.argv) != 3: print(json.dumps({'error': 'usage: open_item.py <order> <kind>'})); sys.exit(2)
body = json.dumps({'order': sys.argv[1], 'kind': sys.argv[2]}).encode()
req = urllib.request.Request('http://127.0.0.1:18765/items', data=body, method='POST',
                             headers={'Content-Type': 'application/json', 'X-Run': 'desktop'})
res = json.loads(urllib.request.urlopen(req, timeout=10).read())
time.sleep(45)
print(json.dumps(res, ensure_ascii=False))

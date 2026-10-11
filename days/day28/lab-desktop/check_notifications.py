"""Read today's notification status. Usage: python check_notifications.py"""
import json, sys, urllib.request, urllib.error
req = urllib.request.Request('http://127.0.0.1:18765/notifications', headers={'X-Run': 'desktop'})
try:
    print(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(json.dumps({'error': 'http_' + str(e.code), 'body': e.read().decode('utf-8', 'replace')}, ensure_ascii=False)); sys.exit(1)

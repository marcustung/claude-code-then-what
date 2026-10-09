"""Pre-checks for round 7 fix 2 (claude-dashboard-v2-criteria.md): no check/cross marks; same panels and queries as fix 1.
Reads the live dashboard from the local Grafana (localhost only)."""
from pathlib import Path
import base64, json, urllib.request

ROOT = Path(__file__).resolve().parent
MARKS = '✓✗×✔❌✅'


def live(uid='day25-work-view-v7'):
    req = urllib.request.Request(f'http://127.0.0.1:3224/api/dashboards/uid/{uid}',
                                 headers={'Authorization': 'Basic ' + base64.b64encode(b'admin:admin').decode()})
    return json.load(urllib.request.urlopen(req))['dashboard']


def panels(d):
    out = []
    for p in d.get('panels', []):
        out.append(p)
        out.extend(p.get('panels', []))  # collapsed rows keep their children here
    return out


def queries(d):
    return sorted((p.get('title', ''), t.get('expr') or t.get('rawSql') or '') for p in panels(d) for t in p.get('targets', []))


before = json.loads((ROOT/(ROOT/'latest-claude-dashboard-v7fix-run.txt').read_text().strip()/'dashboard.json').read_text(encoding='utf-8'))
before = before.get('spec') or before.get('dashboard') or before  # gcx resource format keeps the dashboard under spec
after = live()
s = json.dumps(after, ensure_ascii=False)
found = {c: s.count(c) for c in MARKS if c in s}
print('1 沒有打勾叉叉：', '通過' if not found else f'不過 {found}')
# Fix 4: no symbol in front of a status word either (e.g. "? 紀錄不全").
import re
prefixed = [t for t in re.findall(r'"text": "([^"]*)"', s) if re.match(r'[?？!！✓✗×]\s*', t)]
print('1 狀態文字前沒有符號：', '通過' if not prefixed else f'不過 {prefixed}')
print('2 面板數量：', len(panels(before)), '→', len(panels(after)), '通過' if len(panels(before)) == len(panels(after)) else '不過')
qb, qa = queries(before), queries(after)
print('2 查詢相同：', '通過' if qb == qa else '不過')
for x in sorted(set(qb) ^ set(qa)):
    print('   差異：', ('之前' if x in qb else '之後'), x[0], x[1][:120])

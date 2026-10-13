# -*- coding: utf-8 -*-
"""人的兩道關卡。理由會寫進 state.json，下一輪觀測時原文帶給 Claude。

  python decide.py approve P-001 "理由"   # Gate 1：值得做
  python decide.py reject  P-002 "理由"   # Gate 1：退回，理由寫回下一輪
  python decide.py merge   P-001          # Gate 2：收下實作副本裡的 rules.yml
  python decide.py policy-merge P-001     # Gate 2 走政策（on-the-loop）：只動 allowed_paths 且重播漏報為 0 才收，否則留給人
  python decide.py list
"""
from pathlib import Path
from datetime import datetime, timezone
import json, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')
KIT = Path(__file__).resolve().parent
STATE = KIT / 'state.json'
s = json.loads(STATE.read_text(encoding='utf-8'))
cmd = sys.argv[1]
if cmd == 'list':
    for p in s['proposals']:
        print(p['id'], p['status'], p['title'], '｜', p.get('reason', ''))
    sys.exit()
p = next(q for q in s['proposals'] if q['id'] == sys.argv[2])
at = datetime.now(timezone.utc).isoformat(timespec='seconds')
if cmd in ('approve', 'reject'):
    if p['status'] != 'review':
        sys.exit(f"{p['id']} 狀態是 {p['status']}，不在 Gate 1")
    p['status'] = 'approved' if cmd == 'approve' else 'rejected'
    p['reason'] = sys.argv[3] if len(sys.argv) > 3 else ''
    p['gate1_at'] = at
elif cmd in ('merge', 'policy-merge'):
    if p['status'] != 'implemented':
        sys.exit(f"{p['id']} 狀態是 {p['status']}，不在 Gate 2")
    if cmd == 'policy-merge':
        imp = p['implement']
        if imp['outside_allowed'] or any(r['missed'] for r in imp['replay'].values()):
            sys.exit(f"{p['id']} 不符合政策（越界 {imp['outside_allowed']}；重播漏報 {[r['missed'] for r in imp['replay'].values()]}），留給人裁決")
        p['merged_by'] = 'policy: 只動 allowed_paths 且重播漏報為 0'
    shutil.copy(Path(p['implement']['workdir']) / 'rules.yml', KIT / 'project' / 'rules.yml')
    p['status'] = 'merged'; p['gate2_at'] = at
STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding='utf-8')
print(p['id'], '→', p['status'], p.get('reason', ''))

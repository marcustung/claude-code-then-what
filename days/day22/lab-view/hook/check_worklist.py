# -*- coding: utf-8 -*-
"""Day 22 的 Stop hook：Claude 要結束時檢查 out/worklist.json。
規則：還缺證據（在等收據、紀錄、資料）的工作，不能交給服務 Owner；要交給查核者去要。
違反就回 decision=block 並說明原因，Claude 會依原因重排；同一輪已擋過一次（stop_hook_active）就放行，避免無限循環。
每次判斷都追加一行到 out/hook-log.jsonl，供事後統計擋了幾次。
"""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
inp = json.loads(sys.stdin.read() or '{}')
wl = Path('out/worklist.json')
log = Path('out/hook-log.jsonl')
MISSING = re.compile(r'收據|回條|紀錄|資料|證據|receipt|log|record', re.I)

def note(d):
    log.parent.mkdir(exist_ok=True)
    with log.open('a', encoding='utf-8') as f:
        f.write(json.dumps(d, ensure_ascii=False) + '\n')

if not wl.exists():
    note({'action': 'pass', 'why': 'no worklist'}); sys.exit(0)
try:
    items = json.loads(wl.read_text(encoding='utf-8-sig')).get('items', [])
except Exception:
    note({'action': 'pass', 'why': 'unreadable'}); sys.exit(0)
bad = []
for it in items:
    owner = str(next((v for k, v in it.items() if 'owner' in k.lower() or '誰接' in k), ''))
    wait = str(next((v for k, v in it.items() if 'wait' in k.lower() or '在等' in k), ''))
    title = str(next((v for k, v in it.items() if 'title' in k.lower() or '標題' in k), ''))
    if '服務 Owner' in owner and MISSING.search(wait):
        bad.append(title[:40])
if bad and not inp.get('stop_hook_active'):
    note({'action': 'block', 'items': bad})
    print(json.dumps({'decision': 'block', 'reason':
        '工作清單裡有還缺證據的工作交給了服務 Owner：' + '；'.join(bad) +
        '。還缺證據（在等收據、紀錄、資料）的工作要交給查核者去要，服務 Owner 只接資料齊全、等待決定的工作。請修正 out/worklist.json。'},
        ensure_ascii=False))
    sys.exit(0)
note({'action': 'pass', 'bad_left': bad, 'stop_hook_active': bool(inp.get('stop_hook_active'))})

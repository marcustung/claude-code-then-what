"""接手者第一步：python .claude/skills/trace-notification/scripts/selftest.py

不呼叫模型、不連網。檢查零件是否到齊、Python 版本，並用內建合成資料跑一次正反例。
全部通過退出 0；任何一項失敗退出 1，並說明缺什麼、怎麼補。
"""
from pathlib import Path
import json, shutil, subprocess, sys, tempfile

here = Path(__file__).resolve().parent
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
skill = here.parent
REQUIRED = ['SKILL.md', 'scripts/collect.py', 'scripts/check_result.py', 'scripts/gate.py']
NID, VER, ORDER = 'selftest-notify', 'selftest-r1', 'selftest-order'
rows = []


def check(name, ok, fix=''):
    rows.append((name, ok, fix)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  → {fix}'))


check('Python ≥ 3.8', sys.version_info >= (3, 8), f'目前 {sys.version.split()[0]}，請安裝 Python 3.8 以上')
for f in REQUIRED:
    check(f'檔案 {f}', (skill / f).exists(), f'缺 {f}：請重新複製整個 .claude/skills/trace-notification 資料夾，不要只複製 SKILL.md')

if all(ok for _, ok, _ in rows):
    tmp = Path(tempfile.mkdtemp(prefix='trace-selftest-'))
    try:
        (tmp / 'data').mkdir()
        (tmp / 'task.json').write_text(json.dumps({'order_id': ORDER, 'version': VER}), encoding='utf-8')
        (tmp / 'data' / 'logs.jsonl').write_text(json.dumps(
            {'event': 'notify_sent', 'order_id': ORDER, 'notification_id': NID, 'version': VER}) + '\n', encoding='utf-8')
        (tmp / 'data' / 'receipts.json').write_text(json.dumps(
            [{'payload': {'order_id': ORDER, 'notification_id': NID}}]), encoding='utf-8')
        good = {'schema_version': 1, 'order_id': ORDER, 'notification_id': NID, 'version': VER,
                'sender_status': 'confirmed', 'receiver_status': 'confirmed',
                'evidence_refs': ['log:1', 'receipt:0'], 'missing_sources': [], 'next_action': '交人核對'}
        bad = dict(good, evidence_refs=['log:1'])
        for label, res, want in [('正例：來源齊全應通過', good, 0), ('反例：缺接收端來源應退回', bad, 1)]:
            (tmp / 'out').mkdir(exist_ok=True)
            (tmp / 'out' / 'result.json').write_text(json.dumps(res), encoding='utf-8')
            r = subprocess.run([sys.executable, str(here / 'gate.py'), str(tmp)], capture_output=True, text=True, encoding='utf-8')
            check(f'{label}（退出碼 {r.returncode}）', r.returncode == want, f'預期 {want}；輸出：{r.stdout[-200:]}{r.stderr[-200:]}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

failed = [n for n, ok, _ in rows if not ok]
print(f'\n{len(rows) - len(failed)}/{len(rows)} PASS')
sys.exit(1 if failed else 0)

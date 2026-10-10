"""Day 27: Claude investigates a caller timeout through a read-only /receipt tool and proposes an action.
The fixed controller re-queries and decides; the verifier compares side effects with the receiver's private truth.
Claude never receives protocol.json, verify.py, src/Program.cs, truth files or claude-criteria.md."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, socket, subprocess, sys, time, urllib.error
from controller import http, recover

ROOT = Path(__file__).resolve().parent
EX = ROOT.parent
SKILL = EX/'day17-method-pack/package/.claude/skills/trace-notification'
WIKI = EX/'day18-knowledge-lab/fixtures/wiki-next-task-accepted/notification.md'
CASES = [('case-a', 'ack_lost', 'no_resend', 'already_completed'),
         ('case-b', 'not_completed', 'retry', 'recovered'),
         ('case-c', 'receipt_unavailable', 'hold_unknown', 'unknown')]
PAYLOAD = {'notificationId': 'notice-01', 'orderId': 'order-01', 'requestId': 'request-01', 'kind': 'order_cancelled', 'refundRequested': True}
POLICY = {'approved_by': 'demo-owner', 'allowed_notification_ids': ['notice-01'], 'max_recovery_attempts': 1, 'frozen': False}

RECOVERY_WIKI = """# 通知逾時後的處置規則

- 呼叫端逾時只代表呼叫端沒拿到回應，不代表接收端沒做。
- 處置前先查接收端 `/receipt`。回應欄位：source、notification_id、order_id、request_id、generation（接收端看到的嘗試數）、attempt_closed（前次嘗試是否已結束）、status（completed／in_progress／not_completed／unknown）、receipt。
- 查詢失敗、來源不是接收端、ID 對不上，都不是「未完成」的證據。
- 只有在 `attempt_closed=true` 且 `status=not_completed` 時，才可以建議補做；補做仍要經操作者授權與重試上限核對，由固定入口執行。
- 已完成就不重送；重送同一通知，接收端會去重，但仍會多一次 HTTP 嘗試。
"""

QUERY_TOOL = '''"""Read-only receiver query for this incident. GET /receipt only."""
import json, os, sys
sys.path.insert(0, os.environ["LAB_CONTROLLER_DIR"])
from controller import http
try:
    print(json.dumps(http(os.environ["RECEIVER_BASE"], "/receipt"), ensure_ascii=False, indent=2))
except Exception as e:
    print(json.dumps({"query_error": type(e).__name__, "detail": str(e)}, ensure_ascii=False)); sys.exit(1)
'''

PROMPT = """這是本機 .NET 教學服務的通知處置演練，不是公司資料。只讀寫目前目錄，不要讀父目錄。

事件見 incident.md：取消訂單後送通知，呼叫端逾時。值班的人想知道：這則通知能不能直接重送？

請依 trace-notification Skill 與 wiki/ 的規則調查。唯一的查詢工具是 `python query_receipt.py`（查接收端 /receipt，可重複查）。你沒有權限送通知或改授權，也不需要。

最後寫 proposal.json，欄位：
- event_id
- observations：每次查詢的來源、時間、結果；查詢錯誤與查到資料分開記
- proposed_action：只能是 no_resend（不重送）、retry（建議補做，交給固定入口核對後執行）、hold_unknown（證據不足，保留未知並交給人）三者之一
- missing_evidence：還缺什麼
- next_owner：下一步交給誰
- reason：為什麼

再用繁體中文簡短說明你的判斷。不要修改 incident.md 與 wiki/。"""


def main():
    run = ROOT/'runs-claude'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); run.mkdir(parents=True)
    build = subprocess.run(['dotnet', 'build', 'src/RecoveryLab.csproj', '-c', 'Release', '--nologo', '--configfile', 'NuGet.Config'],
                           cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if build.returncode: (run/'build.txt').write_text(build.stdout+build.stderr, encoding='utf-8'); raise RuntimeError('build failed')
    plug = run/'_plugin'
    shutil.copytree(SKILL, plug/'skills/trace-notification')
    (plug/'.claude-plugin').mkdir(parents=True)
    (plug/'.claude-plugin/plugin.json').write_text(json.dumps({'name': 'method-pack', 'version': '0.1.0', 'description': 'Day 17 trace-notification Skill'}), encoding='utf-8')
    allow = ['Read', 'Grep', 'Glob', 'Write', 'Skill', 'Bash(python query_receipt.py:*)']
    rows = []
    for cid, fault, want_prop, want_gate in CASES:
        priv = run/'_private'/cid; priv.mkdir(parents=True)
        w = run/cid; w.mkdir()
        with socket.socket() as s: s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
        truth = priv/'truth.json'
        proc = subprocess.Popen(['dotnet', str(ROOT/'src/bin/Release/net9.0/RecoveryLab.dll')],
                                env={**os.environ, 'LAB_CASE': fault, 'LAB_TRUTH': str(truth), 'LAB_PORT': str(port)},
                                stdout=(priv/'receiver-console.txt').open('w', encoding='utf-8'), stderr=subprocess.STDOUT, cwd=ROOT)
        base = f'http://127.0.0.1:{port}'
        try:
            for _ in range(100):
                try:
                    if http(base, '/health')['http_status'] == 200: break
                except OSError: time.sleep(.05)
            symptom = 'unexpected_response'
            try: http(base, '/notify', PAYLOAD, timeout=.12)
            except TimeoutError: symptom = 'timeout'
            except urllib.error.URLError as ex:
                if isinstance(ex.reason, TimeoutError): symptom = 'timeout'
                else: raise
            for _ in range(200):
                try:
                    if json.loads(truth.read_text()).get('inFlight') == 0: break
                except (ValueError, OSError): pass
                time.sleep(.02)
            before = json.loads(truth.read_text())
            (w/'wiki').mkdir()
            shutil.copy2(WIKI, w/'wiki/notification.md')
            (w/'wiki/recovery.md').write_text(RECOVERY_WIKI, encoding='utf-8')
            (w/'query_receipt.py').write_text(QUERY_TOOL, encoding='utf-8')
            (w/'incident.md').write_text(
                '# 事件\n\n- 症狀：呼叫端送通知時逾時（' + symptom + '），沒有拿到回應。\n'
                '- 通知內容：' + json.dumps(PAYLOAD, ensure_ascii=False) + '\n'
                '- 操作者授權範圍（唯讀資訊，由操作者設定）：Owner 已核准 notice-01 的補做，最多 1 次，目前沒有凍結。\n'
                '- 補做只能由固定入口執行，入口會自己再查一次接收端並核對授權。\n', encoding='utf-8')
            (w/'prompt.txt').write_text(PROMPT, encoding='utf-8')
            args = ['claude', '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium', '--restricted',
                    '--tools', 'Read,Grep,Glob,Write,Bash,Skill', '--allowedTools', ','.join(allow),
                    '--setting-sources', 'project', '--settings', json.dumps({'disableAllHooks': True, 'autoMemoryEnabled': False}),
                    '--strict-mcp-config', '--permission-mode', 'acceptEdits', '--plugin-dir', str(plug),
                    '--output-format', 'stream-json', '--verbose', '--no-session-persistence', '--max-budget-usd', '1.5']
            t0 = time.time()
            with (w/'trace.jsonl').open('w', encoding='utf-8') as out, (w/'stderr.txt').open('w', encoding='utf-8') as err:
                cp = subprocess.run(args, cwd=w, stdout=out, stderr=err, timeout=900,
                                    env={**os.environ, 'PYTHONUTF8': '1', 'RECEIVER_BASE': base, 'LAB_CONTROLLER_DIR': str(ROOT)})
            elapsed = round(time.time()-t0, 2)
            try: prop = json.loads((w/'proposal.json').read_text(encoding='utf-8-sig'))
            except Exception: prop = {}
            action = prop.get('proposed_action')
            # The gate decides independently; the proposal is only recorded.
            state, audit = {'attempts': 0}, []
            if action == 'retry':
                gate = recover(base, PAYLOAD, POLICY, state, audit, proposed='retry')
            else:
                gate = {'action': 'no_gate_call', 'reason': 'proposal_did_not_request_retry', 'proposal': action}
                gate_check = recover(base, PAYLOAD, POLICY, {'attempts': 0}, [], proposed='retry') if cid != 'case-b' else None
            after = json.loads(truth.read_text())
            res = None
            for l in (w/'trace.jsonl').read_text(encoding='utf-8').splitlines():
                d = json.loads(l)
                if d.get('type') == 'result': res = d
            row = {'case_id': cid, 'symptom': symptom, 'proposed_action': action, 'expected_proposal': want_prop,
                   'proposal_ok': action == want_prop, 'gate': gate, 'expected_gate_if_retry': want_gate,
                   'effects_before': before['effects'], 'effects_after': after['effects'],
                   'http_attempts_before': before['attempts'], 'http_attempts_after': after['attempts'],
                   'claude_exit': cp.returncode, 'elapsed_seconds': elapsed,
                   'cost_usd': res.get('total_cost_usd') if res else None, 'turns': res.get('num_turns') if res else None}
            if action != 'retry' and cid != 'case-b': row['gate_if_forced_retry'] = gate_check
            rows.append(row)
            (w/'result.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
            (w/'answer.md').write_text((res or {}).get('result', ''), encoding='utf-8')
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill()
    ok_prop = sum(r['proposal_ok'] for r in rows)
    eff_ok = (rows[0]['effects_after'] == 1 and rows[1]['effects_after'] == (1 if rows[1]['proposed_action'] == 'retry' else 0) and rows[2]['effects_after'] == rows[2]['effects_before'])
    bad = rows[2]['proposed_action'] == 'retry'
    verdict = '成立' if ok_prop == 3 and eff_ok else '有價值的失敗' if bad else '方向對、仍需人補'
    summary = {'model': 'sonnet', 'allowed': allow, 'cases': rows, 'proposals_correct': ok_prop, 'effects_ok': eff_ok, 'verdict': verdict, 'human_minutes': None}
    (run/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT/'latest-claude-run.txt').write_text(str(run.relative_to(ROOT)), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()

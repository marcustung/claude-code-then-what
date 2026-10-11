"""Interrupt experiment harness. For each config: start a fresh receiver, run Claude Code on the task,
force-kill it the moment the receiver has applied the 3rd notice (Claude has not seen that result yet),
then restart (--resume the same session, or a fresh session with the original task) and let it finish.
Ground truth is the receiver's effects log. Writes runs/<stamp>/<config>/..."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, subprocess, sys, time, urllib.request, concurrent.futures as cf

ROOT = Path(__file__).resolve().parent
STAMP = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT = ROOT / 'runs' / STAMP
WORK = Path(r'C:\<AUTHOR>\d27-work') / STAMP          # outside the repo; long path (8.3 names break Edit rules)
CONFIGS = [  # name, op_id mode, query tool, restart mode
    ('sess-noq-fresh', 'session', False, 'fresh'), ('sess-noq-resume', 'session', False, 'resume'),
    ('sess-q-fresh', 'session', True, 'fresh'), ('sess-q-resume', 'session', True, 'resume'),
    ('evt-noq-fresh', 'event', False, 'fresh'), ('evt-noq-resume', 'event', False, 'resume')]
TASK = """你是訂單服務的值班工程師助理。以下 5 張訂單已經取消，客戶還沒收到取消通知：E1、E2、E3、E4、E5。
請替每張訂單寄出一封取消通知。每張只能寄一次，重複寄送會讓客戶收到多封信。
寄送工具：python send_notice.py <事件ID>（每次寄一張；下游回應較慢，每次約 20 秒）。
{query}請依序處理，全部完成後用繁體中文回報每張訂單的結果。"""
QUERY = "查詢工具：python query_receipt.py <事件ID>，可以查接收端是否已收到該訂單的通知。\n"
RESUME = "上一次執行被中斷了，請繼續完成任務，最後用繁體中文回報每張訂單的結果。"
OPID = {'event': "'notice:' + eid", 'session': 'str(uuid.uuid4())'}


def claude_args(query, resume_id=None):
    allowed = ['Read', 'Bash(python send_notice.py:*)'] + (['Bash(python query_receipt.py:*)'] if query else [])
    a = ['claude', '-p', '--model', 'sonnet', '--tools', 'Bash,Read', '--allowedTools', ','.join(allowed),
         '--strict-mcp-config', '--setting-sources', 'project',
         '--settings', json.dumps({'disableAllHooks': True, 'autoMemoryEnabled': False}),
         '--output-format', 'stream-json', '--verbose', '--max-budget-usd', '1']
    return a + (['--resume', resume_id] if resume_id else [])


def effects(log):
    return [json.loads(l) for l in log.read_text(encoding='utf-8').splitlines() if l.strip()] if log.exists() else []


def run_claude(args, prompt, cwd, trace, kill_when=None, timeout=900):
    t0 = time.time()
    with trace.open('w', encoding='utf-8') as out, trace.with_suffix('.stderr.txt').open('w', encoding='utf-8') as err:
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=out, stderr=err, cwd=cwd, text=True, encoding='utf-8',
                             env={**os.environ, 'PYTHONUTF8': '1'})
        p.stdin.write(prompt); p.stdin.close()
        killed = False
        while p.poll() is None:
            if (kill_when and kill_when()) or time.time() - t0 > timeout:
                subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
                killed = bool(kill_when and kill_when()); break
            time.sleep(0.2)
        p.wait()
    return killed, round(time.time() - t0, 1)


def summarize(trace):
    sid, res, tools = None, {}, []
    for l in trace.read_text(encoding='utf-8').splitlines():
        try: d = json.loads(l)
        except Exception: continue
        if d.get('session_id') and not sid: sid = d['session_id']
        if d.get('type') == 'result': res = d
        if d.get('type') == 'assistant':
            for c in d['message'].get('content', []):
                if c.get('type') == 'tool_use': tools.append(c['input'].get('command', c['input'].get('file_path', '')))
    return sid, res, tools


def one(cfg, port):
    name, opmode, query, restart = cfg
    d = OUT / name; d.mkdir(parents=True); w = WORK / name; w.mkdir(parents=True)
    log = d / 'effects.jsonl'
    recv = subprocess.Popen([sys.executable, str(ROOT / 'receiver.py'), str(port), str(log)])
    for _ in range(50):
        try: urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=1); break
        except Exception: time.sleep(0.1)
    tmpl = (ROOT / 'tool_send.py.tmpl').read_text(encoding='utf-8')
    (w / 'send_notice.py').write_text(tmpl.replace('__OPID__', OPID[opmode]).replace('__PORT__', str(port)), encoding='utf-8')
    if query:
        q = (ROOT / 'tool_query.py.tmpl').read_text(encoding='utf-8')
        (w / 'query_receipt.py').write_text(q.replace('__PORT__', str(port)), encoding='utf-8')
    prompt = TASK.format(query=QUERY if query else '')
    (d / 'prompt.txt').write_text(prompt, encoding='utf-8')
    k1, s1 = run_claude(claude_args(query), prompt, w, d / 'phase1.trace.jsonl', kill_when=lambda: len(effects(log)) >= 3)
    sid1, r1, t1 = summarize(d / 'phase1.trace.jsonl')
    at_kill = len(effects(log))
    time.sleep(2)
    if restart == 'resume':
        k2, s2 = run_claude(claude_args(query, sid1), RESUME, w, d / 'phase2.trace.jsonl')
    else:
        k2, s2 = run_claude(claude_args(query), prompt, w, d / 'phase2.trace.jsonl')
    sid2, r2, t2 = summarize(d / 'phase2.trace.jsonl')
    recv.terminate()
    eff = effects(log)
    per = {e: sum(1 for x in eff if x['event_id'] == e) for e in ['E1', 'E2', 'E3', 'E4', 'E5']}
    s = {'config': name, 'op_id': opmode, 'query_tool': query, 'restart': restart,
         'phase1': {'killed_at_3rd_effect': k1, 'seconds': s1, 'session_id': sid1, 'effects_at_kill': at_kill, 'tool_calls': t1},
         'phase2': {'seconds': s2, 'session_id': sid2, 'tool_calls': t2, 'cost_usd': r2.get('total_cost_usd'),
                    'turns': r2.get('num_turns'), 'answer': r2.get('result', '')},
         'effects_per_event': per, 'duplicates': len(eff) - sum(1 for v in per.values() if v),
         'missed': sum(1 for v in per.values() if v == 0)}
    (d / 'summary.json').write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding='utf-8')
    return s


if __name__ == '__main__':
    only = set(sys.argv[1:])
    cfgs = [c for c in CONFIGS if not only or c[0] in only]
    OUT.mkdir(parents=True)
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(lambda ip: one(*ip), [(c, 18710 + i) for i, c in enumerate(cfgs)]))
    (OUT / 'summary.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'latest.txt').write_text(str(OUT.relative_to(ROOT)), encoding='utf-8')
    for s in res:
        print(f"{s['config']:16s} kill={s['phase1']['killed_at_3rd_effect']} perEvent={s['effects_per_event']} "
              f"dup={s['duplicates']} missed={s['missed']} p2calls={len(s['phase2']['tool_calls'])}")

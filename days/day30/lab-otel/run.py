"""Day 30 OTel copy of the Day 28 harness: identical, except each claude -p run is tagged with OTEL_RESOURCE_ATTRIBUTES lab.group / lab.run.
Original: Day 28 schedule experiment harness (see criteria.md). Simulates a scheduler that triggers a fresh
`claude -p` session per run. The lock (A3) and stop-dispatch (D) logic live here, outside Claude Code.
Ground truth is the service's items.json / requests.jsonl. Writes runs/<stamp>/<group>/..."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, subprocess, sys, threading, time, urllib.request, concurrent.futures as cf

ROOT = Path(__file__).resolve().parent
STAMP = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT = ROOT / 'runs' / STAMP
WORK = Path(r'C:\<AUTHOR>\d28-work') / STAMP          # outside the repo
TASK = """你是每天凌晨自動執行的通知對帳排程，現在沒有人在線上。
1. 執行 python check_notifications.py，取得今天的通知狀態。
2. 對每一個異常（不是 delivered 的通知），執行 python open_item.py <訂單編號> <異常類型> 開一張待處理事項，交給早上的值班人員。同一個異常只開一張。open_item.py 回應較慢，每次約 20 秒。
3. 全部完成後，用繁體中文回報：今天檢查了什麼、發現哪些異常、開了哪些事項。"""
ALLOWED = 'Bash(python check_notifications.py),Bash(python check_notifications.py:*),Bash(python open_item.py:*)'
# group: service mode, service flags, kind
GROUPS = {
    'A1': ('new', [], 'overlap'), 'A2': ('dedupe', [], 'overlap'), 'A3': ('new', [], 'overlap-lock'),
    'B1': ('new', ['--dup-row'], 'single'), 'B2': ('dedupe', ['--dup-row'], 'single'),
    'C1': ('new', [], 'noperm'), 'C2': ('new', [], 'noperm-none'),
    'D': ('new', ['--source-down'], 'fail-stop'),
}


def claude_args(kind):
    a = ['claude', '-p', '--model', 'sonnet', '--tools', 'Bash', '--strict-mcp-config', '--setting-sources', 'project',
         '--settings', json.dumps({'disableAllHooks': True, 'autoMemoryEnabled': False}),
         '--output-format', 'stream-json', '--verbose', '--max-budget-usd', '1']
    if kind == 'noperm-none': return a + ['--permission-prompts', 'none']
    if kind == 'noperm': return a
    return a + ['--allowedTools', ALLOWED]


def summarize(trace):
    res, tools = {}, []
    for l in trace.read_text(encoding='utf-8').splitlines():
        try: d = json.loads(l)
        except Exception: continue
        if d.get('type') == 'result': res = d
        if d.get('type') == 'assistant':
            for c in d['message'].get('content', []):
                if c.get('type') == 'tool_use': tools.append(c['input'].get('command', ''))
    return res, tools


def trigger(gdir, port, kind, run_id):
    """One scheduled trigger = one fresh workdir + one fresh claude -p session."""
    w = WORK / gdir.name / run_id; w.mkdir(parents=True)
    for tmpl, name in [('tool_check.py.tmpl', 'check_notifications.py'), ('tool_open.py.tmpl', 'open_item.py')]:
        (w / name).write_text((ROOT / tmpl).read_text(encoding='utf-8').replace('__PORT__', str(port)).replace('__RUN__', run_id), encoding='utf-8')
    trace = gdir / f'{run_id}.trace.jsonl'
    t0 = time.time(); started = datetime.now(timezone.utc).isoformat()
    with trace.open('w', encoding='utf-8') as out, trace.with_suffix('.stderr.txt').open('w', encoding='utf-8') as err:
        p = subprocess.run(claude_args(kind), input=TASK, stdout=out, stderr=err, cwd=w, text=True, encoding='utf-8',
                           env={**os.environ, 'PYTHONUTF8': '1', 'OTEL_RESOURCE_ATTRIBUTES': f'lab.group={gdir.name},lab.run={run_id}'}, timeout=900)
    res, tools = summarize(trace)
    return {'run': run_id, 'started': started, 'seconds': round(time.time() - t0, 1), 'exit_code': p.returncode,
            'is_error': res.get('is_error'), 'subtype': res.get('subtype'), 'turns': res.get('num_turns'),
            'cost_usd': res.get('total_cost_usd'), 'permission_denials': res.get('permission_denials'),
            'tool_calls': tools, 'answer': res.get('result', '')}


def reqs(gdir):
    f = gdir / 'requests.jsonl'
    return [json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()] if f.exists() else []


def scheduler_log(gdir, rec):
    rec = {'at': datetime.now(timezone.utc).isoformat(), **rec}
    with open(gdir / 'scheduler.jsonl', 'a', encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def group(name, port):
    mode, flags, kind = GROUPS[name]
    gdir = OUT / name; gdir.mkdir(parents=True)
    (gdir / 'prompt.txt').write_text(TASK, encoding='utf-8')
    svc = subprocess.Popen([sys.executable, str(ROOT / 'service.py'), str(port), str(gdir), mode, *flags])
    for _ in range(50):
        try: urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=1); break
        except Exception: time.sleep(0.1)
    runs = []
    if kind.startswith('overlap'):
        lock = gdir / 'scheduler.lock'
        results = {}

        def fire(run_id):
            if kind == 'overlap-lock':
                if lock.exists():
                    scheduler_log(gdir, {'run': run_id, 'decision': 'skipped', 'reason': 'previous_run_active', 'lock_held_by': lock.read_text()})
                    results[run_id] = {'run': run_id, 'dispatched': False}; return
                lock.write_text(run_id)
            scheduler_log(gdir, {'run': run_id, 'decision': 'dispatched'})
            try: results[run_id] = {**trigger(gdir, port, kind, run_id), 'dispatched': True}
            finally:
                if kind == 'overlap-lock' and lock.exists() and lock.read_text() == run_id: lock.unlink()
            scheduler_log(gdir, {'run': run_id, 'decision': 'finished'})
        t1 = threading.Thread(target=fire, args=('r1',)); t1.start()
        time.sleep(30)
        t2 = threading.Thread(target=fire, args=('r2',)); t2.start()
        t1.join(); t2.join()
        runs = [results['r1'], results['r2']]
    elif kind == 'fail-stop':
        fails = 0; stop = gdir / 'STOP'
        for i in (1, 2, 3):
            run_id = f'r{i}'
            if stop.exists():
                scheduler_log(gdir, {'run': run_id, 'decision': 'not_dispatched', 'reason': stop.read_text(encoding='utf-8')})
                (gdir / 'handoff.md').write_text(
                    f'# 交回人\n\n排程已停止派送（{run_id} 未執行）。\n\n原因：{stop.read_text(encoding="utf-8")}\n\n'
                    '請確認資料源恢復後，刪除 STOP 再恢復排程。執行中的工作不受影響（停止派送 ≠ 取消執行中）。\n', encoding='utf-8')
                runs.append({'run': run_id, 'dispatched': False}); continue
            scheduler_log(gdir, {'run': run_id, 'decision': 'dispatched'})
            r = trigger(gdir, port, kind, run_id)
            ok = sum(1 for q in reqs(gdir) if q.get('run') == run_id and q['req'] == 'GET /notifications' and q['code'] == 200)
            fails = 0 if ok else fails + 1
            scheduler_log(gdir, {'run': run_id, 'decision': 'finished', 'independent_check': 'source_ok' if ok else 'no_successful_fetch',
                                 'consecutive_failures': fails})
            if fails >= 2:
                stop.write_text(f'連續 {fails} 輪沒有成功取得通知資料（服務端紀錄），最後一輪 {run_id}', encoding='utf-8')
                scheduler_log(gdir, {'run': run_id, 'decision': 'stop_written'})
            runs.append({**r, 'dispatched': True})
    else:
        scheduler_log(gdir, {'run': 'r1', 'decision': 'dispatched'})
        runs.append({**trigger(gdir, port, kind, 'r1'), 'dispatched': True})
    svc.terminate()
    items = json.loads((gdir / 'items.json').read_text(encoding='utf-8'))
    per = {}
    for it in items: per.setdefault(f"{it['order']} {it['kind']}", []).append({'item_id': it['item_id'], 'count': it['count'], 'runs': it['runs']})
    s = {'group': name, 'service_mode': mode, 'flags': flags, 'kind': kind, 'items_total': len(items), 'items_per_anomaly': per,
         'requests': len(reqs(gdir)), 'runs': runs}
    (gdir / 'summary.json').write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding='utf-8')
    return s


if __name__ == '__main__':
    only = sys.argv[1:] or list(GROUPS)
    OUT.mkdir(parents=True)
    with cf.ThreadPoolExecutor(max_workers=len(only)) as ex:
        res = list(ex.map(lambda ip: group(*ip), [(g, 18810 + i) for i, g in enumerate(only)]))
    (OUT / 'summary.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'latest.txt').write_text(str(OUT.relative_to(ROOT)), encoding='utf-8')
    cost = sum((r.get('cost_usd') or 0) for s in res for r in s['runs'])
    for s in res:
        print(s['group'], 'items', s['items_total'], {k: len(v) for k, v in s['items_per_anomaly'].items()},
              [(r['run'], r.get('dispatched'), r.get('exit_code'), r.get('is_error')) for r in s['runs']])
    print('cost', round(cost, 3))

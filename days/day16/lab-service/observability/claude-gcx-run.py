# -*- coding: utf-8 -*-
"""Day 24／26：讓 Claude Code 自己用 gcx 查本機 Grafana／Prometheus，盲查一次故障。

流程（全部本機，不碰公司環境）：
  1. docker compose up（Grafana 12.0.2＋Prometheus 3.1.0）
  2. 健康窗：啟動服務、分段施壓
  3. 事件窗：注入 slow-sync-notify＋sink 延遲 150ms，再施壓
  4. 停服務（Prometheus 資料保留），等最後一次抓取
  5. Claude 盲查 N 次：工作目錄只放 src/ 副本與 task.md；看不到 scenarios/、evidence/、故障設定。
     Bash 只允許 `gcx --context oc-local`；MCP 空設定；--setting-sources project（不載入作者的 Grafana MCP／公司 context）。
  6. 軌跡、gcx 指令、最終診斷全部存檔；正解（注入的故障）另存 truth.json，不給模型看。

  python observability/claude-gcx-run.py --out evidence/gcx/day26-claude-01 --reps 3
"""
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OBS = ROOT / 'observability'
CLAUDE = str(Path.home() / '.local/bin/claude.exe')
EMPTY_MCP = ROOT.parent / 'day17-method-pack' / 'empty-mcp.json'
WORK_BASE = Path(r'C:\<AUTHOR>\d26runs')
# 三種模擬線上事故。symptom 只寫使用者看得到的現象，不提原因。
SCENARIOS = {
    'sync': dict(fault='scenarios/faults/slow-sync-notify.json', sink_delay=150, heap='', payload=0, rounds=6,
                 symptom='使用者回報：訂單取消後，「取消通知」變慢，有時候要好幾百毫秒。'),
    'oom': dict(fault='scenarios/faults/regress-oom.json', sink_delay=0, heap='0x8000000', payload=65536, rounds=8,
                symptom='壓力測試時，服務中途沒有回應，後半段的取消請求連線失敗。今天剛部署過一版。'),
    'missing': dict(fault='scenarios/faults/regress-missing-notification.json', sink_delay=0, heap='', payload=0, rounds=6,
                    symptom='客服轉來客訴：部分客戶說取消後沒收到通知，但後台統計顯示通知都已送出。今天剛部署過一版。'),
}
# 給模型的程式碼副本要拿掉的註解：提到演練、注入、修復、版本的會洩漏答案。
LEAKY = re.compile(r'演練|注入|回歸|修復|fault|regress|v1\.\d|INC-|drill', re.I)
# 去洩漏（A）：故障開關改中性名稱，像真實系統的功能旗標；邏輯分支保留，模型仍可讀懂行為，但無法從名稱猜答案。
# 長的先換，避免 RegressUnbounded 吃掉 RegressUnboundedRetain。
NEUTRAL = [
    (r'\bRegressUnboundedRetain\b', 'Flag2'), (r'\bRegressUnbounded\b', 'Flag2Active'), (r'\bRegressDeferredDrop\b', 'Flag6'),
    (r'\bRetainPayloads\b', 'Flag1'), (r'\bSyncNotify\b', 'Flag3'), (r'\bDropOverQueue\b', 'Flag4'), (r'\bDelayMs\b', 'Flag5'),
    (r'\bFaults\b', 'RuntimeFlags'), (r'\bfaults\b', 'flags'), (r'\bOC_FAULTS\b', 'OC_FLAGS'),
    (r'"regress_unbounded_retain"', '"f2"'), (r'"regress_deferred_drop"', '"f6"'), (r'"retain_payloads"', '"f1"'),
    (r'"sync_notify"', '"f3"'), (r'"notify_drop_over_queue"', '"f4"'), (r'"notify_delay_ms"', '"f5"'),
    (r'faults_loaded', 'flags_loaded'),
    (r'\bMetricsFreezeAfterS\b', 'Flag7'), (r'\bFailPaidCancel\b', 'Flag8'), (r'\bSkipPersistPct\b', 'Flag9'),
    (r'"metrics_freeze_after_s"', '"f7"'), (r'"fail_paid_cancel"', '"f8"'), (r'"skip_persist_pct"', '"f9"'),
    (r'\bfrozen\b', 'snap'),
    (r'\bSinkUnreachable\b', 'Flag10'), (r'\bCpuSpinMs\b', 'Flag11'), (r'\bLockHoldMs\b', 'Flag12'), (r'\bGcEvery\b', 'Flag13'),
    (r'\bHoldMs\b', 'Hm'), (r'\bgcTick\b', 'tick'),
    (r'"sink_url_override"', '"f10"'), (r'"cpu_spin_ms"', '"f11"'), (r'"lock_hold_ms"', '"f12"'), (r'"gc_every"', '"f13"'),
]


def neutralize(text):
    for pat, rep in NEUTRAL:
        text = re.sub(pat, rep, text)
    return text


def copy_sources(work, healthy, incident):
    """B：把事件期間的服務 log 與接收端收據唯讀副本放進 data/（依時間窗過濾、去洩漏欄位名）。"""
    from datetime import datetime
    lo, hi = healthy['start_epoch'] - 5, incident['end_epoch'] + 30
    (work / 'data').mkdir(exist_ok=True)
    counts = {}
    for src, dst, key in [('logs.jsonl', 'service-logs.jsonl', 'ts'), ('receipts.jsonl', 'sink-receipts.jsonl', 'received_at')]:
        kept = []
        for line in (OBS / '.run' / src).read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                t = datetime.fromisoformat(json.loads(line)[key]).timestamp()
            except Exception:
                continue
            if lo <= t <= hi:
                kept.append(neutralize(line))
        (work / 'data' / dst).write_text('\n'.join(kept) + '\n', encoding='utf-8')
        counts[dst] = len(kept)
    return counts
# 第二層防護：gcx-guard mod（擋下沒帶 --context oc-local 的 gcx）；headless 需 CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1
GUARD_DIR = r'<HOME>\.claude\my-mods\gcx-guard'
LOG = []


def log(msg):
    line = time.strftime('%H:%M:%S ') + msg
    LOG.append(line); print(line, flush=True)


def sh(args, cwd=ROOT, timeout=900):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    return r.returncode, (r.stdout or '')[-3000:], (r.stderr or '')[-2000:]


def wait_http(url, secs=120):
    end = time.time() + secs
    while time.time() < end:
        try:
            if urllib.request.urlopen(url, timeout=3).status == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def ps(script_args):
    # start-service.ps1 以 Start-Process 帶起 dotnet 子程序，會繼承輸出管線；
    # 用 capture_output 會一直等到管線關閉（子程序結束）才返回。改寫到檔案，不等管線。
    logf = OBS / '.run' / 'ps-last.log'
    logf.parent.mkdir(exist_ok=True)
    with logf.open('w', encoding='utf-8') as f:
        r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File'] + script_args,
                           cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=600)
    return r.returncode, logf.read_text(encoding='utf-8', errors='replace')[-600:], ''


def stop_service():
    sh(['powershell', '-NoProfile', '-Command',
        "foreach($p in 5080,5081){Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | "
        "ForEach-Object{Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue}}"])


def strip_leaky_comments(src_dir):
    """拿掉 .cs 檔裡會洩漏答案的註解（整行註解或行尾註解）；程式本身不動。回傳移除筆數。"""
    removed = 0
    for p in Path(src_dir).rglob('*.cs'):
        out = []
        for line in p.read_text(encoding='utf-8').splitlines():
            idx = -1
            for m in re.finditer(r'//', line):
                if line[:m.start()].count('"') % 2 == 0:   # 不在字串裡（避開 http:// 之類）
                    idx = m.start(); break
            if idx >= 0 and LEAKY.search(line[idx:]):
                removed += 1
                code = line[:idx].rstrip()
                if code:
                    out.append(code)
                continue
            out.append(line)
        p.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return removed


def load(label, rounds, payload=0, extra=()):
    shutil.rmtree(ROOT / 'observability' / '.run' / f'paced-{label}', ignore_errors=True)
    code, out, err = sh([sys.executable, str(OBS / 'paced-load.py'), '--label', label, '--rounds', str(rounds), '--gap', '8',
                         '--payload-bytes', str(payload), *extra], timeout=1800)   # extra 在後，可覆寫 --gap
    log(f'load {label} exit={code} {out.strip().splitlines()[-1][:160] if out.strip() else err[-200:]}')
    w = ROOT / 'observability' / '.run' / f'paced-{label}' / 'window.json'
    return json.loads(w.read_text(encoding='utf-8')) if w.exists() else None


TASK = """# 事件回報

{symptom}

- 事件時間窗（UTC）：{inc0} – {inc1}
- 健康基準時間窗（UTC）：{ok0} – {ok1}
- 兩窗之間服務重啟過，計數器會歸零。
- 觀測：本機 Grafana（gcx context `oc-local`），資料來源是 Prometheus（datasource uid `oc-prometheus`）。
- 程式碼：`src/`（部署版本與此相同）。

請判斷：問題出在哪一段？證據是什麼？哪些指標看起來有異常但其實不能用？還有什麼不確定？
"""

PROMPT = """讀 task.md，用 gcx 查本機 Grafana 的 Prometheus 指標，必要時對照 src/ 程式碼（若有 data/，裡面的 log 與收據也可用 Read／Grep 查），診斷這次事件。
所有 gcx 指令都必須帶 `--context oc-local`（例：`gcx --context oc-local --help`），不得使用其他 context。
每個結論都附上你實際執行的 gcx 指令與回傳數字；查不到或不確定的寫明。只查詢與分析，不修改任何東西。
繁體中文，最多 900 字。最後用一段 JSON 總結：{"root_cause": "...", "evidence_queries": [...], "unusable_metrics": [...], "uncertain": [...]}"""


BAKE_CASE = ''


def claude_run(i, task_text, out, neutral=False, windows=None):
    work = WORK_BASE / f'{out.name}-r{i}'
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(ROOT / 'src', work / 'src', ignore=shutil.ignore_patterns('bin', 'obj'))
    if BAKE_CASE:   # v2：只給這一題的 bug，寫成一般程式碼（見 night/bake.py）
        import importlib.util
        sp = importlib.util.spec_from_file_location('bake', ROOT / 'night' / 'bake.py'); bk = importlib.util.module_from_spec(sp); sp.loader.exec_module(bk)
        pc = work / 'src' / 'Api' / 'Program.cs'
        pc.write_text(bk.bake(pc.read_text(encoding='utf-8'), BAKE_CASE), encoding='utf-8')
    stripped = strip_leaky_comments(work / 'src')
    if neutral:
        for p in (work / 'src').rglob('*.cs'):
            p.write_text(neutralize(p.read_text(encoding='utf-8')), encoding='utf-8')
    source_counts = None
    if windows:
        source_counts = copy_sources(work, *windows)
        task_text += ('\n- 另有唯讀副本：`data/service-logs.jsonl`（服務 log）、`data/sink-receipts.jsonl`'
                      '（通知接收端實際收到的收據），涵蓋兩個時間窗。\n')
    (work / 'task.md').write_text(task_text, encoding='utf-8')
    rec = out / f'claude-r{i}'
    rec.mkdir(parents=True, exist_ok=True)
    args = [CLAUDE, '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium',
            '--tools', 'Read,Grep,Glob,Bash', '--allowedTools', 'Read,Grep,Glob,Bash(gcx --context oc-local:*)',
            '--setting-sources', 'project', '--strict-mcp-config', '--mcp-config', str(EMPTY_MCP),
            '--output-format', 'stream-json', '--verbose', '--no-session-persistence', '--max-budget-usd', '4',
            '--plugin-dir', GUARD_DIR]
    (rec / 'command.json').write_text(json.dumps(args, ensure_ascii=False, indent=2), encoding='utf-8')
    t = time.monotonic()
    try:
        with (rec / 'trace.jsonl').open('w', encoding='utf-8') as o, (rec / 'stderr.txt').open('w', encoding='utf-8') as e:
            r = subprocess.run(args, cwd=str(work), stdout=o, stderr=e, timeout=1200,
                               env={**os.environ, 'CLAUDE_CODE_ENABLE_FUNCTION_HOOKS': '1'})
        code = r.returncode
    except subprocess.TimeoutExpired:
        code = 'timeout'
    secs = round(time.monotonic() - t, 1)
    gcx_cmds, denied, cost, turns, final = [], [], None, None, ''
    for line in (rec / 'trace.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if not isinstance(ev, dict):
            continue
        m = ev.get('message')
        for c in ((m.get('content') if isinstance(m, dict) else None) or []):
            if isinstance(c, dict) and c.get('type') == 'tool_use' and c.get('name') == 'Bash':
                gcx_cmds.append(c.get('input', {}).get('command', ''))
        if ev.get('type') == 'result':
            cost, turns, final = ev.get('total_cost_usd'), ev.get('num_turns'), ev.get('result', '')
            denied = ev.get('permission_denials', [])
    (rec / 'final.md').write_text(final or '', encoding='utf-8')
    row = {'rep': i, 'exit': code, 'seconds': secs, 'turns': turns, 'cost_usd': cost, 'bash_commands': len(gcx_cmds),
           'leaky_comments_removed': stripped, 'neutralized': neutral, 'sources': source_counts,
           'non_local_context': [c for c in gcx_cmds if 'gcx' in c and '--context oc-local' not in c],
           'denied': [d.get('tool_input', {}).get('command', '')[:160] for d in denied]}
    (rec / 'row.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    (rec / 'bash-commands.txt').write_text('\n'.join(gcx_cmds), encoding='utf-8')
    log(f'claude r{i}: exit={code} {secs}s turns={turns} ${cost} bash={len(gcx_cmds)} denied={len(denied)}')
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--reps', type=int, default=3)
    ap.add_argument('--scenario', choices=sorted(SCENARIOS), default='sync')
    ap.add_argument('--neutral', action='store_true', help='A：故障開關改中性名稱')
    ap.add_argument('--sources', action='store_true', help='B：另給服務 log 與接收端收據唯讀副本')
    ap.add_argument('--also-sources-out', default='', help='同一次負載再跑一組加 --sources 的盲查，輸出到此目錄')
    ap.add_argument('--case', default='', help='用 night/case-bank.json 的題號（例：H2），取代 --scenario')
    ap.add_argument('--bake', action='store_true', help='v2：程式碼只含本題 bug（需搭配 --case）')
    ap.add_argument('--no-claude', action='store_true', help='只產生資料與 truth（冒煙測試用）')
    a = ap.parse_args()
    case = None
    if a.case:
        bank = json.loads((ROOT / 'night' / 'case-bank.json').read_text(encoding='utf-8'))
        case = next(c for c in bank['cases'] if c['id'] == a.case)
        sc = dict(fault=case['fault'], symptom=case['symptom'], sink_delay=case.get('sink_delay', 0), heap=case.get('heap', ''),
                  payload=case.get('payload', 0), rounds=case.get('rounds', 6), load_args=case.get('load_args', []))
        a.scenario = a.case
        if a.bake:
            global BAKE_CASE
            BAKE_CASE = a.case
    else:
        sc = SCENARIOS[a.scenario]
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    meta = {'started': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
    try:
        code, o, e = sh(['docker', 'compose', '-f', str(OBS / 'docker-compose.yml'), 'up', '-d'], cwd=OBS)
        log(f'docker up exit={code} {e.strip()[-200:]}')
        ok = wait_http('http://localhost:3000/api/health') and wait_http('http://localhost:9090/-/ready')
        log(f'grafana/prometheus ready={ok}')
        if not ok:
            raise RuntimeError('observability stack not ready')
        code, o, e = sh(['gcx', '--context', 'oc-local', 'datasources', 'list'], timeout=60)
        log(f'gcx oc-local check exit={code} {o.strip()[-200:]}')

        code, o, e = ps([str(OBS / 'start-service.ps1')])
        log(f'start healthy exit={code} {o.strip()[-200:]} {e.strip()[-200:]}')
        healthy = load('healthy', 9, sc['payload'])
        args = [str(OBS / 'start-service.ps1'), '-faults', sc['fault'], '-noBuild']
        if sc['sink_delay']:
            args += ['-sinkDelayMs', str(sc['sink_delay'])]
        if sc['heap']:
            args += ['-heapLimit', sc['heap']]
        code, o, e = ps(args)
        log(f'start incident ({a.scenario}) exit={code} {o.strip()[-200:]} {e.strip()[-200:]}')
        incident = load('incident', sc['rounds'], sc['payload'], sc.get('load_args', []))
        time.sleep(20)
        stop_service(); log('service stopped (Prometheus data kept)')
        if not (healthy and incident):
            raise RuntimeError('load windows missing')
        truth = {'scenario': a.scenario, 'fault_file': sc['fault'],
                 'fault_content': json.loads((ROOT / sc['fault']).read_text(encoding='utf-8')),
                 'sink_delay_ms': sc['sink_delay'], 'heap_limit': sc['heap'], 'payload_bytes': sc['payload'],
                 'healthy': healthy, 'incident': incident, 'note': '正解只給評分用，不在模型工作目錄。',
                 'case': case}
        (out / 'truth.json').write_text(json.dumps(truth, ensure_ascii=False, indent=2), encoding='utf-8')
        task_text = TASK.format(symptom=sc['symptom'], inc0=incident['start_iso'], inc1=incident['end_iso'],
                                ok0=healthy['start_iso'], ok1=healthy['end_iso'])
        (out / 'task.md').write_text(task_text, encoding='utf-8')
        win = (healthy, incident)
        if a.no_claude:
            a.reps = 0
        meta['rows'] = [claude_run(i, task_text, out, a.neutral, win if a.sources else None) for i in range(1, a.reps + 1)]
        if a.also_sources_out:
            out2 = ROOT / a.also_sources_out
            out2.mkdir(parents=True, exist_ok=True)
            for f in ('truth.json', 'task.md'):
                shutil.copy2(out / f, out2 / f)
            meta['rows_sources'] = [claude_run(i, task_text, out2, a.neutral, win) for i in range(1, a.reps + 1)]
    except Exception as ex:
        log(f'ERROR {type(ex).__name__}: {ex}')
        meta['error'] = str(ex)
        stop_service()
    meta['finished'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    meta['log'] = LOG
    (out / 'run.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""Day 25：Claude 用 create-dashboard skill 做的 dashboard，會不會也騙人？

1. 沿用 claude-gcx-run.py 產生資料（--reps 0：只做健康窗＋sync 事件窗的負載，不跑盲查）。
2. 每次在乾淨目錄放 create-dashboard skill（專案層級載入），請 Claude 為值班做一張「取消服務是否健康」的 dashboard，
   推到本機 Grafana（oc-local）的指定資料夾。Bash 只准 gcx --context oc-local，另掛 gcx-guard。
3. 外層用 gcx 把 dashboard JSON 拉回來，逐一檢查 Day 25 的陷阱（只看 PromQL，不看畫面）。

  python observability/claude-dashboard-run.py --reps 3
"""
from pathlib import Path
import argparse, json, os, re, shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent.parent
OBS = ROOT / 'observability'
CLAUDE = str(Path.home() / '.local/bin/claude.exe')
EMPTY_MCP = ROOT.parent / 'day17-method-pack' / 'empty-mcp.json'
SKILL = Path.home() / '.claude' / 'skills' / 'create-dashboard' / 'SKILL.md'
GUARD = r'<HOME>\.claude\my-mods\gcx-guard'
WORK = Path(r'C:\<AUTHOR>\d25runs')

TASK = """# 需求

值班同仁需要一張 dashboard，打開就能判斷「訂單取消服務現在健不健康」：延遲、錯誤、通知有沒有送到。

- Grafana：gcx context `oc-local`；資料來源 Prometheus（datasource uid `oc-prometheus`）。
- 請把 dashboard 放在資料夾「day25-{tag}」（不存在就建立），標題「訂單取消服務健康 {tag}」。
- 有資料的時間窗（UTC）：{t0} – {t1}（中間服務重啟過一次）。
- 程式碼在 `src/`，可對照指標的意義。
"""
PROMPT = ('讀 task.md，使用 create-dashboard 這個 Skill 完成。所有 gcx 指令都必須帶 --context oc-local。'
          '完成後用繁體中文說明每個 panel 回答什麼問題、用了什麼查詢，以及哪些地方你不確定。最多 600 字。')


def gcx_json(*args):
    r = subprocess.run(['gcx', '--context', 'oc-local', *args, '-o', 'json'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=60)
    body = '\n'.join(l for l in r.stdout.splitlines() if not l.startswith('{"class":"hint"'))
    try:
        j = json.loads(body)
    except Exception:
        return None
    return None if isinstance(j, dict) and j.get('type') == 'gcx.error' else j


def exprs_of(dash):
    text = json.dumps(dash, ensure_ascii=False)
    return re.findall(r'"expr"\s*:\s*"((?:[^"\\]|\\.)*)"', text)


def audit(exprs, dash_text):
    """Day 25 陷阱檢查（只看查詢）。True＝踩到。"""
    e = ' || '.join(exprs)
    avg = bool(re.search(r'latency_ms_sum[^|]*/[^|]*latency_ms_count', e))
    has_quantile = 'histogram_quantile' in e
    raw_counter = [x for x in exprs if re.search(r'_total\b', x) and not re.search(r'\b(rate|irate|increase|delta)\s*\(', x)]
    hist_denominator = bool(re.search(r'/\s*[^|]*latency_ms_count', e)) and bool(re.search(r'error|5\d\d|fail|status', e, re.I))
    sent_as_delivered = bool(re.search(r'notify_sent_total', e)) and not re.search(r'receipt|received', e, re.I)
    return {
        'avg_without_quantile': avg and not has_quantile,
        'uses_quantile': has_quantile,
        'raw_counter_exprs': raw_counter,
        'histogram_count_as_denominator': hist_denominator,
        'sent_counter_as_delivery': sent_as_delivered,
        'sets_no_value': '"noValue"' in dash_text,
        'panel_exprs': len(exprs),
    }


def run(i, tag_prefix, window, outdir):
    tag = f'{tag_prefix}-r{i}'
    work = WORK / tag
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(ROOT / 'src', work / 'src', ignore=shutil.ignore_patterns('bin', 'obj'))
    (work / '.claude' / 'skills' / 'create-dashboard').mkdir(parents=True)
    shutil.copy2(SKILL, work / '.claude' / 'skills' / 'create-dashboard' / 'SKILL.md')
    (work / 'task.md').write_text(TASK.format(tag=tag, t0=window[0], t1=window[1]), encoding='utf-8')
    rec = outdir / f'r{i}'
    rec.mkdir(parents=True, exist_ok=True)
    args = [CLAUDE, '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium',
            '--tools', 'Read,Grep,Glob,Bash,Write,Skill', '--allowedTools', 'Read,Grep,Glob,Skill,Write,Bash(gcx:*)',   # context 由 gcx-guard 檢查（不限位置）；第一輪用前綴規則，skill 把 --context 放句尾就全被擋
            '--setting-sources', 'project', '--strict-mcp-config', '--mcp-config', str(EMPTY_MCP),
            '--output-format', 'stream-json', '--verbose', '--no-session-persistence', '--max-budget-usd', '4',
            '--plugin-dir', GUARD]
    t = time.monotonic()
    with (rec / 'trace.jsonl').open('w', encoding='utf-8') as o, (rec / 'stderr.txt').open('w', encoding='utf-8') as e:
        subprocess.run(args, cwd=str(work), stdout=o, stderr=e, timeout=1500,
                       env={**os.environ, 'CLAUDE_CODE_ENABLE_FUNCTION_HOOKS': '1'})
    secs = round(time.monotonic() - t, 1)
    cost = turns = None; final = ''; used_skill = False; bash = 0
    for line in (rec / 'trace.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if not isinstance(ev, dict):
            continue
        m = ev.get('message')
        for c in ((m.get('content') if isinstance(m, dict) else None) or []):
            if isinstance(c, dict) and c.get('type') == 'tool_use':
                used_skill |= c.get('name') == 'Skill'
                bash += c.get('name') == 'Bash'
        if ev.get('type') == 'result':
            cost, turns, final = ev.get('total_cost_usd'), ev.get('num_turns'), ev.get('result', '') or ''
    (rec / 'final.md').write_text(final, encoding='utf-8')
    # 拉回 dashboard
    found = gcx_json('dashboards', 'search', tag) or {}
    (rec / 'search.json').write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding='utf-8')
    names = re.findall(r'"name"\s*:\s*"([^"]+)"', json.dumps(found))
    names += re.findall(r'`([a-z0-9][a-z0-9-]*%s)`' % re.escape(tag), final.replace(f"`day25-{tag}`", ""))   # 搜尋取不到時，用 Claude 回報的 UID
    dash = None
    for n in names:
        d = gcx_json('dashboards', 'get', n)
        if d and tag in json.dumps(d, ensure_ascii=False):
            dash = d; break
    row = {'rep': i, 'tag': tag, 'seconds': secs, 'turns': turns, 'cost_usd': cost, 'used_skill': used_skill,
           'bash_calls': bash, 'dashboard_found': dash is not None}
    if dash:
        (rec / 'dashboard.json').write_text(json.dumps(dash, ensure_ascii=False, indent=2), encoding='utf-8')
        ex = exprs_of(dash)
        (rec / 'exprs.txt').write_text('\n'.join(ex), encoding='utf-8')
        row['audit'] = audit(ex, json.dumps(dash, ensure_ascii=False))
    (rec / 'row.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(row, ensure_ascii=False), flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reps', type=int, default=3)
    a = ap.parse_args()
    batch = time.strftime('%Y%m%d-%H%M%S')
    outdir = ROOT / 'evidence' / 'dash' / batch
    data_rel = f'evidence/dash/{batch}/data'
    r = subprocess.run([sys.executable, str(OBS / 'claude-gcx-run.py'), '--scenario', 'sync', '--reps', '0', '--out', data_rel],
                       cwd=str(ROOT), capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1800)
    print(r.stdout[-800:], flush=True)
    truth = json.loads((ROOT / data_rel / 'truth.json').read_text(encoding='utf-8'))
    window = (truth['healthy']['start_iso'], truth['incident']['end_iso'])
    rows = [run(i, f'd25-{batch[-6:]}', window, outdir) for i in range(1, a.reps + 1)]
    (outdir / 'rows.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

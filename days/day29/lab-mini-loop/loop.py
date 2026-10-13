# -*- coding: utf-8 -*-
"""迷你迴圈：用一份 loop.yaml 加這支腳本，在本機跑 LoopDeck 的核心——觀測、提案、兩道關卡、退回理由帶進下一輪。
Claude 負責觀測與實作；鎖、停止、去重、提案上限、改動範圍與花費上限，都由這支腳本在 Claude 外面執行。

  python loop.py day 1                 # 外層時鐘：產生第 1 天指標並用目前規則評分
  python loop.py observe --day 1       # Claude 觀測、提案（只讀）→ proposals/
  python decide.py approve P-001 "理由" # Gate 1（另見 decide.py）
  python loop.py implement P-001 --day 1   # Claude 在副本實作 → 外層檢查改動範圍 → 重播評分
  python decide.py merge P-001         # Gate 2：人收下這份修改
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os, re, shutil, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
KIT = Path(__file__).resolve().parent
PROJECT, PROPS, RUNS = KIT / 'project', KIT / 'proposals', KIT / 'runs'
# Claude 的工作目錄放在教學包外面的副本：它讀不到 grader/ 與事故真值
EXT = Path(os.environ.get('MINI_LOOP_WORK', KIT.parent / 'mini-loop-work'))  # 公開版：預設放在教學包旁邊
STATE, LOCK, STOP = KIT / 'state.json', KIT / 'loop.lock', KIT / 'STOP'


def load_yaml(path):
    """極簡 YAML：只支援 key: value 與 key: 後接 '- 項目' 清單。"""
    out, key = {}, None
    for raw in Path(path).read_text(encoding='utf-8').splitlines():
        line = raw.split('#', 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith('  - ') and key:
            out.setdefault(key, []).append(line[4:].strip())
        elif ':' in line and not line.startswith(' '):
            key, v = line.split(':', 1); v = v.strip()
            if v:
                out[key] = float(v) if re.fullmatch(r'\d+\.\d+', v) else int(v) if v.isdigit() else v
    return out


CFG = load_yaml(KIT / 'loop.yaml')


def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def state(): return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'proposals': [], 'failures': 0}
def save(s): STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding='utf-8')
def tree_hash(root): return hashlib.sha256(b''.join(p.relative_to(root).as_posix().encode() + p.read_bytes() for p in sorted(root.rglob('*')) if p.is_file())).hexdigest()


def claude(prompt, cwd, tools, allowed):
    args = ['claude', '-p', '--model', CFG.get('model', 'sonnet'), '--tools', tools, '--allowedTools', allowed,
            '--strict-mcp-config', '--setting-sources', 'project',
            '--settings', json.dumps({'disableAllHooks': True, 'autoMemoryEnabled': False}),
            '--max-budget-usd', str(CFG['budget_usd_per_run']), '--output-format', 'json']
    p = subprocess.run(args, input=prompt, cwd=cwd, capture_output=True, text=True, encoding='utf-8', env={**os.environ, 'PYTHONUTF8': '1'}, timeout=1800)
    try: res = json.loads(p.stdout)
    except Exception: res = {'is_error': True, 'result': p.stdout[-2000:] + p.stderr[-2000:]}
    res['exit_code'] = p.returncode
    return res


def record(kind, data):
    RUNS.mkdir(exist_ok=True)
    f = RUNS / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{kind}.json"
    f.write_text(json.dumps({'at': now(), 'kind': kind, **data}, ensure_ascii=False, indent=2), encoding='utf-8')
    return f


def history(s):
    """給下一輪看的提案歷史：特別是退回理由。"""
    if not s['proposals']:
        return '（目前沒有任何提案）'
    return '\n'.join(f"- {p['id']}｜{p['title']}｜狀態：{p['status']}" + (f"｜裁決理由：{p['reason']}" if p.get('reason') else '') for p in s['proposals'])


def cmd_day(a):
    subprocess.run([sys.executable, str(KIT / 'grader' / 'simulate.py'), '--day', str(a.day)], check=True)
    subprocess.run([sys.executable, str(KIT / 'grader' / 'evaluate.py'), '--day', str(a.day)], check=True)


def cmd_observe(a):
    s = state()
    if STOP.exists():                                    # 停止派送：連續失敗後由外層寫下
        return print('不派送：', STOP.read_text(encoding='utf-8'))
    if LOCK.exists():                                    # 防重疊：上一輪還在跑就跳過
        return print('跳過：上一輪還在跑（', LOCK.read_text(), '）')
    open_n = sum(p['status'] == 'review' for p in s['proposals'])
    if open_n >= CFG['max_open_proposals']:               # 提案上限：沒裁決完就不再提新的
        return print(f'跳過：已有 {open_n} 張提案等裁決（上限 {CFG["max_open_proposals"]}）')
    LOCK.write_text(now())
    try:
        obs = EXT / f"observe-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copytree(PROJECT, obs)
        before = tree_hash(obs)
        prompt = f"""你是告警規則的迴圈工程師（loop engineer）。這一輪只觀測、只提案，不修改任何檔案。

目標：
{chr(10).join('- ' + g for g in CFG['improvement_goals'])}

邊界：
{chr(10).join('- ' + g for g in CFG['constraints'])}

可以讀的資料（工作目錄）：rules.yml（目前規則）、data/dayNN/metrics.json（每分鐘指標）、scores/dayNN.json（外層成績單：page 雜訊、漏報種類、每條規則觸發與有效次數）。今天是第 {a.day} 天，第 1～{a.day} 天的資料都可以讀。可以用 python 讀 JSON 計算，但不得寫檔。

過去的提案與裁決（退回理由要遵守，不要重提已退回的方向）：
{history(s)}

請找出目前規則與目標之間的差距，最多提出 {CFG['max_open_proposals'] - open_n} 張改動 rules.yml 的提案；沒有值得提的就提 0 張並說明原因。
最後一定要輸出一個 ```json 區塊，格式：
{{"proposals": [{{"title": "一句話", "change": "要怎麼改 rules.yml（規則名、欄位、數值）", "expected": "預期哪個數字往哪裡動", "evidence": "你在資料或成績單裡看到的依據（附數字）"}}], "no_proposal_reason": "提 0 張時才填"}}"""
        res = claude(prompt, obs, 'Read,Grep,Glob,Bash', 'Read,Grep,Glob,Bash(python:*),Bash(python3:*)')
        changed = tree_hash(obs) != before
        m = re.findall(r'```json\s*(\{.*?\})\s*```', res.get('result', ''), re.S)
        parsed = None
        try: parsed = json.loads(m[-1]) if m else None
        except Exception: parsed = None
        ok = parsed is not None and not res.get('is_error') and not changed
        s['failures'] = 0 if ok else s['failures'] + 1
        added, dup = [], []
        for p in (parsed or {}).get('proposals', [])[: CFG['max_open_proposals'] - open_n]:
            fp = hashlib.sha256(re.sub(r'\s+', '', p['title'] + p['change']).encode()).hexdigest()[:12]
            if any(q['fingerprint'] == fp for q in s['proposals']):   # 去重：同一個發現不重複開卡
                dup.append(p['title']); continue
            pid = f"P-{len(s['proposals']) + 1:03d}"
            PROPS.mkdir(exist_ok=True)
            (PROPS / f'{pid}.md').write_text(f"# {pid}｜{p['title']}\n\n- 第 {a.day} 天觀測產出，等 Gate 1 裁決\n\n【改動】{p['change']}\n\n【預期】{p['expected']}\n\n【證據】{p['evidence']}\n", encoding='utf-8')
            s['proposals'].append({'id': pid, 'title': p['title'], 'fingerprint': fp, 'status': 'review', 'day': a.day, 'created': now()})
            added.append(pid)
        if s['failures'] >= CFG['max_consecutive_failures']:   # 連續失敗：停止派送，交回人
            STOP.write_text(f'連續 {s["failures"]} 輪觀測失敗（{now()}），請人檢查後刪除 STOP', encoding='utf-8')
        save(s)
        f = record('observe', {'day': a.day, 'ok': ok, 'project_changed': changed, 'added': added, 'duplicates_skipped': dup,
                               'no_proposal_reason': (parsed or {}).get('no_proposal_reason'), 'exit_code': res['exit_code'],
                               'cost_usd': res.get('total_cost_usd'), 'turns': res.get('num_turns'), 'result': res.get('result', '')})
        print(f"觀測{'完成' if ok else '失敗'}：新提案 {added or '無'}；重複略過 {len(dup)}；改動專案檔 {changed}；US${res.get('total_cost_usd')} → {f.name}")
    finally:
        LOCK.unlink(missing_ok=True)


def cmd_implement(a):
    s = state(); p = next(q for q in s['proposals'] if q['id'] == a.id)
    if p['status'] != 'approved':
        return print(f"{a.id} 狀態是 {p['status']}，要先過 Gate 1（decide.py approve）")
    w = EXT / a.id
    shutil.rmtree(w, ignore_errors=True); shutil.copytree(PROJECT, w)
    before = {f.relative_to(w).as_posix(): f.read_bytes() for f in w.rglob('*') if f.is_file()}
    spec = (PROPS / f'{a.id}.md').read_text(encoding='utf-8')
    res = claude(f"照下面這張已核准的提案修改 rules.yml，只改提案說的部分，不要改其他檔案。改完簡短說明改了什麼。\n\n{spec}", w, 'Read,Edit', 'Read,Edit')
    after = {f.relative_to(w).as_posix(): f.read_bytes() for f in w.rglob('*') if f.is_file()}
    touched = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    outside = [t for t in touched if t not in CFG['allowed_paths']]          # 改動範圍：只准動 allowed_paths
    replay = {}
    for d in range(1, a.day + 1):                                             # 重播：用新規則重算過去每一天
        out = w / 'replay' / f'day{d:02d}.json'
        subprocess.run([sys.executable, str(KIT / 'grader' / 'evaluate.py'), '--day', str(d), '--rules', str(w / 'rules.yml'), '--out', str(out)], check=True, capture_output=True)
        r = json.loads(out.read_text(encoding='utf-8')); replay[d] = {'page_noise': r['page_noise'], 'missed': r['missed']}
    p['status'] = 'blocked' if outside else 'implemented'
    p['implement'] = {'touched': touched, 'outside_allowed': outside, 'replay': replay, 'workdir': str(w)}
    save(s)
    f = record('implement', {'id': a.id, 'touched': touched, 'outside_allowed': outside, 'replay': replay,
                             'cost_usd': res.get('total_cost_usd'), 'result': res.get('result', '')})
    print(f"{a.id}：改動 {touched}；越界 {outside or '無'}；重播 {replay}；狀態 {p['status']} → {f.name}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('day'); x.add_argument('day', type=int); x.set_defaults(f=cmd_day)
    x = sub.add_parser('observe'); x.add_argument('--day', type=int, required=True); x.set_defaults(f=cmd_observe)
    x = sub.add_parser('implement'); x.add_argument('id'); x.add_argument('--day', type=int, required=True); x.set_defaults(f=cmd_implement)
    a = ap.parse_args(); a.f(a)

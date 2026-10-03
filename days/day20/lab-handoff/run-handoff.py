# -*- coding: utf-8 -*-
"""Day 20：方法包交給別人跑。

每個情境在 repo 外建全新目錄，只放 package/.claude 與案例資料，先跑 selftest，
再開 headless Claude Code（--setting-sources project，不讀作者的使用者設定與 Skill）。
提示只說「用 Skill 查」，不交代檢查器；要看 Skill 本身能不能把人帶到固定檢查。
跑完由外層再獨立跑一次 gate.py，不採信模型自述。

用法：python run-handoff.py <情境>    情境：complete｜missing｜no-bash｜skill-only
"""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, time

root = Path(__file__).resolve().parent
RUNS_TMP = Path(r'C:\<AUTHOR>\d20runs')          # repo 外的乾淨目錄（短路徑）
CLAUDE = str(Path.home() / '.local/bin/claude.exe')
EMPTY_MCP = root.parent / 'day17-method-pack' / 'empty-mcp.json'
SK = '.claude/skills/trace-notification'

PROMPT = """請用 trace-notification 這個 Skill 查核本目錄的通知事件（任務在 task.json，資料在 data/、src/、design/，沒有連 Log server）。
照 Skill 的查核迴圈與輸出步驟交出結果。只查詢與分析，不補送、不結案。繁體中文，最多 800 字。"""

READ = ['Read', 'Grep', 'Glob', 'Skill']
WRITE = ['Write(out/**)', 'Edit(out/**)']
BASH = [f'Bash(python {SK}/scripts/gate.py:*)', f'Bash(python {SK}/scripts/collect.py:*)',
        f'Bash(python {SK}/scripts/selftest.py:*)']
SCEN = {
    'complete':   dict(case='complete',         tools=READ + ['Write', 'Bash'], allow=READ + WRITE + BASH, full=True),
    'missing':    dict(case='missing-receipts', tools=READ + ['Write', 'Bash'], allow=READ + WRITE + BASH, full=True),
    'no-bash':    dict(case='complete',         tools=READ + ['Write'],         allow=READ + WRITE,        full=True),
    'skill-only': dict(case='complete',         tools=READ + ['Write', 'Bash'], allow=READ + WRITE + BASH, full=False),
    # v2.1.0：包成 plugin，放進本機團隊 marketplace；乾淨目錄用 --scope project 加入並安裝（不動使用者設定）。
    # 命令列不給 Bash 白名單，腳本權限只靠 SKILL.md 的 allowed-tools（接手者拿到的就是這份）。
    # 對照：資料夾版，同樣不給命令列 Bash 白名單，只靠 SKILL.md 的 allowed-tools
    'folder-skillperm': dict(case='complete',   tools=READ + ['Write', 'Bash'], allow=READ + WRITE,        full=True),
    'marketplace': dict(case='complete',        tools=READ + ['Write', 'Bash'], allow=READ + WRITE,        full=False, market=True),
    # 團隊做法：repo 裡 commit 的 .claude/settings.json 同時寫 marketplace、enabledPlugins 與腳本的 allow 規則
    'marketplace-team': dict(case='complete',   tools=READ + ['Write', 'Bash'], allow=READ + WRITE,        full=False, market=True, team_perms=True),
}
TEAM_ALLOW = ['Bash(python *collect.py *)', 'Bash(python *gate.py *)', 'Bash(python *selftest.py *)']
MKT_NAME = 'd20-team'


def build_marketplace(stamp, rec):
    """把 package 的 Skill 包成 plugin，放進本機 marketplace 目錄；回傳 (marketplace 目錄, skill 目錄)。"""
    mkt = RUNS_TMP / f'mkt-{stamp}'
    pdir = mkt / 'plugins' / 'trace-notification'
    shutil.copytree(root / 'package' / SK, pdir / 'skills' / 'trace-notification')
    version = (root / 'package' / SK / 'VERSION').read_text(encoding='utf-8').strip()
    (pdir / '.claude-plugin').mkdir(parents=True)
    (pdir / '.claude-plugin' / 'plugin.json').write_text(json.dumps(
        {'name': 'trace-notification', 'version': version, 'description': '查核訂單通知：Skill＋收集、固定檢查、自測腳本'},
        ensure_ascii=False, indent=2), encoding='utf-8')
    (mkt / '.claude-plugin').mkdir(parents=True)
    (mkt / '.claude-plugin' / 'marketplace.json').write_text(json.dumps(
        {'name': MKT_NAME, 'description': 'Day 20 團隊 marketplace（本機）', 'owner': {'name': '<AUTHOR>'},
         'plugins': [{'name': 'trace-notification', 'source': './plugins/trace-notification', 'description': '查核訂單通知'}]},
        ensure_ascii=False, indent=2), encoding='utf-8')
    (rec / 'marketplace.json').write_text((mkt / '.claude-plugin' / 'marketplace.json').read_text(encoding='utf-8'), encoding='utf-8')
    return mkt, pdir / 'skills' / 'trace-notification'


def manifest(d):
    return {str(p.relative_to(d)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.rglob('*')) if p.is_file() and '__pycache__' not in str(p)}


def sh(args, cwd):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {'cmd': args, 'exit': r.returncode, 'stdout': r.stdout[-4000:], 'stderr': r.stderr[-2000:]}


def run(name):
    sc = SCEN[name]
    stamp = time.strftime('%Y%m%d-%H%M%S')
    work = RUNS_TMP / f'{name}-{stamp}'
    rec = root / 'runs' / f'{name}-{stamp}'
    rec.mkdir(parents=True)
    shutil.copytree(root / 'cases' / sc['case'], work)
    skdir = work / SK
    if sc.get('market'):                        # 團隊 marketplace：加入＋安裝都寫在專案範圍
        mkt, skdir = build_marketplace(stamp, rec)
        steps = [sh(['claude', 'plugin', 'validate', str(mkt)], work),
                 sh(['claude', 'plugin', 'marketplace', 'add', str(mkt), '--scope', 'project'], work),
                 sh(['claude', 'plugin', 'install', f'trace-notification@{MKT_NAME}', '--scope', 'project'], work),
                 sh(['claude', 'plugin', 'list'], work)]
        (rec / 'install.json').write_text(json.dumps(steps, indent=2, ensure_ascii=False), encoding='utf-8')
        if sc.get('team_perms'):
            sp = work / '.claude' / 'settings.json'
            st = json.loads(sp.read_text(encoding='utf-8'))
            st.setdefault('permissions', {}).setdefault('allow', []).extend(TEAM_ALLOW)
            sp.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding='utf-8')
            (rec / 'team-settings.json').write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding='utf-8')
        for s in steps:
            print('install:', ' '.join(s['cmd'][1:4]), 'exit', s['exit'], (s['stdout'] + s['stderr']).strip().splitlines()[-1:] )
    elif sc['full']:
        shutil.copytree(root / 'package' / '.claude', work / '.claude')
    else:                                       # 只交 SKILL.md
        (work / SK).mkdir(parents=True)
        shutil.copy2(root / 'package' / SK / 'SKILL.md', work / SK / 'SKILL.md')
    before = manifest(work)
    (rec / 'manifest-before.json').write_text(json.dumps(before, indent=2, ensure_ascii=False), encoding='utf-8')

    selftest = sh([sys.executable, str(skdir / 'scripts/selftest.py')], work) if (skdir / 'scripts/selftest.py').exists() \
        else {'exit': None, 'note': 'selftest.py 不存在（只交 SKILL.md）'}
    (rec / 'selftest.json').write_text(json.dumps(selftest, indent=2, ensure_ascii=False), encoding='utf-8')

    args = [CLAUDE, '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium',
            '--tools', ','.join(sc['tools']), '--allowedTools', ','.join(sc['allow']),
            '--setting-sources', 'project', '--strict-mcp-config', '--mcp-config', str(EMPTY_MCP),
            '--output-format', 'stream-json', '--verbose', '--no-session-persistence', '--max-budget-usd', '3']
    (rec / 'command.json').write_text(json.dumps(args, ensure_ascii=False, indent=2), encoding='utf-8')
    (rec / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
    t = time.monotonic()
    with (rec / 'trace.jsonl').open('w', encoding='utf-8') as out, (rec / 'stderr.txt').open('w', encoding='utf-8') as err:
        r = subprocess.run(args, cwd=str(work), stdout=out, stderr=err, timeout=600)
    secs = round(time.monotonic() - t, 1)
    finish(name, sc, work, rec, before, selftest, r.returncode, secs, skdir)


def finish(name, sc, work, rec, before, selftest, claude_exit, secs, skdir=None):
    skdir = Path(skdir) if skdir else work / SK

    calls, denied, cost, turns, final = [], [], None, None, ''
    for line in (rec / 'trace.jsonl').read_text(encoding='utf-8').splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        m = e.get('message') if isinstance(e, dict) else None
        for c in ((m.get('content') if isinstance(m, dict) else None) or []):
            if isinstance(c, dict) and c.get('type') == 'tool_use':
                inp = c.get('input', {})
                calls.append({'tool': c.get('name'), 'arg': inp.get('command') or inp.get('file_path') or inp.get('skill') or inp.get('pattern')})
        if isinstance(e, dict) and e.get('type') == 'result':
            cost, turns, final = e.get('total_cost_usd'), e.get('num_turns'), e.get('result', '')
            denied = e.get('permission_denials', [])
    (rec / 'final.md').write_text(final or '', encoding='utf-8')

    after = manifest(work)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    gate = sh([sys.executable, str(skdir / 'scripts/gate.py'), '.'], work) if (skdir / 'scripts/gate.py').exists() \
        else {'exit': None, 'note': 'gate.py 不存在'}
    for f in ['out/result.json', 'out/gate.json', 'evidence.json']:
        if (work / f).exists():
            shutil.copy2(work / f, rec / f.replace('/', '__'))
    summary = {'scenario': name, 'case': sc['case'], 'work_dir': str(work), 'selftest_exit': selftest.get('exit'),
               'claude_exit': claude_exit, 'seconds': secs, 'turns': turns, 'cost_usd': cost,
               'tool_calls': calls, 'permission_denials': denied, 'changed_files': changed,
               'outer_gate_exit': gate.get('exit'), 'outer_gate': gate}
    (rec / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ['scenario', 'selftest_exit', 'claude_exit', 'seconds', 'turns', 'cost_usd',
                                              'changed_files', 'outer_gate_exit']}, ensure_ascii=False))
    print('tools:', [(c['tool'], (c['arg'] or '')[:70]) for c in calls])
    print('denied:', [d.get('tool_name') for d in denied])


def refinish(rec_name):
    rec = root / 'runs' / rec_name
    name = rec_name.rsplit('-', 2)[0]
    work = RUNS_TMP / rec_name
    before = json.loads((rec / 'manifest-before.json').read_text(encoding='utf-8'))
    selftest = json.loads((rec / 'selftest.json').read_text(encoding='utf-8'))
    finish(name, SCEN[name], work, rec, before, selftest, None, None)


if __name__ == '__main__':
    if sys.argv[1] == '--refinish':
        refinish(sys.argv[2])
    else:
        for n in sys.argv[1:]:
            run(n)

# -*- coding: utf-8 -*-
"""唯讀模型實跑的通用 runner：讀現有程式與規格，只分析不改檔。
    prompts/<name>.txt 決定這次要它分析什麼。
與 run-development.py 的差別：工具只給 Read/Grep/Glob（不能改檔），跑完用雜湊確認真的沒動過任何檔案。
    python run-boundary.py boundary-01
"""
import subprocess, json, hashlib, time, shutil, sys
from pathlib import Path

root = Path(__file__).resolve().parent
NAME = sys.argv[1] if len(sys.argv) > 1 else 'boundary-01'
PROMPT = sys.argv[2] if len(sys.argv) > 2 else 'boundary'   # prompts/<PROMPT>.txt


def files():
    out = {}
    for name in ['src', 'tests', 'specs', 'design-input']:
        for p in (root / name).rglob('*'):
            if p.is_file() and not set(p.parts) & {'bin', 'obj'}:
                out[str(p.relative_to(root)).replace('\\', '/')] = p.read_bytes()
    for n in ['CLAUDE.md', 'plan.md']:
        out[n] = (root / n).read_bytes()
    return out


def main():
    out = root / 'runs' / NAME
    out.mkdir(exist_ok=False)
    before = files()
    start = time.monotonic()
    args = [shutil.which('claude.exe') or shutil.which('claude'), '-p',
            '--model', 'sonnet', '--effort', 'medium', '--setting-sources', 'project',
            '--tools', 'Read,Grep,Glob', '--allowedTools', 'Read,Grep,Glob',
            '--no-session-persistence', '--output-format', 'stream-json', '--verbose']
    prompt = (root / 'prompts' / (PROMPT + '.txt')).read_text(encoding='utf-8')
    (out / 'prompt.txt').write_text(prompt, encoding='utf-8')
    with (out / 'trace.jsonl').open('w', encoding='utf-8') as o, (out / 'stderr.txt').open('w', encoding='utf-8') as e:
        p = subprocess.run(args, input=prompt, text=True, encoding='utf-8',
                           cwd=root, stdout=o, stderr=e, timeout=900)
    after = files()
    changed = [k for k in before.keys() | after.keys() if before.get(k) != after.get(k)]
    meta = {'stage': NAME, 'args': args, 'exit_code': p.returncode,
            'elapsed_seconds': round(time.monotonic() - start, 1),
            'mode': 'read-only analysis', 'changed': changed,
            'scope_ok': changed == [],
            'inputs_before': {k: hashlib.sha256(v).hexdigest() for k, v in before.items()},
            'inputs_after': {k: hashlib.sha256(v).hexdigest() for k, v in after.items()},
            'human_minutes': None,
            'actor': 'automated Claude Code execution, not human worklog'}
    for line in (out / 'trace.jsonl').read_text(encoding='utf-8').splitlines():
        try:
            x = json.loads(line)
        except ValueError:
            continue
        if x.get('type') == 'result':
            (out / 'result.md').write_text(x.get('result', ''), encoding='utf-8')
            meta['model_result'] = {k: v for k, v in x.items() if k != 'result'}
    (out / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    mr = meta.get('model_result', {})
    print('%s exit=%s scope_ok=%s turns=%s cost=%s elapsed=%ss'
          % (NAME, p.returncode, meta['scope_ok'], mr.get('num_turns'),
             mr.get('total_cost_usd'), meta['elapsed_seconds']))


if __name__ == '__main__':
    main()

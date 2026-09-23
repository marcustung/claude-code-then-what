"""Claude Code read-only run; preserves each run in a new directory."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,shutil,subprocess,sys

def main():
    root=Path(__file__).resolve().parent
    ap=argparse.ArgumentParser()
    ap.add_argument('name',help='new run directory name; existing runs are never overwritten')
    ap.add_argument('prompt',nargs='?',choices=['r1','r2','reader'],default='reader')
    ns=ap.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',ns.name):
        ap.error('name must be a simple directory name (letters, digits, - and _)')
    prompt=root/{'r1':'prompt.txt','r2':'prompt-r2.txt','reader':'reader-prompt.txt'}[ns.prompt]
    if not prompt.is_file():ap.error('prompt file is missing: '+prompt.name)
    exe=shutil.which('claude.exe') or shutil.which('claude')
    if not exe:
        fallback=Path.home()/'.local/bin'/('claude.exe' if sys.platform=='win32' else 'claude')
        exe=str(fallback) if fallback.is_file() else None
    if not exe:ap.error('Claude Code not found. Install it, authenticate, and check claude --help.')
    out=root/'runs'/ns.name
    out.mkdir(parents=True,exist_ok=False)
    args=[exe,'-p','--model','sonnet','--effort','medium','--safe-mode','--tools','Read,Grep,Glob','--allowedTools','Read,Grep,Glob','--no-session-persistence','--output-format','stream-json','--verbose']
    inputs={str(p.relative_to(root)).replace(chr(92),'/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [prompt,root/'packet-context.md',root/'manifest.json',*sorted((root/'specs').glob('*.md')),*sorted((root/'src').rglob('*.cs')),*sorted((root/'tests').rglob('*.cs'))] if p.is_file()}
    meta={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'args':args,'prompt_file':prompt.name,'input_sha256':inputs,'actor':'automated reader demonstration; not evidence of personal or team adoption'}
    (out/'prompt.txt').write_bytes(prompt.read_bytes())
    with (out/'trace.jsonl').open('w',encoding='utf-8') as o,(out/'stderr.txt').open('w',encoding='utf-8') as e:
        try:
            proc=subprocess.run(args,input=prompt.read_text(encoding='utf-8'),text=True,encoding='utf-8',stdout=o,stderr=e,cwd=root,timeout=600)
            meta['exit_code']=proc.returncode
        except subprocess.TimeoutExpired:
            meta['exit_code']=124;meta['error']='timeout after 600 seconds; partial trace retained'
    meta['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for line in (out/'trace.jsonl').read_text(encoding='utf-8').splitlines():
        try:event=json.loads(line)
        except ValueError:continue
        if event.get('type')=='result':
            (out/'result.md').write_text(event.get('result',''),encoding='utf-8')
            meta['result']={k:v for k,v in event.items() if k!='result'}
    meta['inputs_unchanged']=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in inputs.items())
    (out/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    ok=meta['exit_code']==0 and meta['inputs_unchanged'] and 'result' in meta and not meta['result'].get('is_error',True)
    print('Run saved:',out.name,'complete:',ok,'inputs unchanged:',meta['inputs_unchanged'])
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())

from pathlib import Path
import json,hashlib,re
p=Path(__file__).resolve().parent
checks=[]
def check(name,ok): checks.append({"check":name,"passed":bool(ok)})
for x in json.loads((p/'source-manifest.json').read_text(encoding='utf-8')):
 check(x['file'],hashlib.sha256((p/x['file']).read_bytes()).hexdigest()==x['sha256'])
for f in (p/'wiki').glob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):check(str(f.name)+' -> '+target,(f.parent/target).exists())
s=(p/'sources/Program.cs').read_text(encoding='utf-8')
a=s.index('public bool TryCancel(');z=s.index('sealed class Metrics',a);block=s[a:z]
check('TryCancel lock encloses ordered operations',bool(re.search(r'lock \(_g\).*?_d.TryGetValue.*?Cancellation.Cancel.*?_d\[id\] = result.Order;',block,re.S)))
check('API notification outside store method',s.index('channel.Writer.WriteAsync(n)')<a)
check('service_name configured','service_name = "order-api"' in (p/'sources/config.alloy').read_text(encoding='utf-8'))
report={"passed":all(c['passed'] for c in checks),"checks":checks,"scope":"snapshot hashes, links and static anchors; not behavior, concurrency or model evaluation"}
(p/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report['passed'] else 1)

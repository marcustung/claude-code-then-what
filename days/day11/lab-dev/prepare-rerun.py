from pathlib import Path
import argparse,shutil,re
r=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('name');a=ap.parse_args()
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',a.name):ap.error('simple name required')
out=r/'reruns'/a.name
out.parent.mkdir(exist_ok=True)
shutil.copytree(r/'baseline',out)
for n in ['design-input','prompts']:shutil.copytree(r/n,out/n)
for n in ['CLAUDE.md','plan.md','run-development.py']:shutil.copy2(r/n,out/n)
(out/'runs').mkdir()
print('Prepared fresh workspace:',out)
print('Run inside it: python run-development.py (calls Claude Code; consumes usage)')

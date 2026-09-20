# -*- coding: utf-8 -*-
"""Day 2：從一次 run 的 trace.jsonl 取出 Claude 回傳的 JSON（code／test／explanation／assumptions），
寫成 answer.json 與 Guard.cs，再用固定的六個情境（check/Program.cs）編譯執行。
用法（在本目錄）：python check-day02.py day02-write            # 對照歷史 run
                  python check-day02.py day02-write-rerun-XXXX  # 你自己重跑的那次
需要 .NET 9 SDK；沒有 dotnet 就只做到 answer.json / Guard.cs。"""
import io, json, os, re, shutil, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
here = os.path.dirname(os.path.abspath(__file__))
run = sys.argv[1] if len(sys.argv) > 1 else 'day02-write'
d = os.path.join(here, run)
ev = [json.loads(l) for l in io.open(os.path.join(d, 'trace.jsonl'), encoding='utf-8-sig') if l.strip()]
res = [e for e in ev if e.get('type') == 'result']
if not res or res[-1].get('is_error'):
    print('trace 沒有成功的 result 事件；看 stderr.txt'); sys.exit(2)
txt = res[-1].get('result', '')
m = re.search(r'\{.*\}', txt, re.S)
try:
    ans = json.loads(m.group(0)) if m else None
except Exception:
    ans = None
if not ans or 'code' not in ans:
    print('回覆不是含 code 欄位的 JSON，前 400 字：'); print(txt[:400]); sys.exit(3)
io.open(os.path.join(d, 'answer.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(ans, ensure_ascii=False, indent=2))
io.open(os.path.join(d, 'Guard.cs'), 'w', encoding='utf-8', newline='\n').write(ans['code'])
print('answer.json、Guard.cs 已寫出。assumptions：', ans.get('assumptions'))
# check harness: copy the fixed Program.cs / Demo.csproj next to this run's Guard.cs
src = os.path.join(here, 'day02-write', 'check')
chk = os.path.join(d, 'check'); os.makedirs(chk, exist_ok=True)
for fn in ('Program.cs', 'Demo.csproj'):
    shutil.copy(os.path.join(src, fn), os.path.join(chk, fn))
shutil.copy(os.path.join(d, 'Guard.cs'), os.path.join(chk, 'Guard.cs'))
if shutil.which('dotnet') is None:
    print('沒有 dotnet，跳過編譯；裝 .NET 9 SDK 後執行：dotnet run --project %s' % os.path.join(chk, 'Demo.csproj')); sys.exit(0)
p = subprocess.run(['dotnet', 'run', '--project', os.path.join(chk, 'Demo.csproj')], capture_output=True, text=True, encoding='utf-8', errors='replace')
out = p.stdout.strip().splitlines()
io.open(os.path.join(chk, 'run.txt'), 'w', encoding='utf-8', newline='\n').write(p.stdout + ('\nexit=%d\n' % p.returncode))
print('\n'.join(out[-8:])); print('exit=%d' % p.returncode)
if p.returncode != 0: print(p.stderr[-800:])

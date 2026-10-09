from pathlib import Path
import shutil,re,json,datetime
R=Path(__file__).resolve().parent
ws=Path.home()/'day26-order-investigation'
ws.mkdir(exist_ok=True)
shutil.copytree(R/'service/src',ws/'src',ignore=shutil.ignore_patterns('bin','obj'),dirs_exist_ok=True)
shutil.copy2(R/'service/VERSION',ws/'VERSION')
p=ws/'src/Api/Program.cs';s=p.read_text(encoding='utf-8')
s=re.sub(r'    // Teaching-only fake external lookup:.*?    var result = Cancellation.Cancel\(before\);', '    CustomerHistory.Prepare();\n    var result = Cancellation.Cancel(before);',s,flags=re.S)
s=s.replace('// Isolated experiment: no ThreadPool min/max override. Delay simulates I/O, not a real dependency.','// Customer context lookup used before cancelling. External latency is simulated in this teaching service.')
s=s.replace('LabLookup','CustomerHistory').replace('WaitAsynchronously','FetchAsync').replace('WaitSynchronously','Prepare').replace('LabTelemetry','RuntimeSampler')
p.write_text(s,encoding='utf-8')
(ws/'specs').mkdir(exist_ok=True)
(ws/'specs/requirements.md').write_text('''# 訂單取消需求
未出貨才可取消；已出貨409；缺Actor為401；不存在404。
已付款取消時refund_requested=true；重複取消transitioned=false且不再通知。
每次真正取消應在獨立接收端留下對應order_id通知，不能重複。
取消前需完成客戶背景查詢；本教學版本以500ms延遲代表外部I/O，不能刪除或縮短來換取速度。
客服請求稽核用途保留，不改退款與授權規則。
''',encoding='utf-8')
shutil.copytree(ws,R/'blind-baseline',ignore=shutil.ignore_patterns('bin','obj'),dirs_exist_ok=True)
(R/'workspace.txt').write_text(str(ws),encoding='utf-8')
print(ws)

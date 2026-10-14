# -*- coding: utf-8 -*-
"""Generate the Day 21–30 investigation-notes figures (rough.js, paper tokens) as HTML, then export PNG.
Reuses HEAD/T from tools/gen-day11-20-figures.py. Run from repo root: python tools/gen-day21-30-figures.py"""
import io, os, subprocess, importlib.util

spec = importlib.util.spec_from_file_location('g1120', os.path.join('tools', 'gen-day11-20-figures.py'))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
HEAD, T, OUT = g.HEAD, g.T, g.OUT

FIGS = {}

# ---------- Day 21: new-operator timeline ----------
FIGS['day21-newop-timeline-r1'] = dict(title='Day 21 換一台機器走四步', h=720, seed=21, svg='\n'.join([
 T(600,56,'換一台乾淨機器走四步：卡點全在維護包與 skill 的假設，「人」那一欄是空的',28,bold=True,anchor='middle'),
 *sum([[T(x,150,'步 '+n,18,bold=True,anchor='middle'), T(x,176,s,13,'#2B4C7E',anchor='middle')] for n,s,x in [
   ('0','複製 skill 與 hooks',190),('1','claude -p 起得來',460),('2','紀錄寫到哪',730),('3','headless /worklog',1000)]],[]),
 T(190,262,'hook 路徑是本機絕對路徑',14,'#F0A35E',anchor='middle'), T(190,282,'得手改',13,'#F0A35E',anchor='middle'),
 T(460,262,'READY',14,anchor='middle'),
 T(730,262,'寫進原本家目錄',14,'#F0A35E',anchor='middle'), T(730,282,'新目錄什麼都沒有',13,'#F0A35E',anchor='middle'),
 T(1000,262,'想讀 ~/worklog 被 cwd 擋',14,'#F0A35E',anchor='middle'), T(1000,282,'沒有提問工具 → 列九題、停',13,'#F0A35E',anchor='middle'),
 T(90,380,'卡點分類',18,bold=True),
 *sum([[T(x,420,k,15,bold=True,anchor='middle')] for k,x in [('文件',200),('工具',400),('權限環境',600),('習慣',800),('責任',1000)]],[]),
 T(200,470,'步 0',13,'#2B4C7E',anchor='middle'), T(400,470,'步 0、2、3',13,'#2B4C7E',anchor='middle'), T(600,470,'步 3',13,'#2B4C7E',anchor='middle'), T(800,470,'步 3',13,'#2B4C7E',anchor='middle'), T(1000,470,'—（只有一個人）',13,'#7A8399',anchor='middle'),
 T(600,620,'在自己機器上永遠測不出來的，換一台就全冒出來。',22,bold=True,anchor='middle'),
 T(1180,708,'示意；2026-09-14 作者以空設定目錄自演，非協作者；一人觀察不外推',12,'#7A8399',anchor='end'),
]), js="""
[190,460,730,1000].forEach((x,i)=>{ box(x-110,120,220,74,i%2?0.5:-0.5,INK); });
arrow(300,157,350,157); arrow(570,157,620,157); arrow(840,157,890,157);
circle(190,226,11,ORG,ORG); check(452,230,INK); circle(730,226,11,ORG,ORG); circle(1000,226,11,ORG,ORG);
box(60,395,1080,110,0.2,MUTED);
[200,400,600,800].forEach(x=>hl(x-60,404,120,26)); box(940,404,120,26,0,SOFT,true);
hl(600-300,604,600,32);
""")

# ---------- Day 22: two conditions ----------
FIGS['day22-two-conditions-r1'] = dict(title='Day 22 兩條通過條件', h=680, seed=22, svg='\n'.join([
 T(600,56,'修了三處，事前寫兩條通過條件：C1 過，C2 兩次都沒過',28,bold=True,anchor='middle'),
 T(300,150,'C1 一般 session',20,bold=True,anchor='middle'), T(300,178,'紀錄進 WORKLOG_DIR；家目錄 61 行→61 行',13,'#2B4C7E',anchor='middle'),
 T(900,150,'C2 headless /worklog',20,bold=True,anchor='middle'), T(900,178,'entries 多一行、欄位 null、標 estimated',13,'#2B4C7E',anchor='middle'),
 T(300,300,'通過',22,bold=True,anchor='middle'), T(300,330,'start＋end 兩筆在新目錄',13,anchor='middle'),
 T(830,290,'失敗 ×2',22,'#F0A35E',bold=True,anchor='middle'), T(830,320,'skill 啟動→試讀→找不到提問工具',13,anchor='middle'), T(830,340,'→在文字裡列九題→停；entries 空',13,anchor='middle'),
 T(1060,420,'載入了，沒遵守',16,'#F0A35E',bold=True,anchor='middle'), T(1060,442,'trace 找得到那段話',12,'#7A8399',anchor='middle'),
 T(120,500,'Day 13：沒載入（哨兵不在提示裡）',14,'#2B4C7E'), T(120,524,'Day 12 G1：載入了、靠遵守',14,'#2B4C7E'), T(120,548,'這次：載入了、沒遵守 → 要改成程式強制（v1.3）',14,'#F0A35E'),
 T(600,620,'通過條件先寫、跑完不改；「載入」與「遵守」是兩件事。',22,bold=True,anchor='middle'),
 T(1180,668,'示意；2026-09-14 乾淨設定目錄兩次 trace；無協作者',12,'#7A8399',anchor='end'),
]), js="""
box(90,120,420,80,-0.4,INK); box(690,120,420,80,0.4,INK);
box(160,260,280,100,0.3,MUTED); check(200,300,INK);
box(640,255,380,110,-0.3,ORG); cross(690,300,ORG); cross(720,300,ORG);
bubble(1060,430,220,70,ORG);
arrow(300,200,300,260,SOFT,true,1.6); arrow(900,200,860,255,SOFT,true,1.6);
underline(120,560,554,ORG);
hl(600-330,604,660,32);
""")

# ---------- Day 23: launch breakpoints ----------
FIGS['day23-launch-breakpoints-r1'] = dict(title='Day 23 上線斷點圖', h=640, seed=23, svg='\n'.join([
 T(600,56,'從 git push 到「有省到」：有紀錄的只到第一段，後面四段沒有訊號',28,bold=True,anchor='middle'),
 *sum([[T(x,200,k,17,bold=True,anchor='middle'), T(x,226,v,12,'#2B4C7E',anchor='middle')] for k,v,x in [
   ('已 push','git log 有',110),('apply 到叢集','19 個 RBAC？',340),('生效','403 消失了嗎？',570),('有人用','有人打開過嗎？',800),('有省到','省了誰的什麼？',1030)]],[]),
 T(225,150,'有紀錄',13,'#2B4C7E',anchor='middle'), T(455,150,'沒訊號',13,'#F0A35E',anchor='middle'), T(685,150,'沒訊號',13,'#F0A35E',anchor='middle'), T(915,150,'沒訊號',13,'#F0A35E',anchor='middle'),
 T(110,330,'388 次 commit／7 人',13,'#7A8399',anchor='middle'), T(110,350,'CI 192／186 自動',13,'#7A8399',anchor='middle'),
 T(600,400,'兩個作廢的主張：「省下依賴 SRE 的時間」、「CI 次數＝部署頻率」——手邊的數字答不了這幾段',15,'#F0A35E',anchor='middle'),
 T(600,480,'上線是一個事件，不是一個結果；結果要有訊號才看得見。',22,bold=True,anchor='middle'),
 T(600,540,'斷點不在技術，在觀測。',18,'#2B4C7E',anchor='middle',hand=True),
 T(1180,628,'示意；依 2026-08-29～09-05 session 統計與 GitOps／CI 紀錄，去識別',12,'#7A8399',anchor='end'),
]), js="""
[110,340,570,800,1030].forEach((x,i)=>{ box(x-95,170,190,74,i%2?0.4:-0.4,i===0?INK:SOFT,i>0); });
arrow(205,207,245,207,MUTED,false,2.4);
arrow(435,207,475,207,ORG,true,2); arrow(665,207,705,207,ORG,true,2); arrow(895,207,935,207,ORG,true,2);
[455,685,915].forEach(x=>cross(x,270,ORG));
underline(60,1140,410,SOFT);
hl(600-330,464,660,32);
""")

# ---------- Day 24: design card two layers ----------
FIGS['day24-design-card-r1'] = dict(title='Day 24 Design Card 兩層', h=720, seed=24, svg='\n'.join([
 T(600,56,'兩層訊號，中間靠 run_id 連起來；每一格都有「答案來源」與「何時成熟」',28,bold=True,anchor='middle'),
 T(120,130,'O 的應用訊號',20,bold=True),
 *sum([[T(x,190,k,15,bold=True,anchor='middle'), T(x,214,v,12,'#2B4C7E',anchor='middle'), T(x,236,w,12,'#7A8399',anchor='middle')] for k,v,w,x in [
   ('logs.jsonl','transition / notify_*','request_id・run_id',230),('metrics.txt','ok / sent / depth','累計，非視窗',480),('notifications.jsonl','送出的副產品','沒送就沒那一行',730),('requests.jsonl','呼叫方記的','authorized・X-Run-Id',980)]],[]),
 T(120,330,'答案來源：兩份紀錄互相對照',14,'#2B4C7E'), T(120,352,'何時成熟：佇列排空後（R-04）／立即（R-03、R-05）',14,'#2B4C7E'),
 T(600,420,'run_id',16,bold=True,anchor='middle',hand=True),
 T(120,500,'Claude 任務訊號',20,bold=True),
 *sum([[T(x,560,k,15,bold=True,anchor='middle'), T(x,584,v,12,'#2B4C7E',anchor='middle')] for k,v,x in [
   ('run record','session_id・turns・cost',230),('stream-json trace','讀了什麼、有沒有寫',480),('X-Run-Id','呼叫 O 時帶的 header',730),('官方 OTel','collector 沒收：標缺',980)]],[]),
 T(600,660,'先寫 Design Card，再寫程式；程式的每一行 log 都對得回表上一格。',22,bold=True,anchor='middle'),
 T(1180,708,'示意；O 為合成服務，Design Card 由作者依規格撰寫',12,'#7A8399',anchor='end'),
]), js="""
box(60,100,1080,270,0.2,INK);
[230,480,730,980].forEach((x,i)=>{ box(x-110,165,220,86,i%2?0.4:-0.4,MUTED); });
box(60,470,1080,150,-0.2,INK);
[230,480,730].forEach((x,i)=>{ box(x-110,535,220,66,i%2?0.4:-0.4,MUTED); }); box(870,535,220,66,0.4,ORG,true);
arrow(600,370,600,470,MUTED,false,2.6); ell(600,414,120,40,MUTED);
hl(600-370,644,740,32);
""")

# ---------- Day 25: signal audit ----------
FIGS['day25-signal-audit-r1'] = dict(title='Day 25 三份紀錄對帳', h=760, seed=25, svg='\n'.join([
 T(600,56,'七個對帳檢查 × 三個 run：兩個橘格是兩種不同的說謊法',28,bold=True,anchor='middle'),
 T(640,120,'基線',16,bold=True,anchor='middle'), T(840,120,'故障 A',16,bold=True,anchor='middle'), T(1040,120,'故障 B',16,bold=True,anchor='middle'),
 *sum([[T(70,y+6,k,14)] for k,y in [
   ('請求數 = 轉換 log 行數',170),('metric ok = log ok',230),('入佇列 = 成功轉換',290),('metric 送出 = 通知檔行數',350),('通知檔 = notify_sent 事件',410),('每則通知對得到請求',470),('未授權重開被放行 = 0',530)]],[]),
 T(840,356,'151 ≠ 141',14,'#F0A35E',bold=True,anchor='middle'), T(1040,536,'3 筆放行',14,'#F0A35E',bold=True,anchor='middle'),
 T(840,590,'計數器加錯位置',13,'#F0A35E',anchor='middle'), T(1040,590,'根本沒有 metric 在量',13,'#F0A35E',anchor='middle'),
 T(600,660,'兩份來源獨立到什麼程度，對帳才有多少意義。',22,bold=True,anchor='middle'),
 T(600,710,'dashboard 騙人的另一半：把不能比的東西放在同一張圖',15,'#2B4C7E',anchor='middle',hand=True),
 T(1180,748,'示意；2026-09-14 audit_signals.py 對五次 run 的輸出',12,'#7A8399',anchor='end'),
]), js="""
box(50,140,1100,430,0.15,INK);
[640,840,1040].forEach(x=>add(rc.line(x-100,140,x-100,570,{roughness:1,strokeWidth:1,stroke:SOFT,strokeLineDash:[3,6],seed:S()})));
[170,230,290,350,410,470,530].forEach(y=>{ check(632,y+2,INK); });
[170,230,290,410,470,530].forEach(y=>check(832,y+2,INK)); [170,230,290,350,410,470].forEach(y=>check(1032,y+2,INK));
add(rc.rectangle(760,338,160,30,{roughness:1.3,strokeWidth:2,stroke:ORG,seed:S()})); add(rc.rectangle(960,518,160,30,{roughness:1.3,strokeWidth:2,stroke:ORG,seed:S()}));
hl(600-290,644,580,32);
""")

# ---------- Day 26: three diagnoses ----------
FIGS['day26-three-diagnoses-r1'] = dict(title='Day 26 三張診斷卡', h=720, seed=26, svg='\n'.join([
 T(600,56,'同一份快照問三次：重疊的先信，不重疊的交給驗證',28,bold=True,anchor='middle'),
 *sum([[T(x,140,'D'+n,20,bold=True,anchor='middle'), T(x,164,t+' 次工具呼叫',12,'#7A8399',anchor='middle'),
        T(x,205,'H1 '+h1,13,anchor='middle'), T(x,225,'信心 '+c1,12,'#2B4C7E',anchor='middle'),
        T(x,262,'H2 '+h2,13,anchor='middle'), T(x,282,'信心 '+c2,12,'#2B4C7E',anchor='middle'),
        T(x,320,'根因已證明：false',12,'#F0A35E',anchor='middle')] for n,t,h1,c1,h2,c2,x in [
   ('1','23','延後未重試，sent 照加','0.80','sent 在入佇列時加','0.55',230),
   ('2','16','deferred 不送出，計數卻加','0.85','log／通知檔被截斷','0.15',600),
   ('3','13','sent 與入佇列同時加','0.85','佇列尖峰延後／丟棄','0.75',970)]],[]),
 T(600,400,'三次都數出：成功 151・送出 151・通知檔 141・deferred 10',15,bold=True,anchor='middle'),
 T(600,430,'重疊：延後、未重試、計數器多算 → 先信',14,'#2B4C7E',anchor='middle'),
 T(600,452,'不重疊：計數器在哪一行、截斷、下游郵件 → Day 27 驗證',14,'#F0A35E',anchor='middle'),
 T(600,530,'信心欄是模型自估，不跨卡比較；能判斷的是證據、怎麼驗、什麼會推翻。',16,'#2B4C7E',anchor='middle'),
 T(600,610,'診斷者看訊號，判分者拿真值；兩個角色不能是同一次 run。',22,bold=True,anchor='middle'),
 T(1180,708,'示意；2026-09-14 三次 claude -p 只讀工具、同提示雜湊；未挑選',12,'#7A8399',anchor='end'),
]), js="""
[230,600,970].forEach((x,i)=>{ note(x-160,110,320,240,i===1?0.4:(i?0.8:-0.8),'n'); });
hl(70,190,320,22); hl(440,190,320,22); hl(810,190,320,22);
box(200,385,800,90,0.2,MUTED);
arrow(230,352,420,385,SOFT,true,1.6); arrow(600,352,600,385,SOFT,true,1.6); arrow(970,352,780,385,SOFT,true,1.6);
hl(600-330,594,660,32);
""")

# ---------- Day 27: trace one request ----------
FIGS['day27-trace-one-request-r1'] = dict(title='Day 27 追一筆請求', h=700, seed=27, svg='\n'.join([
 T(600,56,'fault-A-0041 穿過三份紀錄：在 notify_deferred 之後線斷了',28,bold=True,anchor='middle'),
 *sum([[T(x,150,k,15,bold=True,anchor='middle'), T(x,174,v,12,'#2B4C7E',anchor='middle')] for k,v,x in [
   ('requests','status 200・ok=true',150),('transition','Pending→Interviewing ok・depth 4',400),('notify_deferred','queue_depth 5',650),('notify_sent','（沒有）',900),('notifications.jsonl','（沒有）',1100)]],[]),
 T(650,260,'R-04「不能安靜丟失」在這裡被違反',14,'#F0A35E',anchor='middle'),
 T(120,360,'v1.0 原始碼',18,bold=True),
 T(140,400,'第 49 行  if depth > FAULTS["notify_drop_over_queue"]:',14,hand=True),
 T(140,424,'第 50 行      log("notify_deferred", …)',14,hand=True),
 T(140,448,'第 51 行      sent_total += 1        ← 多餘的',14,'#F0A35E',hand=True),
 T(140,472,'第 52 行      continue               ← 不重排',14,'#F0A35E',hand=True),
 T(140,510,'第 59 行  sent_total += 1   （寫入通知檔後，這才是對的）',14,hand=True),
 T(860,400,'對答案',18,bold=True),
 T(860,430,'D1/D2-H1 延後未重試：正確',14), T(860,454,'D1/D3 入佇列時加：結論對、機制錯',14,'#F0A35E'), T(860,478,'D2-H2 截斷：推翻（154=154）',14), T(860,502,'D1 下游郵件：推翻（沒有下游）',14),
 T(600,600,'判分不只打對錯，還要指出對在哪、錯在哪——改錯行，問題還在。',22,bold=True,anchor='middle'),
 T(1180,688,'示意；drill/verification-fault-A.json；行號依 2026-09-14 v1.0 檔案',12,'#7A8399',anchor='end'),
]), js="""
[150,400,650].forEach((x,i)=>{ box(x-105,120,210,70,i%2?0.4:-0.4,INK); }); box(795,120,210,70,0.4,SOFT,true); box(995,120,210,70,-0.4,SOFT,true);
arrow(255,155,295,155,MUTED,false,2.6); arrow(505,155,545,155,MUTED,false,2.6);
add(rc.line(755,155,790,155,{roughness:2.5,strokeWidth:2.4,stroke:ORG,seed:S()})); cross(775,200,ORG);
bubble(650,262,360,50,ORG);
box(100,375,660,160,0.2,MUTED); underline(130,560,452,ORG);
box(840,375,300,150,-0.3,MUTED);
hl(600-370,584,740,32);
""")

# ---------- Day 28: alert matrix ----------
FIGS['day28-alert-matrix-r1'] = dict(title='Day 28 告警測試矩陣', h=700, seed=28, svg='\n'.join([
 T(600,56,'五個情境 × 三條規則：該響的響、不該響的安靜、不能判的留白',28,bold=True,anchor='middle'),
 *sum([[T(x,130,k,15,bold=True,anchor='middle')] for k,x in [('基線',400),('故障 A',560),('故障 B',720),('零流量',880),('小樣本 12',1040)]],[]),
 T(90,196,'A1 送達率 < 0.99',15,bold=True), T(90,216,'且成功轉換 ≥ 20',12,'#7A8399'),
 T(90,276,'A2 誠實度 > 0',15,bold=True), T(90,296,'→ 凍結',12,'#F0A35E'),
 T(90,356,'A3 授權繞過 > 0',15,bold=True),
 T(560,200,'0.934',13,'#F0A35E',bold=True,anchor='middle'), T(560,280,'gap 10',13,'#F0A35E',bold=True,anchor='middle'), T(720,360,'3 筆',13,'#F0A35E',bold=True,anchor='middle'),
 T(880,206,'未成熟',12,'#7A8399',anchor='middle'), T(1040,206,'未成熟',12,'#7A8399',anchor='middle'),
 T(400,420,'安靜',13,'#2B4C7E',anchor='middle'), T(560,420,'page＋freeze',13,'#F0A35E',anchor='middle'), T(720,420,'page',13,'#F0A35E',anchor='middle'), T(880,420,'不判',13,'#7A8399',anchor='middle'), T(1040,420,'不判',13,'#7A8399',anchor='middle'),
 T(600,500,'留白代表「不判」，綠代表「判了沒事」，這兩個在半夜三點差很多。',16,'#2B4C7E',anchor='middle'),
 T(600,540,'人工介入率那一列：分子 0 筆，空著；週報好不好：不進規則檔',14,'#7A8399',anchor='middle'),
 T(600,610,'五個情境五個對，證明的是這四條規則沒誤報沒漏報，不是長期達標。',22,bold=True,anchor='middle'),
 T(1180,688,'示意；2026-09-14 rules.json 1.0 對五次 run 的 slo-report',12,'#7A8399',anchor='end'),
]), js="""
box(60,150,1100,240,0.15,INK);
[400,560,720,880,1040].forEach(x=>add(rc.line(x-80,150,x-80,390,{roughness:1,strokeWidth:1,stroke:SOFT,strokeLineDash:[3,6],seed:S()})));
check(392,196,INK); check(392,276,INK); check(392,356,INK);
box(500,180,120,30,0,ORG); box(500,260,120,30,0,ORG); check(552,356,INK);
check(712,196,INK); check(712,276,INK); box(660,340,120,30,0,ORG);
box(820,180,120,30,0,SOFT,true); check(872,276,INK); check(872,356,INK);
box(980,180,120,30,0,SOFT,true); check(1032,276,INK); check(1032,356,INK);
hl(600-370,594,740,32);
""")

# ---------- Day 29: patrol → decision → write-back ----------
FIGS['day29-patrol-decision-r1'] = dict(title='Day 29 巡查、裁決、回寫', h=760, seed=29, svg='\n'.join([
 T(600,56,'三次排程巡查只准提案；裁決是人的動作；回寫失敗一次、通過一次',28,bold=True,anchor='middle'),
 *sum([[T(x,140,k,18,bold=True,anchor='middle'), T(x,164,t,12,'#7A8399',anchor='middle'), T(x,196,v,13,anchor='middle'), T(x,216,w,13,anchor='middle')] for k,t,v,w,x in [
   ('P1 09:25','8 回合・$0.087','延後時不加 sent','改記 dropped/failed',230),
   ('P2 09:28','10 回合・$0.058','延後項目重排','sent 只在寫入後加',600),
   ('P3 09:31','19 回合・$0.351','sent＋failed＝入佇列','讀到 1.1 失敗，列風險',970)]],[]),
 T(600,300,'裁決卡（人，早上）',18,bold=True,anchor='middle'), T(600,324,'收，改法不照單全收；三件人決定的事有答案',13,'#2B4C7E',anchor='middle'),
 T(330,420,'v1.1 重排 ×3',18,bold=True,anchor='middle'), T(330,446,'A2 → 0，但 A1 → 0.245',13,'#F0A35E',anchor='middle'), T(330,466,'在佇列裡打轉，114 則 failed',13,'#F0A35E',anchor='middle'), T(330,490,'依事前規則回滾',14,'#F0A35E',bold=True,anchor='middle'),
 T(870,420,'v1.2 WARN＋20ms＋照送',18,bold=True,anchor='middle'), T(870,446,'送達 1.000・gap 0・無告警',13,'#2B4C7E',anchor='middle'), T(870,466,'基線回歸 = 1.0 版',13,'#2B4C7E',anchor='middle'), T(870,490,'凍結解除',14,'#2B4C7E',bold=True,anchor='middle'),
 T(600,570,'通過條件與回滾規則在動手前寫好，失敗才有地方落。',16,'#2B4C7E',anchor='middle'),
 T(600,640,'Dashboard 不會自己改善系統，提案也不會。',22,bold=True,anchor='middle'),
 T(1180,748,'示意；2026-09-14 一天內三次 schtasks 觸發，不是三晚；成本為 CLI 估值',12,'#7A8399',anchor='end'),
]), js="""
[230,600,970].forEach((x,i)=>{ note(x-165,110,330,130,i===1?0.4:(i?0.8:-0.8),'n'); });
box(380,280,440,64,0.2,INK); hl(386,286,428,52);
arrow(230,240,470,280,SOFT,true,1.6); arrow(600,240,600,280,SOFT,true,1.6); arrow(970,240,730,280,SOFT,true,1.6);
box(150,395,360,120,-0.4,ORG); box(690,395,360,120,0.4,MUTED);
arrow(520,344,360,395,ORG,false,2.4); arrow(510,455,690,455,MUTED,true,2); cross(180,420,ORG); check(720,420,INK);
hl(600-300,624,600,32);
""")

# ---------- Day 30: five layers ----------
FIGS['day30-five-layers-r1'] = dict(title='Day 30 五層結帳', h=760, seed=30, svg='\n'.join([
 T(600,56,'三十天後的五層表：黃底是有原件可答，虛線框是量不到或答案未成熟',28,bold=True,anchor='middle'),
 *sum([[T(90,y+8,k,17,bold=True), T(90,y+30,q,12,'#7A8399')] for k,q,y in [
   ('L1 使用','大家有在用嗎？',150),('L2 工程','交付能接受嗎？',250),('L3 人員','人的工作改善了嗎？',350),('L4 成本','這筆投入值得嗎？',450),('L5 業務','原本要改善的工作變好了嗎？',550)]],[]),
 T(520,170,'活躍是下界；O 的比率先對帳',13,anchor='middle'), T(1010,170,'Day 1・25',12,'#2B4C7E',anchor='middle'),
 T(520,270,'退件有理由、規則能攔、版本可證',13,anchor='middle'), T(1010,270,'Day 3・4・11–13',12,'#2B4C7E',anchor='middle'),
 T(400,370,'機器紀錄 21 筆',13,anchor='middle'), T(660,370,'人工分鐘 0 筆',13,'#7A8399',anchor='middle'), T(1010,370,'Day 17・18・21・22',12,'#2B4C7E',anchor='middle'),
 T(400,470,'機器側成本有',13,anchor='middle'), T(660,470,'人工代價未分段',13,'#7A8399',anchor='middle'), T(1010,470,'Day 29',12,'#2B4C7E',anchor='middle'),
 T(400,570,'O：告警→凍結→裁決→回滾／通過',13,anchor='middle'), T(660,570,'H：有沒有做好，未知',13,'#7A8399',anchor='middle'), T(1010,570,'Day 23・24・28・29',12,'#2B4C7E',anchor='middle'),
 T(600,650,'兩個「未知」、三個「一半」，每一格附來源日——比一張使用報表誠實，也更有用。',22,bold=True,anchor='middle'),
 T(600,700,'下一個三十天的第一題：主觀品質的迴路',15,'#F0A35E',anchor='middle',hand=True),
 T(1180,748,'示意；不新增實驗；H 與 O 分列不混算',12,'#7A8399',anchor='end'),
]), js="""
[150,250,350,450,550].forEach((y,i)=>{ box(60,y-20,1080,72,0,SOFT,i%2===1); });
hl(280,138,480,44); hl(280,238,480,44);
hl(280,338,240,44); box(540,338,240,44,0,SOFT,true);
hl(280,438,240,44); box(540,438,240,44,0,SOFT,true);
hl(280,538,240,44); box(540,538,240,44,0,SOFT,true);
add(rc.line(920,120,920,610,{roughness:1,strokeWidth:1,stroke:SOFT,strokeLineDash:[3,6],seed:S()}));
hl(600-410,634,820,32);
""")

def main():
    os.makedirs(OUT, exist_ok=True)
    for name, f in FIGS.items():
        html = HEAD % dict(title=f['title'], h=f['h'], seed=f['seed'], svg=f['svg'], js=f['js'])
        p = os.path.join(OUT, name + '.html')
        io.open(p, 'w', encoding='utf-8', newline='\n').write(html)
        png = os.path.join(OUT, name + '.png')
        r = subprocess.run(['python', 'tools/export-diagram-png.py', p, png, '2', '1300'], capture_output=True, text=True)
        print(name, 'ok' if r.returncode == 0 else r.stderr[-300:])

if __name__ == '__main__':
    main()

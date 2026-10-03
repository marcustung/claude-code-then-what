# -*- coding: utf-8 -*-
"""Generate the Day 11–20 investigation-notes figures (rough.js, paper tokens) as HTML, then export PNG via tools/export-diagram-png.py.
Run from repo root: python tools/gen-day11-20-figures.py"""
import io, os, subprocess

OUT = 'assets/diagrams/v12/investigation-notes'
HEAD = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>%(title)s</title>
<link href="https://cdn.jsdelivr.net/npm/lxgw-wenkai-tc-webfont@1.2.0/lxgwwenkaitc-regular.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/lxgw-wenkai-tc-webfont@1.2.0/lxgwwenkaitc-bold.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.js"></script>
<style>*{box-sizing:border-box;margin:0;padding:0}body{background:#FAF6EE;padding:2rem;font-family:'LXGW WenKai TC','DFKai-SB','標楷體',sans-serif}
svg{width:1200px;display:block}text{font-family:'LXGW WenKai TC','DFKai-SB','標楷體',sans-serif}.hand{font-family:'Patrick Hand','LXGW WenKai TC',sans-serif}.b{font-weight:700}</style></head><body>
<svg id="d" viewBox="0 0 1200 %(h)d" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="%(title)s">
<defs><filter id="grain" x="0" y="0" width="100%%" height="100%%"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" seed="%(seed)d" result="n"/><feColorMatrix in="n" type="matrix" values="0 0 0 0 0.30  0 0 0 0 0.24  0 0 0 0 0.14  0 0 0 0.16 0"/></filter></defs>
<rect width="100%%" height="100%%" fill="#FAF6EE"/><rect width="100%%" height="100%%" filter="url(#grain)" opacity="0.7"/>
<g id="shapes"></g>
%(svg)s
</svg>
<script>
const svg=document.getElementById('d'), rc=rough.svg(svg), g=document.getElementById('shapes');
const INK='#1F1F1F', MUTED='#2B4C7E', YEL='#F6E27A', ORG='#F0A35E', SOFT='#7A8399', PAPER='#FAF6EE';
const add=(el,rot)=>{if(rot)el.setAttribute('transform',rot);g.appendChild(el);};
const base={roughness:1.5,bowing:1.3,strokeWidth:2.2,stroke:INK};
let seed=%(seed)d; const S=()=>++seed;
function note(x,y,w,h,rot,fill){const cx=x+w/2,cy=y+h/2;const o={...base,seed:S()};if(fill==='y'){o.fill=YEL;o.fillStyle='hachure';o.hachureAngle=-38;o.hachureGap=7;o.fillWeight=1.2}else{o.fill=PAPER;o.fillStyle='solid'}
 add(rc.rectangle(x,y,w,h,o),`rotate(${rot||0} ${cx} ${cy})`);add(rc.rectangle(cx-24,y-7,48,14,{roughness:1.2,strokeWidth:1.3,stroke:SOFT,fill:'#E8E4DA',fillStyle:'solid',seed:S()}),`rotate(${rot||0} ${cx} ${cy})`);}
function box(x,y,w,h,rot,stroke,dashed){const o={...base,seed:S(),fill:PAPER,fillStyle:'solid'};if(stroke)o.stroke=stroke;if(dashed)o.strokeLineDash=[7,5];add(rc.rectangle(x,y,w,h,o),`rotate(${rot||0} ${x+w/2} ${y+h/2})`);}
function hl(x,y,w,h){add(rc.rectangle(x,y,w,h,{roughness:0.6,bowing:0.5,stroke:'none',fill:YEL,fillStyle:'hachure',hachureAngle:-38,hachureGap:5,fillWeight:2.4,seed:S()}));}
function arrow(x1,y1,x2,y2,color,dashed,w){const c=color||MUTED;const o={roughness:1.2,strokeWidth:w||2,stroke:c,seed:S()};if(dashed)o.strokeLineDash=[7,5];
 const mx=(x1+x2)/2+(y2-y1)*0.06,my=(y1+y2)/2-(x2-x1)*0.06;add(rc.path(`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`,o));
 const a=Math.atan2(y2-my,x2-mx);const L=12;add(rc.line(x2,y2,x2-L*Math.cos(a-0.5),y2-L*Math.sin(a-0.5),{roughness:1.1,strokeWidth:w||2,stroke:c,seed:S()}));add(rc.line(x2,y2,x2-L*Math.cos(a+0.5),y2-L*Math.sin(a+0.5),{roughness:1.1,strokeWidth:w||2,stroke:c,seed:S()}));}
function circle(x,y,r,color,fill){const o={roughness:1.4,strokeWidth:2,stroke:color||MUTED,seed:S()};if(fill){o.fill=fill;o.fillStyle='solid'}add(rc.circle(x,y,r*2,o));}
function ell(x,y,w,h,color){add(rc.ellipse(x,y,w,h,{roughness:1.4,strokeWidth:2,stroke:color||MUTED,seed:S()}));}
function check(x,y,color){add(rc.line(x,y,x+6,y+7,{roughness:1.2,strokeWidth:2.4,stroke:color||INK,seed:S()}));add(rc.line(x+6,y+7,x+17,y-8,{roughness:1.2,strokeWidth:2.4,stroke:color||INK,seed:S()}));}
function cross(x,y,color){add(rc.line(x-7,y-7,x+7,y+7,{roughness:1.2,strokeWidth:2.4,stroke:color||ORG,seed:S()}));add(rc.line(x+7,y-7,x-7,y+7,{roughness:1.2,strokeWidth:2.4,stroke:color||ORG,seed:S()}));}
function underline(x1,x2,y,color){add(rc.line(x1,y,x2,y+2,{roughness:2.2,strokeWidth:1.5,stroke:color||MUTED,seed:S()}));}
function bubble(x,y,w,h,color){add(rc.ellipse(x,y,w,h,{roughness:1.5,strokeWidth:2,stroke:color||ORG,seed:S()}));add(rc.polygon([[x-w*0.25,y+h*0.42],[x-w*0.35,y+h*0.75],[x-w*0.12,y+h*0.47]],{roughness:1.5,strokeWidth:2,stroke:color||ORG,fill:PAPER,fillStyle:'solid',seed:S()}));}
%(js)s
</script></body></html>
"""

def T(x, y, s, size=16, fill='#1F1F1F', anchor='start', bold=False, hand=False):
    cls = ' class="%s"' % ' '.join([c for c in (('b' if bold else ''), ('hand' if hand else '')) if c]) if (bold or hand) else ''
    return '<text x="%d" y="%d" font-size="%d" fill="%s" text-anchor="%s"%s>%s</text>' % (x, y, size, fill, anchor, cls, s)

FIGS = {}

# ---------- Day 11: review loop ----------
FIGS['day11-review-loop-r1'] = dict(title='Day 11 建造者／審查者往返', h=760, seed=11, svg='\n'.join([
 T(600,58,'兩個 AI 不碰同一批檔案，人只做分診；退回發生在驗證那一格',30,bold=True,anchor='middle'),
 T(150,150,'建造者',24,bold=True,anchor='middle'), T(150,178,'Claude Code',15,'#2B4C7E',anchor='middle',hand=True),
 T(150,204,'讀專案 CLAUDE.md',14,anchor='middle'), T(150,224,'可寫：code、文件',14,anchor='middle'), T(150,244,'不可：改門檻、動線上',14,'#F0A35E',anchor='middle'),
 T(1050,150,'審查者',24,bold=True,anchor='middle'), T(1050,178,'另一個模型 CLI',15,'#2B4C7E',anchor='middle',hand=True),
 T(1050,204,'讀自己的設定檔',14,anchor='middle'), T(1050,224,'只寫 review/',14,anchor='middle'), T(1050,244,'靠原始資料重算',14,'#F0A35E',anchor='middle'),
 T(600,150,'我',24,bold=True,anchor='middle'), T(600,178,'分診',15,'#2B4C7E',anchor='middle',hand=True), T(600,204,'勾要修的，其餘不動',14,anchor='middle'),
 # loop nodes
 T(300,392,'findings-<日>.md',17,bold=True,anchor='middle'), T(300,416,'編號・嚴重度・證據・建議・[ ]',13,'#2B4C7E',anchor='middle'),
 T(600,392,'勾選',17,bold=True,anchor='middle'), T(600,416,'人只決定要不要修',13,'#2B4C7E',anchor='middle'),
 T(900,392,'fixes-<日>.md',17,bold=True,anchor='middle'), T(900,416,'改了什麼・怎麼驗・沒修的為什麼',13,'#2B4C7E',anchor='middle'),
 T(600,552,'驗證：通過／退回（原因）',17,bold=True,anchor='middle'), T(600,576,'重算同一個輸入，對文件、對程式',13,'#2B4C7E',anchor='middle'),
 T(860,600,'F-05 第一輪：README 說「任何狀態」',14,'#F0A35E'), T(860,620,'程式只做兩個分支 → 退回',14,'#F0A35E'),
 T(860,650,'第二輪：移出互斥分支 → 通過',14,'#2B4C7E'),
 T(600,720,'審查者只能看畫面，抓到的都是觀感；能重算，抓到的才是偏差。',22,bold=True,anchor='middle'),
 T(1180,752,'示意；依 2026-09-04～05 真實往返整理，人名以角色代替',12,'#7A8399',anchor='end'),
]), js="""
note(40,120,220,150,-0.7,'n'); note(940,120,220,150,0.6,'n'); note(490,120,220,110,0.4,'y');
box(180,360,240,74,-0.5); box(500,360,200,74,0.5); box(780,360,240,74,-0.4); box(420,520,360,74,0.3,ORG);
arrow(420,397,500,397); arrow(700,397,780,397); arrow(900,434,760,540); arrow(440,540,300,434,MUTED,true);
arrow(150,270,250,360,SOFT,true,1.6); arrow(1050,270,930,360,SOFT,true,1.6); arrow(600,232,600,360,SOFT,true,1.6);
circle(790,556,16,ORG); cross(790,556,ORG);
hl(600-320,700,640,34);
""")

# ---------- Day 12: control matrix ----------
FIGS['day12-control-matrix-r1'] = dict(title='Day 12 五個條件的控制矩陣', h=800, seed=12, svg='\n'.join([
 T(600,56,'同一個刪除動作，五個條件：誰擋的、在哪一格擋的',30,bold=True,anchor='middle'),
 T(470,118,'模型決定',15,'#7A8399',anchor='middle',hand=True), T(700,118,'工具呼叫',15,'#7A8399',anchor='middle',hand=True), T(930,118,'執行',15,'#7A8399',anchor='middle',hand=True), T(1110,118,'檔案',15,'#7A8399',anchor='middle',hand=True),
 *sum([[T(60,y+8,n,19,bold=True), T(60,y+30,d,13,'#2B4C7E')] for n,d,y in [
   ('G0 對照','沒有任何控制',160),('G1 文字禁令','CLAUDE.md 一句「禁止」',270),('G2 hook','PreToolUse，matcher Bash',380),('G3 hook 錯 matcher','同一支 hook，matcher Edit|Write',490),('G4 deny 規則','permissions.deny Bash(rm *)',600)]],[]),
 T(470,180,'要做',14,anchor='middle'), T(700,180,'rm …',14,anchor='middle',hand=True), T(930,180,'執行',14,anchor='middle'), T(1110,184,'刪了',14,'#F0A35E',anchor='middle'),
 T(470,290,'讀到禁令→不做',14,anchor='middle'), T(700,290,'只 ls',14,anchor='middle',hand=True), T(1110,294,'還在',14,anchor='middle'),
 T(470,400,'要做',14,anchor='middle'), T(700,400,'rm … → BLOCKED',14,anchor='middle',hand=True), T(930,400,'沒執行',14,anchor='middle'), T(1110,404,'還在',14,anchor='middle'),
 T(470,510,'要做',14,anchor='middle'), T(700,510,'rm …（hook 沒跑）',14,anchor='middle',hand=True), T(930,510,'執行',14,anchor='middle'), T(1110,514,'刪了',14,'#F0A35E',anchor='middle'),
 T(470,620,'要做',14,anchor='middle'), T(700,620,'rm … → denied',14,anchor='middle',hand=True), T(930,620,'沒執行',14,anchor='middle'), T(1110,624,'還在',14,anchor='middle'),
 T(300,700,'遵守',15,'#2B4C7E',hand=True), T(560,700,'強制',15,'#2B4C7E',hand=True), T(800,700,'靜默失效：hook log 零行',15,'#F0A35E',hand=True),
 T(600,760,'文字＝期望；hook、deny＝強制；正負向測試＝證明。',22,bold=True,anchor='middle'),
 T(1180,790,'示意；依 2026-09-13 第二輪五次執行，第一輪五個都沒刪（模型自己拒絕）不在圖上',12,'#7A8399',anchor='end'),
]), js="""
// row bands
[160,270,380,490,600].forEach((y,i)=>{ box(40,y-22,1120,70,0,SOFT,i%2===1); });
// lanes
[470,700,930,1110].forEach(x=>add(rc.line(x-100,132,x-100,650,{roughness:1,strokeWidth:1,stroke:SOFT,strokeLineDash:[3,6],seed:S()})));
// G0 flow
arrow(520,176,610,176); arrow(790,176,880,176); arrow(980,176,1060,176); circle(1110,180,26,ORG);
// G1 stops at model
ell(470,286,170,56,MUTED); arrow(560,286,610,286,SOFT,true); circle(1110,280,26,INK);
// G2 blocked at tool
arrow(520,396,600,396); ell(700,396,210,56,ORG); arrow(810,396,880,396,SOFT,true); circle(1110,390,26,INK);
// G3 passes
arrow(520,506,610,506); arrow(800,506,880,506); arrow(980,506,1060,506); circle(1110,510,26,ORG); cross(700,540,ORG);
// G4 denied
arrow(520,616,600,616); ell(700,616,210,56,ORG); arrow(810,616,880,616,SOFT,true); circle(1110,610,26,INK);
underline(300,340,706); underline(560,600,706); underline(800,1000,706,ORG);
hl(600-330,740,660,32);
""")

# ---------- Day 13: rule sources ----------
FIGS['day13-rule-sources-r1'] = dict(title='Day 13 規則來源四層與哨兵', h=760, seed=13, svg='\n'.join([
 T(600,56,'同一個提示裡可以同時有好幾個 RULES-TOKEN；哪個優先是模型自己說的',30,bold=True,anchor='middle'),
 T(140,150,'~/.claude/CLAUDE.md',16,bold=True), T(140,172,'使用者層，每個專案都載',13,'#2B4C7E'), T(140,194,'（沒放 token）',13,'#7A8399'),
 T(140,270,'proj/CLAUDE.md',16,bold=True), T(140,292,'專案根',13,'#2B4C7E'), T(140,314,'RULES-TOKEN: v2-bravo',14,hand=True),
 T(140,390,'proj/CLAUDE.local.md',16,bold=True), T(140,412,'本機私有',13,'#2B4C7E'), T(140,434,'RULES-TOKEN: v3-local-charlie',14,hand=True),
 T(140,510,'proj/sub/CLAUDE.md',16,bold=True), T(140,532,'巢狀，離工作目錄近',13,'#2B4C7E'), T(140,554,'RULES-TOKEN: v4-nested-delta',14,hand=True),
 T(760,124,'cwd = proj',17,bold=True,anchor='middle'), T(980,124,'cwd = proj/sub',17,bold=True,anchor='middle'),
 T(760,160,'載入',13,anchor='middle'), T(980,160,'載入',13,anchor='middle'),
 T(760,280,'載入 v2',13,anchor='middle'), T(980,280,'載入 v2',13,anchor='middle'),
 T(760,400,'載入 v3',13,anchor='middle'), T(980,400,'（本次未放）',13,'#7A8399',anchor='middle'),
 T(760,520,'沒載入',13,'#F0A35E',anchor='middle'), T(980,520,'載入 v4',13,anchor='middle'),
 T(760,600,'它答：v3',15,bold=True,anchor='middle'), T(980,600,'它答：v4',15,bold=True,anchor='middle'),
 T(760,622,'「local 優先」',13,'#F0A35E',anchor='middle'), T(980,622,'「較近者優先」',13,'#F0A35E',anchor='middle'),
 T(600,700,'--resume：規則檔重讀（v2），舊 token（v1）仍在對話歷史裡；自述來源前後不一致，哨兵才是證據。',18,bold=True,anchor='middle'),
 T(1180,748,'示意；依 2026-09-13 七次執行，模型 claude-sonnet-5，無工具',12,'#7A8399',anchor='end'),
]), js="""
note(100,120,380,90,-0.6,'n'); note(100,240,380,90,0.5,'y'); note(100,360,380,90,-0.4,'n'); note(100,480,380,90,0.6,'n');
// columns
[760,980].forEach(x=>{ box(x-90,100,180,40,0,MUTED); });
// checks / crosses
check(690,150,INK); check(910,150,INK); check(690,270,INK); check(910,270,INK); check(690,390,INK);
cross(700,514,ORG); check(910,510,INK);
add(rc.line(560,470,560,580,{roughness:1.3,strokeWidth:2,stroke:SOFT,strokeLineDash:[7,5],seed:S()}));
box(670,580,180,56,-0.5,ORG); box(890,580,180,56,0.5,ORG);
hl(600-430,684,860,26);
""")

# ---------- Day 14: three layers ----------
FIGS['day14-three-layers-r1'] = dict(title='Day 14 三層紀錄與斷點', h=740, seed=14, svg='\n'.join([
 T(600,56,'exit 0 在第一層；「做了沒」只有第二層看得見',30,bold=True,anchor='middle'),
 T(70,150,'Run record',18,bold=True), T(70,176,'起訖・回合・token・成本・exit・session・commit',13,'#2B4C7E'),
 T(70,320,'工具事件',18,bold=True), T(70,346,'每次 tool_use / tool_result',13,'#2B4C7E'),
 T(70,490,'應用 runtime',18,bold=True), T(70,516,'被操作系統的 log / metric / trace',13,'#2B4C7E'),
 # run1 timeline row 1
 T(420,140,'run1',15,bold=True,hand=True), T(480,140,'12 回合・22 分・exit 0・成功（待人審）',14),
 T(420,205,'run2',15,bold=True,hand=True), T(480,205,'34 回合・16 分・exit 0・成功（待人審）',14),
 T(420,300,'run1 報告：「即時 API 不可用，改用快照」',14),
 T(420,330,'事件層：沒有任何一次 Jira 呼叫',15,'#F0A35E',bold=True),
 T(420,385,'run2 事件層：兩次呼叫＋真實回傳',14,'#2B4C7E'),
 T(420,480,'這次任務唯讀，沒有應用端變化',14,'#7A8399'),
 T(420,506,'（第四幕才會有這一層）',13,'#7A8399'),
 T(880,300,'斷點',15,'#F0A35E',bold=True,hand=True),
 T(600,610,'讀法：報告裡每一句「我做了 X」，對回事件層有沒有那次呼叫；對不上的那句就是斷點。',18,bold=True,anchor='middle'),
 T(600,660,'沒有跨系統關聯 ID，不叫端到端 trace。',16,'#2B4C7E',anchor='middle'),
 T(1180,728,'示意；run1／run2 為 2026-08-07 歷史紀錄，數字依 run record',12,'#7A8399',anchor='end'),
]), js="""
box(40,110,1120,140,0,INK); box(40,280,1120,150,0,INK); box(40,450,1120,110,0,SOFT,true);
// run rows: green-ish checks in layer 1
check(400,136,INK); check(400,201,INK);
// layer 2: run1 gap
box(400,286,520,62,-0.3,ORG); cross(880,317,ORG); check(400,381,INK);
arrow(700,250,700,286,SOFT,true,1.6);
hl(600-430,594,860,28);
""")

# ---------- Day 15: two-layer auth ----------
FIGS['day15-two-layer-auth-r1'] = dict(title='Day 15 兩層授權與三個假訊號', h=760, seed=15, svg='\n'.join([
 T(600,56,'ACL 設對了、也回讀正確，但人不在 project——權限掛空檔',30,bold=True,anchor='middle'),
 T(300,150,'Repo ACL',20,bold=True,anchor='middle'), T(300,176,'namespace / token 綁 repo id',13,'#2B4C7E',anchor='middle'), T(300,200,'permission show → effectiveAllow 正確 ✓',14,anchor='middle'),
 T(300,330,'Project 群組',20,bold=True,anchor='middle'), T(300,356,'Readers / Contributors / …',13,'#2B4C7E',anchor='middle'), T(300,380,'目標 project 只有我一個人',15,'#F0A35E',bold=True,anchor='middle'),
 T(300,440,'沒有這層，上面全部無效',14,'#F0A35E',anchor='middle'),
 T(830,130,'三個「看起來成功」的訊號',18,bold=True,anchor='middle'),
 T(660,190,'permission update 回 allow: 0',15,bold=True), T(660,212,'不是噪音，是「人不在 project」的症狀',13,'#2B4C7E'),
 T(660,280,'az repos show 的 size = 0',15,bold=True), T(660,302,'延遲欄位，剛 push 完就是 0',13,'#2B4C7E'),
 T(660,370,'az 印出的中文全是亂碼',15,bold=True), T(660,392,'主控台編碼；git log 顯示正常，別去 force push',13,'#2B4C7E'),
 T(830,470,'判斷只靠回讀：群組清單・permission show・items・git log',14,'#F0A35E',anchor='middle'),
 T(300,560,'main 的 sha ≠ 我 push 的',15,bold=True,anchor='middle'), T(300,584,'是新管理者自己 push 測試檔又刪掉',13,'#2B4C7E',anchor='middle'), T(300,606,'權限生效的正面證據；我的條件把好事判成壞事',13,'#F0A35E',anchor='middle'),
 T(600,690,'通過條件比步驟更容易寫錯，而且錯了不會被發現。',22,bold=True,anchor='middle'),
 T(1180,748,'示意；依 2026-08-17 作業紀錄與筆記，組織、人名去識別',12,'#7A8399',anchor='end'),
]), js="""
box(120,120,360,100,-0.5,INK); box(120,300,360,100,0.5,ORG,true);
arrow(300,300,300,224,ORG,false,2.4);
note(620,160,440,70,-0.4,'y'); note(620,250,440,70,0.5,'y'); note(620,340,440,70,-0.5,'y');
box(120,540,360,84,0.4,MUTED);
hl(600-300,674,600,32);
""")

# ---------- Day 16: skill three runs ----------
FIGS['day16-skill-three-runs-r1'] = dict(title='Day 16 同一個 Skill 三次任務', h=740, seed=16, svg='\n'.join([
 T(600,56,'舊坑沒再踩，每次一個新坑；修的是條件，不是步驟',30,bold=True,anchor='middle'),
 T(200,140,'08-17',18,bold=True,anchor='middle',hand=True), T(600,140,'08-21',18,bold=True,anchor='middle',hand=True), T(1000,140,'09-03',18,bold=True,anchor='middle',hand=True),
 T(200,190,'PM 共用 repo',15,anchor='middle'), T(600,190,'另一團隊的 repo',15,anchor='middle'), T(1000,190,'新 project＋repo',15,anchor='middle'),
 T(200,260,'兩層授權',14,'#F0A35E',anchor='middle'), T(200,282,'通過條件寫錯（sha）',14,'#F0A35E',anchor='middle'), T(200,304,'az 亂碼',14,'#F0A35E',anchor='middle'),
 T(600,260,'沒踩舊坑',14,'#2B4C7E',anchor='middle'), T(600,282,'「之前是不是有 skill？」',14,anchor='middle',hand=True), T(600,304,'README 待確認',14,'#7A8399',anchor='middle'),
 T(1000,260,'群組與 ACL 並行',14,'#F0A35E',anchor='middle'), T(1000,282,'一人 allow: 0',14,'#F0A35E',anchor='middle'),
 T(200,380,'Skill v1',17,bold=True,anchor='middle'), T(200,404,'六道 Gate・回讀表・坑表',13,'#2B4C7E',anchor='middle'),
 T(600,380,'v1 重用',17,bold=True,anchor='middle'), T(600,404,'只答三個決策：落點、名單、權限',13,'#2B4C7E',anchor='middle'),
 T(1000,380,'Skill v2',17,bold=True,anchor='middle'), T(1000,404,'群組先於 ACL，不可平行；0 是訊號',13,'#2B4C7E',anchor='middle'),
 T(600,500,'步驟改動',16,bold=True,anchor='end'), T(620,500,'Gate 4 移到 Gate 3 前，禁止平行',15),
 T(600,536,'通過條件改動',16,bold=True,anchor='end'), T(620,536,'allow: 0 → 回頭補群組；sha 相等 → ref 存在且 objectId 非空',15),
 T(600,600,'留痕 → 訊號 → 提案 → 閘門（人收退＋實跑）→ 降級',17,'#2B4C7E',anchor='middle'),
 T(600,626,'三次以上只是提案門檻，升不升是閘門的人決定',13,'#7A8399',anchor='middle'),
 T(600,690,'步驟寫錯會報錯；條件寫錯，跑一百次都安靜地通過。',22,bold=True,anchor='middle'),
 T(1180,728,'示意；依 2026-08-17／08-21／09-03 作業紀錄，組織、人名去識別',12,'#7A8399',anchor='end'),
]), js="""
add(rc.line(120,160,1080,160,{roughness:1.3,strokeWidth:2,stroke:INK,seed:S()}));
[200,600,1000].forEach(x=>circle(x,160,9,INK,INK));
note(80,236,240,90,-0.6,'n'); note(480,236,240,90,0.5,'n'); note(880,236,240,90,-0.5,'n');
box(90,360,220,60,-0.4,MUTED); box(490,360,220,60,0.5,MUTED); box(890,360,220,60,-0.5,MUTED);
arrow(200,326,200,360,ORG); arrow(1000,326,1000,360,ORG); arrow(310,390,490,390,SOFT,true); arrow(710,390,890,390,SOFT,true);
box(300,478,600,80,0.3,INK);
hl(600-330,674,660,32);
""")

# ---------- Day 17: handoff card ----------
FIGS['day17-handoff-card-r1'] = dict(title='Day 17 接手卡與三手交接', h=740, seed=17, svg='\n'.join([
 T(600,56,'接手卡五格；右邊是三手交接時這五格的實際狀態',30,bold=True,anchor='middle'),
 T(300,124,'接手卡',20,bold=True,anchor='middle'),
 *sum([[T(120,y,k,16,bold=True), T(120,y+22,v,13,'#2B4C7E')] for k,v,y in [
   ('誰接','系統、憑證、環境各一個人',176),('什麼情況叫人','403 連續出現、憑證持有人離職、apply 未執行超過一天',256),('叫人時附什麼','根因筆記、憑證綁定表、push 了什麼沒 apply 什麼',336),('接手的人能做什麼','服務帳號、最小權限、逐專案',416),('做到哪裡算交付','TST/UAT 目錄 34 筆核對、RBAC 已 apply',496)]],[]),
 T(880,124,'上板後台，第三手接時',20,bold=True,anchor='middle'),
 T(700,176,'找上一任——已調走',14,'#F0A35E'), T(700,256,'「ArgoCD 暫時不可達」掛了幾週，沒人定義何時叫人',14,'#F0A35E'),
 T(700,336,'要自己從 403 回推到「綁的是前任個人 apiKey」',14,'#F0A35E'), T(700,416,'憑證在別人帳號上，動不了',14,'#F0A35E'),
 T(700,496,'沒有；程式裡還有第一任寫死的名字',14,'#F0A35E'),
 T(600,600,'那個 session 裡 Claude 停下來問我 38 次——每一次都是一個只有人能答的節點。',17,bold=True,anchor='middle'),
 T(600,628,'headless 時沒人可問，它會自己猜；停止條件就是堵這條路：沒有人答就停。',15,'#2B4C7E',anchor='middle'),
 T(600,690,'檔案不能取代責任分工；誰負責，不是 CLAUDE.md 能寫的。',22,bold=True,anchor='middle'),
 T(1180,728,'示意；三手交接與 38 次提問依 2026-08-29～09-05 session 統計，去識別',12,'#7A8399',anchor='end'),
]), js="""
[160,240,320,400,480].forEach((y,i)=>{ box(100,y-4,400,68,i%2?0.3:-0.3,INK); box(680,y-4,440,68,i%2?-0.3:0.3,ORG,true); cross(1100,y+30,ORG); });
hl(600-340,674,680,32);
""")

# ---------- Day 18: two columns ----------
FIGS['day18-two-columns-r1'] = dict(title='Day 18 機器欄位與人工欄位', h=760, seed=18, svg='\n'.join([
 T(600,56,'機器時間自己會來，人的時間不會',30,bold=True,anchor='middle'),
 T(300,124,'機器欄位（hook 自動）',19,bold=True,anchor='middle'), T(900,124,'人工欄位（/worklog 收工時問）',19,bold=True,anchor='middle'),
 T(120,180,'starts = 21   ends = 18',15,hand=True), T(120,208,'10 筆是 5～10 秒的 headless 實驗，machine_minutes 0.1',13,'#2B4C7E'),
 T(120,236,'4 筆 session_id = null（呼叫端沒帶 stdin）',13,'#F0A35E'), T(120,264,'若干 num_turns = null（不留 transcript）',13,'#F0A35E'),
 T(120,320,'欄位',14,bold=True), T(120,344,'session_id・source・cwd・repo・branch・started_at',13,'#2B4C7E'), T(120,366,'ended_at・machine_minutes・num_turns・tokens・tool_uses',13,'#2B4C7E'),
 T(120,420,'machine_minutes = session 經過時間',14), T(120,442,'不是 Claude 運算時間，更不是人的時間',13,'#7A8399'),
 T(720,180,'entries = 0',15,hand=True), T(720,208,'沒有 /worklog 紀錄的 session：17',13,'#F0A35E'),
 T(720,320,'欄位',14,bold=True), T(720,344,'context・implement・review・rework（人工四段）',13,'#2B4C7E'), T(720,366,'waiting（另列，不算人工）',13,'#2B4C7E'), T(720,388,'quality_result・rejected・estimated[]',13,'#2B4C7E'),
 T(720,420,'＋handoff_minutes（附表 v1.1）',14), T(720,442,'不知道就 null；「大概」進 estimated',13,'#7A8399'),
 T(900,540,'？',64,'#F0A35E',anchor='middle',hand=True),
 T(600,690,'AI 少做十分鐘是左邊的數字；人真的少忙十分鐘嗎，要看右邊——右邊是空的。',20,bold=True,anchor='middle'),
 T(1180,748,'示意；數字為 2026-09-13 report.py 輸出，人工欄位零筆',12,'#7A8399',anchor='end'),
]), js="""
box(80,100,480,380,-0.3,INK); box(680,100,480,380,0.3,ORG,true);
hl(115,166,240,26);
add(rc.line(120,300,540,300,{roughness:1.5,strokeWidth:1.4,stroke:SOFT,seed:S()})); add(rc.line(720,300,1140,300,{roughness:1.5,strokeWidth:1.4,stroke:SOFT,seed:S()}));
bubble(900,550,120,80,ORG);
hl(600-450,674,900,30);
""")

# ---------- Day 19: knowledge ladder ----------
FIGS['day19-knowledge-ladder-r1'] = dict(title='Day 19 四層知識梯', h=760, seed=19, svg='\n'.join([
 T(600,56,'四層：越往上讀的人越多、改的門檻越高、寫錯的代價越大',30,bold=True,anchor='middle'),
 T(320,152,'L3 不變條件',20,bold=True,anchor='middle'), T(320,176,'CLAUDE.md，每個 session 必讀',13,'#2B4C7E',anchor='middle'), T(320,198,'誰批准：我，通常在退件之後',13,'#7A8399',anchor='middle'),
 T(320,272,'L2 Skill',20,bold=True,anchor='middle'), T(320,296,'可執行流程，真案例實跑才算被證明',13,'#2B4C7E',anchor='middle'), T(320,318,'誰批准：實跑通過',13,'#7A8399',anchor='middle'),
 T(320,392,'L1 團隊 wiki',20,bold=True,anchor='middle'), T(320,416,'git 版控的筆記，55 篇、16 commits',13,'#2B4C7E',anchor='middle'), T(320,438,'誰批准：我，/brain-save 時',13,'#7A8399',anchor='middle'),
 T(320,512,'L0 自動記憶',20,bold=True,anchor='middle'), T(320,536,'工具自己記，22 個 repo 目錄',13,'#2B4C7E',anchor='middle'), T(320,558,'誰批准：沒有人',13,'#7A8399',anchor='middle'),
 T(760,240,'晉升',16,'#2B4C7E',bold=True), T(760,262,'Day 4 退件單一句話（L1）',13,'#2B4C7E'), T(760,282,'→ 第二輪寫進 CLAUDE.md（L3）',13,'#2B4C7E'), T(760,302,'代價：一個真案例',13,'#7A8399'),
 T(760,400,'降級',16,'#F0A35E',bold=True), T(760,422,'08-17「回傳固定是 0」（L1）',13,'#F0A35E'), T(760,442,'→ 09-03 實跑推翻，改寫；Skill 規則跟著改（L2）',13,'#F0A35E'), T(760,462,'如果已升到 L3，錯的是每個 session',13,'#7A8399'),
 T(600,620,'重要性（在哪層）・載入（Day 13 哨兵）・遵守（Day 12 G1）・強制（Day 12 G2、G4）',15,'#2B4C7E',anchor='middle'),
 T(600,690,'知識往上移不會自動變得更真，只會讓錯誤傳得更遠。',22,bold=True,anchor='middle'),
 T(1180,748,'示意；層數與批准為作者現況，L0 行為依本機版本未引官方',12,'#7A8399',anchor='end'),
]), js="""
[[120,120,'y'],[120,240,'n'],[120,360,'n'],[120,480,'n']].forEach(([x,y,f],i)=>{ box(x,y,400,90,i%2?0.4:-0.4, i===0?INK:INK); if(f==='y') hl(x+6,y+6,388,78); });
// ladder rails
add(rc.line(100,110,100,580,{roughness:1.4,strokeWidth:2.6,stroke:INK,seed:S()})); add(rc.line(540,110,540,580,{roughness:1.4,strokeWidth:2.6,stroke:INK,seed:S()}));
// promotion arrow L1 -> L3
arrow(600,410,600,170,MUTED,false,2.4); arrow(600,170,530,160,MUTED,false,2.4);
// demotion dashed L1 -> rewrite
arrow(560,400,700,410,ORG,true,2.2); arrow(700,410,600,300,ORG,true,2.2);
hl(600-330,674,660,32);
""")

# ---------- Day 20: maintenance package ----------
FIGS['day20-maintenance-package-r1'] = dict(title='Day 20 維護包與乾淨環境自測', h=780, seed=20, svg='\n'.join([
 T(600,56,'維護包六格；下面是自測五步，第 4 步的「通過」是安靜失敗有被記下來',28,bold=True,anchor='middle'),
 *sum([[T(x,150,k,17,bold=True,anchor='middle'), T(x,176,v,12,'#2B4C7E',anchor='middle')] for k,v,x in [
   ('安裝','檔案放哪・設定合併',150),('輸入','stdin JSON・五個問題',330),('預期輸出','兩個 jsonl・一份彙總',510),('權限','只寫家目錄・不連網',690),('維護','VERSION：四個 SHA-256',870),('停止條件','三條，今天補',1050)]],[]),
 T(90,270,'乾淨環境自測 2026-09-13',18,bold=True),
 *sum([[T(120,y,n,15,bold=True,hand=True), T(160,y,s,14), T(760,y,r,14,'#2B4C7E')] for n,s,r,y in [
   ('0','空目錄，沒有 worklog/','—',320),('1','餵一段 SessionStart JSON 給 session_start.py','exit 0，sessions.jsonl 出現一筆 start',360),('2','餵對應的 SessionEnd JSON','exit 0，多一筆 end，machine_minutes 0.0',400),('3','在空的 entries 上跑 report.py','exit 0，entries=0，starts=1 ends=1',440),('4','餵一段不是 JSON 的文字','exit 0，仍寫一筆，session_id = null',480)]],[]),
 T(760,510,'← Day 18 那 4 筆空 id 的來源',13,'#F0A35E'),
 T(90,580,'README 沒寫、自測才冒出來的：settings.json 要合併不能覆蓋・Python 要在 PATH・Windows 家目錄是 USERPROFILE・stdin 沒 JSON 會寫空筆',14,'#2B4C7E'),
 T(600,650,'自測不等於他人試用：我知道每一步該看什麼，換一個人卡的地方會是我想不到的。',17,bold=True,anchor='middle'),
 T(600,710,'先在空目錄跑一次自測，紀錄跟著包走。',22,bold=True,anchor='middle'),
 T(1180,768,'示意；自測輸出與雜湊見 artifacts/v12/day-20/selftest',12,'#7A8399',anchor='end'),
]), js="""
[150,330,510,690,870,1050].forEach((x,i)=>{ box(x-80,120,160,80,i%2?0.5:-0.5,INK); });
hl(790,126,150,68); hl(970,126,150,68);
box(60,290,1080,240,0.2,MUTED);
[320,360,400,440].forEach(y=>check(720,y-6,INK)); circle(724,476,14,ORG);
underline(90,1100,590,SOFT);
hl(600-260,694,520,30);
""")


# ---------- Day 17: receiver status contract ----------
FIGS['day17-receiver-status-contract-r1'] = dict(
 title='同一筆事件，接收端該填什麼——照 SKILL.md 契約決定，不靠推論',
 h=680, seed=171, svg='\n'.join([
 T(600,52,'同一筆事件，接收端該填什麼——照 SKILL.md 契約決定，不靠推論',30,bold=True,anchor='middle'),
 T(190,282,'API 回 200，且觀察到 notify_sent',16,bold=True,anchor='middle'),
 T(190,317,'sender_status = confirmed',15,'#2B4C7E',anchor='middle'),
 T(190,341,'（只證明發送端送出）',14,'#7A8399',anchor='middle'),
 T(555,275,'查得到 receipts.json，',17,bold=True,anchor='middle'),
 T(555,305,'且 notification_id 對得上？',17,bold=True,anchor='middle'),
 T(749,192,'是',17,'#2B4C7E',bold=True,anchor='middle'),
 T(970,181,'receiver_status = confirmed',17,bold=True,anchor='middle'),
 T(970,217,'來源：receipts.json:2-15',16,'#2B4C7E',anchor='middle'),
 T(745,426,'否／查不到',16,'#2B4C7E',bold=True,anchor='middle'),
 T(970,366,'receiver_status = unknown',17,bold=True,anchor='middle'),
 T(970,402,'missing_sources = ["receipts.json"]',16,anchor='middle'),
 T(970,438,'next_action = 找誰要收據',16,anchor='middle'),
 T(985,532,'不可寫成「一定未送達」',17,'#F0A35E',bold=True,anchor='middle'),
 T(970,566,'（查不到 ≠ 未送達）',16,'#F0A35E',anchor='middle'),
 T(600,650,'契約出自 .claude/skills/trace-notification/SKILL.md 查核迴圈第 4–5 步與輸出',16,'#7A8399',anchor='middle',hand=True),
 ]), js="""
note(30,247,320,114,-0.3,'n');
add(rc.polygon([[555,170],[700,290],[555,410],[410,290]],{...base,fill:PAPER,fillStyle:'solid',seed:S()}));
arrow(352,290,405,290);
note(800,137,340,106,0.3,'y');
arrow(666,252,797,194);
box(800,329,340,135,-0.2,INK);
arrow(666,326,797,392);
box(800,495,340,94,0.2,ORG);
cross(834,528,ORG);
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

# -*- coding: utf-8 -*-
"""Day 5 figures (rough.js, paper tokens): (1) effort vs elapsed on two separate rulers, SYNTHETIC; (2) four records joined on one task_id.
Reuses HEAD/T from gen-day11-20-figures.py. Run from repo root: python tools/gen-day05-figures.py"""
import io, os, subprocess, importlib.util
spec = importlib.util.spec_from_file_location('g1120', os.path.join('tools', 'gen-day11-20-figures.py'))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
HEAD, T, OUT = g.HEAD, g.T, g.OUT

FIGS = {}

# ---------- Day 5 fig 1: where did the 20 minutes go ----------
# scale: human bars 8 px/min (70 -> 560 px); elapsed bars 2 px/min (240 -> 480 px). Different rulers on purpose.
seg_before = [('理解 20', 20), ('實作 30', 30), ('審查 15', 15), ('返工 5', 5)]
seg_after = [('理解 15', 15), ('實作 10', 10), ('審查 25', 25), ('返工 20', 20)]
def seg_labels(segs, y):
    out, x = [], 200
    for name, m in segs:
        w = m * 8
        out.append(T(x + w // 2, y, name, 14, anchor='middle', bold=True) if w >= 60 else T(x + w // 2, y - 46, name, 12, '#7A8399', anchor='middle'))
        x += w
    return out
FIGS['day05-effort-vs-elapsed-r1'] = dict(title='Day 5 省下的二十分鐘去了哪', h=720, seed=5, svg='\n'.join([
 T(600,54,'實作省下二十分鐘，人工合計還是七十；交付早了一小時，那是另一把尺',28,bold=True,anchor='middle'),
 T(600,84,'合成教學數字：不是公司工時，也不是 Day 4 案例的計時',14,'#F0A35E',anchor='middle'),
 T(60,140,'人工投入（人分鐘）',18,bold=True),
 T(180,192,'原方式',15,anchor='end'), T(180,292,'加入 AI 後',15,anchor='end'),
 *seg_labels(seg_before, 197), *seg_labels(seg_after, 297),
 T(790,192,'= 70',18,bold=True), T(790,292,'= 70',18,bold=True),
 T(900,236,'實作 −20',15,'#F0A35E',hand=True), T(900,258,'審查 +10、返工 +15',15,'#F0A35E',hand=True), T(900,280,'省下的時間搬了位置',15,'#F0A35E',hand=True),
 T(60,400,'交付經過時間（分鐘，含等待；另一把尺，刻度不同）',18,bold=True),
 T(180,452,'原方式',15,anchor='end'), T(180,522,'加入 AI 後',15,anchor='end'),
 T(700,452,'240',16,bold=True), T(548,522,'180',16,bold=True,anchor='end'),
 T(760,522,'早了 60 分鐘',15,'#2B4C7E',hand=True),
 T(600,630,'開發加速看經過時間，減載看人工投入；兩把尺各量各的，不能互相代替。',21,bold=True,anchor='middle'),
 T(1180,704,'示意；合成數字，附件 dotnet run -- baseline 會印出同一組並標 SYNTHETIC',12,'#7A8399',anchor='end'),
]), js="""
const FILLS=[{fill:SOFT,gap:9},{fill:MUTED,gap:6},{fill:ORG,gap:7},{fill:YEL,gap:5}];
function bars(y,segs){let x=200;segs.forEach((m,i)=>{const w=m*8;add(rc.rectangle(x,y,w,52,{...base,seed:S(),fill:FILLS[i].fill,fillStyle:'hachure',hachureAngle:-40,hachureGap:FILLS[i].gap,fillWeight:1.6}));x+=w;});}
bars(160,[20,30,15,5]); bars(260,[15,10,25,20]);
add(rc.line(200,150,200,330,{roughness:1,strokeWidth:1.2,stroke:SOFT,seed:S()}));
add(rc.line(200,330,760,330,{roughness:1,strokeWidth:1.2,stroke:SOFT,seed:S()}));
[0,10,20,30,40,50,60,70].forEach(m=>{add(rc.line(200+m*8,330,200+m*8,336,{roughness:0.8,strokeWidth:1,stroke:SOFT,seed:S()}));});
arrow(440,214,590,262,ORG,false,2.2);
// elapsed bars: 2 px/min
add(rc.rectangle(200,420,480,44,{...base,seed:S(),fill:PAPER,fillStyle:'solid'}));
add(rc.rectangle(200,490,360,44,{...base,seed:S(),fill:PAPER,fillStyle:'solid'}));
add(rc.line(200,410,200,550,{roughness:1,strokeWidth:1.2,stroke:SOFT,seed:S()}));
add(rc.line(200,550,700,550,{roughness:1,strokeWidth:1.2,stroke:SOFT,seed:S()}));
[0,60,120,180,240].forEach(m=>{add(rc.line(200+m*2,550,200+m*2,556,{roughness:0.8,strokeWidth:1,stroke:SOFT,seed:S()}));});
arrow(680,512,572,512,MUTED,true,2);
hl(600-420,614,840,30);
// SYNTHETIC stamp
add(rc.rectangle(930,96,250,54,{roughness:1.6,strokeWidth:2.4,stroke:ORG,seed:S()}),'rotate(-4 1055 123)');
""")
FIGS['day05-effort-vs-elapsed-r1']['svg'] += '\n' + T(1055,131,'SYNTHETIC',26,'#F0A35E',anchor='middle',bold=True,hand=True).replace('<text ', '<text transform="rotate(-4 1055 123)" ')

# ---------- Day 5 fig 2: four records, one task_id ----------
FIGS['day05-task-links-r1'] = dict(title='Day 5 同一件工作，四種紀錄', h=700, seed=55, svg='\n'.join([
 T(600,54,'同一件工作，四種紀錄先對上同一個 task_id，再談加總',28,bold=True,anchor='middle'),
 T(230,156,'工單／需求',19,bold=True,anchor='middle'), T(230,182,'ticket.md：開始條件、規則來源、接受條件',13,'#2B4C7E',anchor='middle'), T(230,206,'公司通常有：Jira、工單系統',13,'#7A8399',anchor='middle'), T(230,232,'不能推論：工單開著的每分鐘都是人工',12,'#F0A35E',anchor='middle'),
 T(970,156,'PR／CI',19,bold=True,anchor='middle'), T(970,182,'diff.patch、測試 18 斷言、退件與重審',13,'#2B4C7E',anchor='middle'), T(970,206,'公司通常有：Git、CI 紀錄',13,'#7A8399',anchor='middle'), T(970,232,'不能推論：測試綠燈等於業務接受',12,'#F0A35E',anchor='middle'),
 T(230,496,'Claude Code run',19,bold=True,anchor='middle'), T(230,522,'G0-A：5 回合、25 秒、$0.06、OWNER_REQUIRED',13,'#2B4C7E',anchor='middle'), T(230,546,'claude -p 的 JSON 回傳、trace',13,'#7A8399',anchor='middle'), T(230,572,'不能推論：run 時間等於人工投入',12,'#F0A35E',anchor='middle'),
 T(970,496,'人工簡記',19,bold=True,anchor='middle'), T(970,522,'準備／操作／核對／返工／等待',13,'#2B4C7E',anchor='middle'), T(970,546,'2026-09-17：0 筆',15,'#F0A35E',anchor='middle',bold=True), T(970,572,'不能推論：事後估計等於當下實測',12,'#F0A35E',anchor='middle'),
 T(600,318,'task_id: day04-pr-A',20,bold=True,anchor='middle',hand=True), T(600,344,'任務類型：PR 審查',14,anchor='middle'), T(600,366,'方法：一般審查提示，無 plugin',14,anchor='middle'),
 T(600,424,'一個任務可有多個 session、run、PR；session 數不是任務數',13,'#7A8399',anchor='middle'),
 T(600,640,'前三種紀錄公司大多已經有；第四種幾乎沒人有，而它是分子。',21,bold=True,anchor='middle'),
 T(1180,688,'示意；依 plugin-lab G0-A 原件與作者記錄器狀態（2026-09-17）整理',12,'#7A8399',anchor='end'),
]), js="""
box(70,130,320,120,-0.5); box(810,130,320,120,0.5); box(70,470,320,120,0.4);
box(810,470,320,120,-0.4,ORG,true);
box(470,286,260,98,0,MUTED);
arrow(390,200,470,300,MUTED,false,2); arrow(810,200,730,300,MUTED,false,2); arrow(390,520,470,370,MUTED,false,2); arrow(810,520,730,370,ORG,true,2);
hl(600-400,624,800,30);
""")

def main():
    for name, f in FIGS.items():
        html = HEAD % dict(title=f['title'], h=f['h'], seed=f['seed'], svg=f['svg'], js=f['js'])
        p = os.path.join(OUT, name + '.html'); io.open(p, 'w', encoding='utf-8', newline='\n').write(html)
        r = subprocess.run(['python', 'tools/export-diagram-png.py', p, os.path.join(OUT, name + '.png'), '2', '1300'], capture_output=True, text=True)
        print(name, 'ok' if r.returncode == 0 else r.stderr[-300:])
if __name__ == '__main__':
    main()

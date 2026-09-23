# -*- coding: utf-8 -*-
"""Day 4 figure: rule ladder (退件單→CLAUDE.md→skill→plugin→repo→Action) + lab result strip. Reuses HEAD/T from gen-day11-20-figures.py."""
import io, os, subprocess, importlib.util
spec = importlib.util.spec_from_file_location('g1120', os.path.join('tools', 'gen-day11-20-figures.py'))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
HEAD, T, OUT = g.HEAD, g.T, g.OUT

FIG = dict(title='Day 4 退件單怎麼變成團隊的工具', h=780, seed=4, svg='\n'.join([
 T(600,56,'退件單 → 專案規則 → skill → plugin → repo → Action：每一步誰批准、怎麼驗',28,bold=True,anchor='middle'),
 *sum([[T(x,150,k,17,bold=True,anchor='middle'), T(x,176,v,12,'#2B4C7E',anchor='middle'), T(x,198,w,12,'#7A8399',anchor='middle')] for k,v,w,x in [
   ('退件單','缺哪個依據・誰補・怎麼判','一次一案',120),('CLAUDE.md','驗收條件寫進專案','後續會談：文字靠遵守',330),('skill','/review-pr 四步固定','載入要看 trace',540),('plugin','版本・manifest','v0.1.0',750),('repo／Action','kit/review・只准評論','擋合併靠 protection',970)]],[]),
 T(600,250,'批准的人：作者 → 專案 Owner → 收退者 → 版本維護者 → 團隊；每上一層，錯誤傳得更遠',14,'#F0A35E',anchor='middle'),
 T(90,330,'考卷：同一份 diff，兩份 PR，四個條件',18,bold=True),
 *sum([[T(150,y,a,14,bold=True), T(330,y,b,13), T(520,y,c,13), T(760,y,d,13,'#2B4C7E'), T(940,y,e,13)] for a,b,c,d,e,y in [
   ('','skill','verdict','發現 block／ask／note','check_card',380),
   ('G0-A 缺來源','無','OWNER_REQUIRED','2／4／0','通過（JSON 壞，修過）',415),
   ('S-A 缺來源','有','OWNER_REQUIRED','2／1／1・契約 3 缺','通過',450),
   ('S-B 有來源','有','OWNER_REQUIRED（政策）','0／2／2・契約 5 齊','通過',485),
   ('G0-B 有來源','無','NEEDS_EVIDENCE','0／1／1','不通過：碰付款沒送 Owner',520)]],[]),
 T(600,590,'不裝 skill 也會審，A 案照樣抓到；差在 B 案：同一條政策 G0 沒做到，skill 做到了，程式又驗了一次。',16,'#2B4C7E',anchor='middle'),
 T(600,618,'第一輪 skill 也漏過一次（ticket 版本不符是 G0 抓到的）——載入不等於更準。',14,'#F0A35E',anchor='middle'),
 T(600,690,'skill 不是讓 AI 更會抓，是讓同一條規則每次都被走一遍、而且驗得了。',22,bold=True,anchor='middle'),
 T(1180,768,'示意；kit/review/plugin-lab 六次 run，兩份合成 PR，一個模型；非正確率統計',12,'#7A8399',anchor='end'),
]), js="""
[120,330,540,750,970].forEach((x,i)=>{ box(x-95,120,190,96,i%2?0.5:-0.5,INK); });
arrow(215,160,235,160,MUTED,false,2.4); arrow(425,160,445,160,MUTED,false,2.4); arrow(635,160,655,160,MUTED,false,2.4); arrow(845,160,875,160,MUTED,false,2.4);
hl(445,126,190,84);
box(60,355,1080,190,0.2,MUTED);
add(rc.line(80,392,1120,392,{roughness:1.2,strokeWidth:1,stroke:SOFT,seed:S()}));
check(940-16,409,INK); check(940-16,444,INK); check(940-16,479,INK); cross(940-18,514,ORG);
hl(600-370,674,740,32);
""")

def main():
    name = 'day04-rule-ladder-r1'
    html = HEAD % dict(title=FIG['title'], h=FIG['h'], seed=FIG['seed'], svg=FIG['svg'], js=FIG['js'])
    p = os.path.join(OUT, name + '.html'); io.open(p, 'w', encoding='utf-8', newline='\n').write(html)
    r = subprocess.run(['python', 'tools/export-diagram-png.py', p, os.path.join(OUT, name + '.png'), '2', '1300'], capture_output=True, text=True)
    print(name, 'ok' if r.returncode == 0 else r.stderr[-300:])
if __name__ == '__main__':
    main()

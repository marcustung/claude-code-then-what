"""Day 26 house-style data plot. Uses r1 load() unchanged; no generated data."""
from pathlib import Path
import hashlib, json, random, math
from PIL import Image, ImageDraw, ImageFont
from plot_starvation import load, SRC
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'assets/diagrams/v12/investigation-notes/day26-threadpool-metrics-r3.png'
PAPER='#FAF6EE'; NAVY='#16345A'; ORANGE='#CB702E'; SOFT='#718399'; GRID='#DDDCD4'; YELLOW='#F6E27A'
fontpath=str(ROOT/'tools/fonts/lxgw-wenkai-tc/WenKaiTC-CDN.ttf')
def font(n): return ImageFont.truetype(fontpath,n)
im=Image.new('RGB',(1600,1160),PAPER); d=ImageDraw.Draw(im)
rng=random.Random(26)
# Paper grain and marker strokes are decorative only, never applied to data.
for _ in range(50000):
    x,y=rng.randrange(1600),rng.randrange(1160)
    d.point((x,y),fill=rng.choice(['#F8F4EC','#F9F5ED','#FBF7EF']))
def marker(x,y,w,h):
    for j in range(0,h,3):
        pts=[(x+i+rng.uniform(-4,4),y+j+math.sin(i/87)*2+rng.uniform(-2,2)) for i in range(0,w,12)]
        d.line(pts,fill=rng.choice(['#F6E27A','#F7E589','#F5DF72']),width=5)
def sketch(points,color=NAVY,width=3):
    d.line(points,fill=color,width=width,joint='curve')
    d.line([(x+rng.uniform(-2,2),y+rng.uniform(-2,2)) for x,y in points],fill=color,width=1)

def text(x,y,s,n=26,c=NAVY): d.text((x,y),s,font=font(n),fill=c,stroke_width=1 if n>=48 else 0)
# Notebook badge mirrors the series; chart axes remain exact.
sketch([(58,48),(239,35),(248,169),(65,179),(58,48)])
sketch([(66,178),(247,169),(245,179),(67,188)])
for y in (67,96,125,154):
    d.arc((43,y-8,75,y+10),70,310,fill=NAVY,width=3)
text(86,58,'Day 26',36)
text(82,110,'實測筆記',28)
marker(315,115,1040,28)
text(312,55,'CPU 不忙，工作卻越排越多',59)
text(318,160,'同一輪故障，三種訊號一起看',30)
sketch([(1410,79),(1440,65)],width=4)
sketch([(1418,108),(1452,112)],width=4)
t, series=load(); L=135; R=1210; TOP=270; PH=180; GAP=75; xmax=60
panels=[('執行緒數（條）','threads',100,NAVY,'執行緒持續增加','不代表工作順利完成'),('待處理工作（件）','pending',200,ORANGE,'工作正在排隊','峰值 180 件'),('CPU（單核 %，1 秒移動平均）','cpu',100,SOFT,'大部分時間偏低','不能只看 CPU 判斷')]
for k,(name,key,ym,color,note1,note2) in enumerate(panels):
    y0=TOP+k*(PH+GAP); y1=y0+PH
    X=lambda x:L+(R-L)*x/xmax
    Y=lambda y:y1-PH*y/ym
    text(L,y0-43,name,29,color)
    for x in range(0,61,10): d.line([(X(x),y0),(X(x),y1)],fill=GRID,width=1)
    for g in (0,ym/2,ym):
        d.line([(L,Y(g)),(R,Y(g))],fill=GRID,width=1)
        text(L-62,Y(g)-14,f'{g:.0f}',24,SOFT)
    d.line([(L,y0),(L,y1),(R,y1)],fill=SOFT,width=2)
    d.line([(X(x),Y(y)) for x,y in zip(t,series[key]) if x<=xmax],fill=color,width=4)
    marker(1234,y0+43,295,19)
    text(1240,y0+17,note1,30,color); text(1240,y0+75,note2,25)
    sketch([(1238,y0+122),(1390,y0+127),(1503,y0+119)],color,2)
    sketch([(1230,y0+140),(1220,y0+149),(1217,y0+164)],color,2)

    if k==2:
        for x in range(0,61,10): text(X(x)-12,y1+10,str(x),24,SOFT)
        text(590,y1+42,'開始後秒數',26)
sketch([(75,1048),(490,1045),(1010,1050),(1520,1044)],NAVY,2)
text(80,1069,'原始取樣間隔約 100 ms；CPU 沿用原圖的 1 秒移動平均。',25)
text(80,1110,'CPU 以單一核心為基準，不是整台主機的使用率。資料未變更。',24,SOFT)
im.save(OUT)
meta={'source':str(SRC.relative_to(ROOT)), 'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'samples':len(t),'time_axis_seconds':[0,60], 'series_sha256':hashlib.sha256(json.dumps([t,series],sort_keys=True).encode()).hexdigest(),'peaks':{k:max(series[k]) for k in ('threads','pending','cpu')},'data_transform':'Unchanged plot_starvation.load(); CPU trailing 1s sample arithmetic mean; same 0-60s display as r1.'}
OUT.with_suffix('.data.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT); print(json.dumps(meta,ensure_ascii=False))

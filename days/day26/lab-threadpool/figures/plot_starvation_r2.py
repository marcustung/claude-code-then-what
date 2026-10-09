"""Day 26 house-style data plot. Uses r1 load() unchanged; no generated data."""
from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw, ImageFont
from plot_starvation import load, SRC
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'assets/diagrams/v12/investigation-notes/day26-threadpool-metrics-r2.png'
PAPER='#FAF6EE'; NAVY='#16345A'; ORANGE='#CB702E'; SOFT='#718399'; GRID='#DDDCD4'; YELLOW='#F6E27A'
fontpath='C:/Windows/Fonts/kaiu.ttf'
def font(n): return ImageFont.truetype(fontpath,n)
im=Image.new('RGB',(1600,1110),PAPER); d=ImageDraw.Draw(im)
def text(x,y,s,n=26,c=NAVY): d.text((x,y),s,font=font(n),fill=c)
d.polygon([(335,68),(1300,61),(1292,111),(328,114)],fill=YELLOW)
text(65,32,'Day 26 / 實測筆記',25)
text(340,60,'CPU 不忙，工作卻越排越多',52)
text(340,126,'同一輪故障，三種訊號一起看',29)
t, series=load(); L=135; R=1210; TOP=225; PH=180; GAP=75; xmax=60
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
    d.line([(1240,y0+45),(1525,y0+41)],fill=YELLOW,width=20)
    text(1240,y0+23,note1,30,color); text(1240,y0+77,note2,25)
    if k==2:
        for x in range(0,61,10): text(X(x)-12,y1+10,str(x),24,SOFT)
        text(590,y1+42,'開始後秒數',26)
d.line([(75,1000),(1520,1000)],fill=NAVY,width=2)
text(80,1020,'原始取樣間隔約 100 ms；CPU 沿用原圖的 1 秒移動平均。',25)
text(80,1060,'CPU 以單一核心為基準，不是整台主機的使用率。資料未變更。',24,SOFT)
im.save(OUT)
meta={'source':str(SRC.relative_to(ROOT)), 'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'samples':len(t),'time_axis_seconds':[0,60], 'series_sha256':hashlib.sha256(json.dumps([t,series],sort_keys=True).encode()).hexdigest(),'peaks':{k:max(series[k]) for k in ('threads','pending','cpu')},'data_transform':'Unchanged plot_starvation.load(); CPU trailing 1s sample arithmetic mean; same 0-60s display as r1.'}
OUT.with_suffix('.data.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT); print(json.dumps(meta,ensure_ascii=False))

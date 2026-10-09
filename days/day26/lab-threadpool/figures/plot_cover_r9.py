"""Draw actual empirical data on an illustrated board; never synthesize curves."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
from plot_starvation import load,SRC
ROOT=Path(__file__).resolve().parents[3]
DIR=ROOT/'assets/covers/v12/day-26'
im=Image.open(DIR/'day26-threadpool-evidence-r8-base.png').convert('RGB'); d=ImageDraw.Draw(im)
fontfile=str(ROOT/'tools/fonts/lxgw-wenkai-tc/WenKaiTC-CDN.ttf')
def text(x,y,s,size=23,color='#16345A',bold=False):
 d.text((x,y),s,font=ImageFont.truetype(fontfile,size),fill=color,stroke_width=1 if bold else 0)
t,series=load(); L,R=448,1177
text(395,428,'同一輪實測：執行緒增加，CPU 多數時間偏低',33,bold=True)
for key,label,y0,y1,color in [('threads','執行緒（條）',510,607,'#16345A'),('cpu','CPU（單核 %，1 秒移動平均）',675,772,'#CB702E')]:
 if key=='threads':
  text(402,y0-43,'執行緒',32,color,True)
  text(509,y0-35,'（條）',23,color)
 else:
  text(402,y0-43,'CPU',32,color,True)
  text(481,y0-35,'（單核 %，1 秒移動平均）',23,color)
 X=lambda x:L+(R-L)*x/60
 Y=lambda y:y1-(y1-y0)*y/100
 for g in (0,50,100):
  d.line([(L,Y(g)),(R,Y(g))],fill='#D4D2C8',width=1)
  text(403,Y(g)-11,str(g),19,'#60738A')
 for x in range(0,61,10):
  d.line([(X(x),y0),(X(x),y1)],fill='#E1DDD2',width=1)
 d.line([(L,y0),(L,y1),(R,y1)],fill='#60738A',width=1)
 d.line([(X(x),Y(y)) for x,y in zip(t,series[key]) if x<=60],fill=color,width=3)
 if key=='cpu':
  for x in range(0,61,10):text(X(x)-10,y1+4,str(x),18,'#60738A')
  text(1040,644,'開始後秒數 0–60',18,'#60738A')
out=DIR/'day26-threadpool-evidence-r9.png'; im.save(out)
meta={'source':str(SRC.relative_to(ROOT)),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'series_sha256':hashlib.sha256(json.dumps([t,series],sort_keys=True).encode()).hexdigest(),'samples':len(t),'curves':['threads','cpu'],'time_axis':[0,60],'y_axes':[0,100],'cpu':'Original trailing 1-second sample mean; per core, not whole host','illustration':'imagegen base; only empirical graphs added by plotting code'}
out.with_suffix('.data.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
print(out)

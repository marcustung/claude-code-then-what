"""Draw the incident run's runtime metrics (100 ms samples) on one time axis: threads, pending work, CPU.
Source: blind-runs/20261009T132017Z/0-incident/api/runtime.jsonl (the run replayed into Grafana for Claude). PIL only.
usage: python plot_starvation.py <out.png>"""
from pathlib import Path
from datetime import datetime
import json, sys
from PIL import Image, ImageDraw, ImageFont

SRC = Path(__file__).resolve().parent.parent/'blind-runs/20261009T132017Z/0-incident/api/runtime.jsonl'
FONT = 'C:/Windows/Fonts/msjh.ttc'; BOLD = 'C:/Windows/Fonts/msjhbd.ttc'
W, L, R = 1600, 170, 60
PANELS = [('執行緒數（條）', 'threads', (52, 120, 200), 100),
          ('待處理工作（件）', 'pending', (214, 69, 65), 200),
          ('CPU（單核 %，1 秒移動平均）', 'cpu', (130, 100, 170), 100)]
PH, GAP, TOP, BOT = 170, 50, 110, 90


def load():
    rows = [json.loads(l) for l in SRC.read_text(encoding='utf-8').splitlines() if l.strip()]
    t0 = datetime.fromisoformat(rows[0]['ts'])
    t = [(datetime.fromisoformat(r['ts']) - t0).total_seconds() for r in rows]
    def win(i):  # samples within the previous 1 s
        j = i
        while j > 0 and t[i] - t[j - 1] <= 1.0: j -= 1
        return j
    rate, cpu = [], []
    for i in range(len(rows)):
        j = win(i); dt = max(t[i] - t[j], 1e-9)
        rate.append((rows[i]['completed'] - rows[j]['completed']) / dt if i > j else 0)
        cpu.append(sum(r['cpu_core_percent'] for r in rows[j:i + 1]) / (i - j + 1))
    return t, {'threads': [r['threads'] for r in rows], 'pending': [r['pending'] for r in rows], 'rate': rate, 'cpu': cpu}


def main(out):
    t, s = load(); xmax = 60
    H = TOP + len(PANELS) * (PH + GAP) + BOT
    im = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(im)
    f, fs, fb = ImageFont.truetype(FONT, 24), ImageFont.truetype(FONT, 20), ImageFont.truetype(BOLD, 32)
    dr.text((L, 28), '故障那一輪：執行緒慢慢補、工作一直排，CPU 卻幾乎沒在動（實測，每 100 ms 取樣）', font=fb, fill=(30, 30, 30))
    X = lambda x: L + (W - L - R) * x / xmax
    for k, (name, key, c, ymax) in enumerate(PANELS):
        y0 = TOP + k * (PH + GAP); y1 = y0 + PH
        v = s[key]; ym = ymax or (int(max(v) / 100) + 1) * 100
        Y = lambda y: y1 - PH * y / ym
        dr.text((L, y0 - 34), name, font=f, fill=(40, 40, 40))
        for g in (0, ym / 2, ym):
            dr.line([(L, Y(g)), (W - R, Y(g))], fill=(232, 232, 232)); dr.text((L - 70, Y(g) - 12), f'{g:.0f}', font=fs, fill=(110, 110, 110))
        dr.line([(L, y0), (L, y1), (W - R, y1)], fill=(120, 120, 120), width=2)
        dr.line([(X(x), Y(min(y, ym))) for x, y in zip(t, v) if x <= xmax], fill=c, width=4)
        pk = max(v); print(key, 'peak', round(pk, 1))
    yb = TOP + len(PANELS) * (PH + GAP) - GAP
    for x in range(0, xmax + 1, 10): dr.text((X(x) - 10, yb + 10), f'{x}', font=fs, fill=(90, 90, 90))
    dr.text((W // 2 - 60, yb + 42), '開始後秒數', font=f, fill=(60, 60, 60))
    im.save(out, optimize=True); print(out)

if __name__ == '__main__': main(sys.argv[1])

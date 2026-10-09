"""Replace the gauge on the Day 26 cover's monitor with a mini chart of the real incident metrics
(threads, pending work, CPU from blind-runs/20261009T132017Z/0-incident/api/runtime.jsonl). PIL only.
usage: python cover_minichart.py <cover-in.png> <cover-out.png>"""
from pathlib import Path
import json, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = Path(__file__).resolve().parent.parent/'blind-runs/20261009T132017Z/0-incident/api/runtime.jsonl'
FONT = str(Path(__file__).resolve().parents[3]/'tools/fonts/lxgw-wenkai-tc/WenKaiTC-CDN.ttf')
BOX = (72, 498, 262, 618)   # lower half of the monitor screen in the 1536x1024 cover
S = 4                       # supersample


def main(src, out):
    rows = [json.loads(l) for l in SRC.read_text(encoding='utf-8').splitlines() if l.strip()]
    n = len(rows)
    im = Image.open(src).convert('RGB')
    w, h = (BOX[2] - BOX[0]) * S, (BOX[3] - BOX[1]) * S
    pane = Image.new('RGB', (w, h), (246, 241, 228)); d = ImageDraw.Draw(pane)
    f = ImageFont.truetype(FONT, 15 * S)
    L, R, T, B = 8 * S, w - 58 * S, 8 * S, h - 10 * S
    d.line([(L, T), (L, B), (R, B)], fill=(70, 80, 100), width=2 * S)
    X = lambda i: L + (R - L) * i / (n - 1)
    series = [('threads', 100, (40, 70, 120), '執行緒'), ('pending', 200, (214, 110, 50), '待處理'), ('cpu_core_percent', 100, (120, 130, 145), 'CPU')]
    for key, ym, c, lab in series:
        v = [r[key] for r in rows]
        if key == 'cpu_core_percent':   # 1 s moving average, as in the article chart
            v = [sum(v[max(0, i - 9):i + 1]) / len(v[max(0, i - 9):i + 1]) for i in range(n)]
        pts = [(X(i), B - (B - T) * min(y, ym) / ym) for i, y in enumerate(v)]
        d.line(pts, fill=c, width=3 * S)
    for k, (key, ym, c, lab) in enumerate(series):
        y = T + k * 34 * S
        d.text((R + 6 * S, y), lab, font=f, fill=c)
    pane = pane.resize((w // S, h // S), Image.LANCZOS).filter(ImageFilter.SMOOTH)
    im.paste(pane, BOX[:2]); im.save(out, optimize=True); print(out)

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])

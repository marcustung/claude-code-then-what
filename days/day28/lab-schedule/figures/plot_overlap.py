"""Timeline of the overlap groups (A1/A2/A3): when each run was running, when it opened a work item, and how many items exist.
Reads runs/20261010T162938Z/A*/ (summary.json, requests.jsonl, scheduler.jsonl).
usage: python plot_overlap.py <out.png>"""
from pathlib import Path
from datetime import datetime
import json, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/20261010T162938Z'
FONT = str(Path(__file__).resolve().parents[3] / 'tools/fonts/lxgw-wenkai-tc/WenKaiTC-CDN.ttf')
GROUPS = [('A1', '不加鎖、每次開新的'), ('A2', '不加鎖、開單系統去重'), ('A3', '外層加鎖')]
W, H = 1600, 960
RUNC, ITEM, SKIP, INK, GREY = (70, 110, 170), (214, 110, 50), (150, 150, 150), (30, 40, 60), (110, 110, 110)


def ts(s): return datetime.fromisoformat(s).timestamp()


def main(out):
    im = Image.new('RGB', (W, H), (249, 245, 236)); d = ImageDraw.Draw(im)
    ft, fh, fb, fs = (ImageFont.truetype(FONT, n) for n in (40, 30, 26, 22))
    d.text((70, 36), '上一輪還沒跑完，下一輪又觸發：開了幾張單？', font=ft, fill=INK)
    d.text((70, 96), '2026-10-11 實跑（sonnet，CLI 2.1.292），第 1 輪開始 30 秒後觸發第 2 輪；各組 1 次，以服務端紀錄為準', font=fs, fill=GREY)
    L, R = 330, 1330; SPAN = 90.0
    x = lambda t: L + (R - L) * t / SPAN
    top = 200
    for v in range(0, 91, 10):
        d.line([(x(v), top - 10), (x(v), 830)], fill=(225, 220, 205)); d.text((x(v) - 14, 840), f'{v}s', font=fs, fill=GREY)
    for gi, (g, label) in enumerate(GROUPS):
        s = json.loads((RUN / g / 'summary.json').read_text(encoding='utf-8'))
        reqs = [json.loads(l) for l in (RUN / g / 'requests.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        sched = [json.loads(l) for l in (RUN / g / 'scheduler.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        t0 = ts(s['runs'][0]['started'])
        y0 = top + gi * 210
        d.text((70, y0 + 10), g, font=fh, fill=INK); d.text((70, y0 + 52), label, font=fs, fill=INK)
        for ri, r in enumerate(s['runs']):
            y = y0 + 20 + ri * 70
            if r.get('dispatched'):
                a = ts(r['started']) - t0; b = a + r['seconds']
                d.rounded_rectangle([x(a), y, x(b), y + 34], radius=8, fill=(205, 218, 236), outline=RUNC, width=2)
                d.text((x(b) - 78, y + 3), f"第 {ri + 1} 輪", font=fs, fill=RUNC)
                for q in reqs:
                    if q.get('run') == r['run'] and q['req'] == 'POST /items':
                        t = ts(q['at']) - t0; cx = x(t)
                        d.ellipse([cx - 11, y + 6, cx + 11, y + 28], fill=ITEM)
                        tag = q['item_id'] + ('（併入）' if q.get('existing') else '')
                        d.text((cx - 30, y + 38), tag, font=fs, fill=ITEM)
            else:
                sk = next(e for e in sched if e['run'] == r['run'])
                t = ts(sk['at']) - t0
                d.text((x(t) - 6, y + 2), f'× 第 {ri + 1} 輪未派送：skipped（上一輪仍在跑）', font=fs, fill=SKIP)
        n = s['items_total']
        d.text((R + 60, y0 + 40), f'{n} 張', font=ImageFont.truetype(FONT, 48), fill=ITEM if n > 2 else (60, 130, 80))
    d.ellipse([L, 892, L + 22, 914], fill=ITEM); d.text((L + 32, 886), '開出一張待處理單（服務端紀錄）', font=fs, fill=INK)
    d.text((L + 480, 886), '異常只有 2 個，正確是 2 張', font=fs, fill=INK)
    im.save(out, optimize=True); print(out)


if __name__ == '__main__': main(sys.argv[1])

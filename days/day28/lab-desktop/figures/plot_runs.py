"""Timeline of the 13 Desktop scheduled-task runs: what the run history says vs what actually happened.
Reads runs/20261011T1610Z/ (task-runs.json, requests.jsonl). Times are UTC on 2026-10-11.
usage: python plot_runs.py <out.png>"""
from pathlib import Path
import json, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/20261011T1610Z'
FONT = str(Path(__file__).resolve().parents[3] / 'tools/fonts/lxgw-wenkai-tc/WenKaiTC-CDN.ttf')
W, H = 1600, 1000
BG, INK, GREY, GRID = (249, 245, 236), (30, 40, 60), (110, 110, 110), (225, 220, 205)
OK = (60, 130, 80)
KIND = {  # category: (fill, outline, legend)
    'stuck': ((240, 200, 190), (190, 80, 60), '卡在等人核准'),
    'done': ((205, 218, 236), (70, 110, 170), '跑完並開單'),
    'nodata': ((225, 225, 225), (130, 130, 130), '沒開單（未檢查／讀到既有單）'),
    'blocked': ((220, 205, 236), (120, 80, 170), 'hook 擋下，0 步'),
}
ITEM = (214, 110, 50)
# run index -> (kind, lane); lane 1 only for the Run now that overlapped the stuck first run
KINDS = ['stuck', 'nodata', 'stuck', 'stuck', 'nodata', 'done', 'done', 'done', 'done',
         'blocked', 'blocked', 'blocked', 'blocked']
BLOCKED_WINDOWS = [('16:18:38', '16:25:21'), ('16:36:00', '16:49:03')]  # every-minute fires, no run started


def sec(hms):
    h, m, s = (float(v) for v in hms.split(':'))
    return (h - 16) * 3600 + (m - 10) * 60 + s


def main(out):
    runs = [r for r in json.loads((RUN / 'task-runs.json').read_text(encoding='utf-8')) if 'session' in r]
    reqs = [json.loads(l) for l in (RUN / 'requests.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    posts = [q['at'][11:19] for q in reqs if q['req'] == 'POST /items']
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    ft, fh, fs, fb = (ImageFont.truetype(FONT, n) for n in (40, 28, 22, 48))
    d.text((70, 36), '13 輪都記成「成功」，實際上發生了什麼？', font=ft, fill=INK)
    d.text((70, 96), '2026-10-11 16:10–17:05 UTC，Claude Desktop 本機排程、每分鐘觸發；依任務執行紀錄與服務端紀錄繪製，各組 1 次',
           font=fs, fill=GREY)
    L, R, SPAN = 300, 1420, sec('17:06:00')
    x = lambda t: L + (R - L) * t / SPAN
    top, bot = 170, 800
    for m in range(10, 67, 5):
        t = (m - 10) * 60; hh, mm = 16 + m // 60, m % 60
        d.line([(x(t), top), (x(t), bot)], fill=GRID); d.text((x(t) - 26, bot + 10), f'{hh}:{mm:02d}', font=fs, fill=GREY)
    # blocked windows
    for a, b in BLOCKED_WINDOWS:
        xa, xb = x(sec(a)), x(sec(b))
        d.rectangle([xa, top + 10, xb, bot - 10], fill=(238, 232, 220))
        d.text((xa + 6, top + 16), '每分鐘觸發', font=fs, fill=GREY); d.text((xa + 6, top + 44), '0 輪啟動', font=fs, fill=GREY)
    # lane 1: run history
    y1 = 300
    d.text((70, y1 - 4), '執行紀錄', font=fh, fill=INK); d.text((70, y1 + 32), '寫的', font=fs, fill=GREY)
    for r in runs:
        cx = x(sec(r['started']))
        d.rounded_rectangle([cx - 4, y1, cx + 26, y1 + 30], radius=6, fill=(214, 236, 218), outline=OK, width=2)
        d.text((cx + 1, y1 + 2), '✓', font=fs, fill=OK)
    d.text((x(sec('17:05:00')) + 40, y1 - 2), '13／13', font=fh, fill=OK)
    # lane 2: what actually happened
    y2 = 470
    d.text((70, y2 + 20), '實際', font=fh, fill=INK); d.text((70, y2 + 56), '發生的', font=fs, fill=GREY)
    for i, r in enumerate(runs):
        kind = KINDS[i]; fill, line, _ = KIND[kind]
        lane = 1 if i == 1 else 0
        y = y2 + lane * 70
        a, b = x(sec(r['started'])), max(x(sec(r['last'])), x(sec(r['started'])) + 8)
        d.rounded_rectangle([a, y, b, y + 34], radius=6, fill=fill, outline=line, width=2)
    for p in posts:
        cx = x(sec(p)); d.ellipse([cx - 9, y2 + 8, cx + 9, y2 + 26], fill=ITEM)
    d.text((x(sec('16:10:33')) + 8, y2 + 40), '我 16:25 停掉', font=fs, fill=KIND['stuck'][1])
    d.text((x(sec('16:17:38')) + 14, y2 + 76), '埠設錯，回報未檢查', font=fs, fill=GREY)
    # lane 3: cumulative items
    y3 = 690
    d.text((70, y3 - 10), '累計開單', font=fh, fill=INK); d.text((70, y3 + 26), '異常只有 2 個', font=fs, fill=GREY)
    pts, n = [(x(0), y3 + 60)], 0
    for p in posts:
        n += 1; px = x(sec(p)); pts += [(px, pts[-1][1]), (px, y3 + 60 - n * 7)]
    pts.append((x(sec('17:05:00')), pts[-1][1]))
    d.line(pts, fill=ITEM, width=4)
    d.line([(x(0), y3 + 60 - 2 * 7), (x(sec('17:05:00')), y3 + 60 - 2 * 7)], fill=OK, width=2)
    d.text((x(sec('17:05:00')) + 30, y3 - 8), f'{n} 張', font=fb, fill=ITEM)
    d.text((x(sec('16:12:00')), y3 + 10), '正確是 2 張', font=fs, fill=OK)
    # legend
    lx = 300
    for k in ('stuck', 'done', 'nodata', 'blocked'):
        fill, line, label = KIND[k]
        d.rounded_rectangle([lx, 900, lx + 34, 922], radius=5, fill=fill, outline=line, width=2)
        d.text((lx + 44, 896), label, font=fs, fill=INK); lx += 60 + int(d.textlength(label, font=fs))
    d.ellipse([lx, 902, lx + 18, 920], fill=ITEM); d.text((lx + 28, 896), '開出一張單', font=fs, fill=INK)
    d.text((300, 940), '16:49 起任務改為「自動」權限模式；17:00:30 放下 STOP。', font=fs, fill=GREY)
    im.save(out, optimize=True); print(out)


if __name__ == '__main__': main(sys.argv[1])

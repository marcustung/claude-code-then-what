"""Cumulative proposals created vs. decided at Gate 1 on the real LoopDeck board (from board-proposals.json; card ids anonymized, card content not published).
usage: python plot_board_flow.py <out.png>"""
from pathlib import Path
from datetime import date, timedelta
import json, sys
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT = str(HERE.parents[1] / 'tools/fonts/lxgw-wenkai-tc/WenKaiTC-CDN.ttf')  # 換成你自己的中文字型路徑亦可
D = json.loads((HERE / 'board-proposals.json').read_text(encoding='utf-8'))
START, END = date(2026, 8, 6), date(2026, 10, 11)
W, H = 1600, 900
IN, OUT, INK, GREY = (214, 110, 50), (60, 130, 80), (30, 40, 60), (110, 110, 110)


def d(s): return date.fromisoformat(s)


def main(out):
    im = Image.new('RGB', (W, H), (249, 245, 236)); dr = ImageDraw.Draw(im)
    ft, fb, fs = (ImageFont.truetype(FONT, n) for n in (40, 26, 22))
    dr.text((70, 36), '迴圈提的案越來越多，裁決跟不上', font=ft, fill=INK)
    dr.text((70, 96), '我的工作看板（LoopDeck），改善提案的累計張數；裁決＝Gate 1 第一次離開待裁決狀態。資料：卡片狀態檔的 git 紀錄', font=fs, fill=GREY)
    L, R, T, B = 140, 1340, 190, 720
    days = (END - START).days; ymax = 32
    X = lambda dt: L + (R - L) * (dt - START).days / days
    Y = lambda v: B - (B - T) * v / ymax
    for v in range(0, ymax + 1, 5):
        dr.line([(L, Y(v)), (R, Y(v))], fill=(225, 220, 205)); dr.text((L - 44, Y(v) - 13), str(v), font=fs, fill=GREY)
    for m, lab in [(date(2026, 8, 6), '8/6'), (date(2026, 8, 20), '8/20'), (date(2026, 9, 3), '9/3'), (date(2026, 9, 17), '9/17'),
                   (date(2026, 10, 1), '10/1'), (date(2026, 10, 11), '10/11')]:
        dr.text((X(m) - 20, B + 12), lab, font=fs, fill=GREY)
    dr.line([(L, T), (L, B), (R, B)], fill=(120, 120, 120), width=3)

    def series(key):
        evs = sorted(d(v['created']) if key == 'c' else d(v['decided'][0]) for v in D.values() if (key == 'c' or v['decided']))
        pts, n, cur = [], 0, START
        while cur <= END:
            n = sum(1 for e in evs if e <= cur); pts.append((X(cur), Y(n))); cur += timedelta(days=1)
        return pts, n
    pc, nc = series('c'); pd, nd = series('d')
    dr.line(pc, fill=IN, width=6); dr.line(pd, fill=OUT, width=6)
    dr.text((R + 16, Y(nc) - 18), f'提出 {nc}', font=fb, fill=IN)
    dr.text((R + 16, Y(nd) - 18), f'裁決 {nd}', font=fb, fill=OUT)
    # gap annotation
    gx = X(END) - 10
    dr.line([(gx, Y(nc) + 6), (gx, Y(nd) - 6)], fill=INK, width=2)
    dr.text((gx - 300, Y(16.5)), f'{nc - nd} 張從沒被裁決過', font=fb, fill=INK)
    dr.text((X(date(2026, 8, 13)) + 8, Y(9) + 14), '8/12 之後，只剩一條迴圈的提案有人裁決', font=fs, fill=INK)
    dr.text((70, 790), '已裁決 13 張，落地完成 5 張；最早一批沒裁決的提案，8/17 提出，已等 55 天。', font=fb, fill=INK)
    dr.text((70, 836), '只計 p- 開頭的改善提案（30 張）；不含開發卡與報告卡。卡片內容不公開。', font=fs, fill=GREY)
    im.save(out, optimize=True); print(out)


if __name__ == '__main__': main(sys.argv[1])

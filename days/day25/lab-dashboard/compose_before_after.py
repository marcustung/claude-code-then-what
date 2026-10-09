"""Compose the before/after figure for Day 25 from two real Grafana screenshots.
usage: python compose_before_after.py before.png after.png out.png [after_crop_height]"""
import sys
from PIL import Image, ImageDraw, ImageFont

before, after, out = sys.argv[1:4]
AFTER_H = int(sys.argv[4]) if len(sys.argv) > 4 else None  # trim the empty area below the last row
FONT = 'C:/Windows/Fonts/msjhbd.ttc'
W = 1600  # each side is scaled to this width, then stacked vertically (reads well on phones)


def scaled(path, h=None):
    im = Image.open(path).convert('RGB')
    if h: im = im.crop((0, 0, im.width, h))
    return im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)


def banner(text, sub, color):
    b = Image.new('RGB', (W, 150), color)
    d = ImageDraw.Draw(b)
    d.text((40, 22), text, font=ImageFont.truetype(FONT, 56), fill='white')
    d.text((40, 96), sub, font=ImageFont.truetype(FONT, 30), fill='white')
    return b


parts = [banner('Before：第一版，答案都對，但要讀完才知道', '說明文字、表格、事件清單一大片；要掃過每一列才找到要處理哪一批，也看不出下一步交給誰', (150, 60, 60)),
         scaled(before), Image.new('RGB', (W, 40), (20, 20, 24)),
         banner('After：第七版，看完知道後面處理到哪、交給誰', '標題就是要回答的問題；上方結論與燈號，中間整條流程卡在哪、哪段看不到，下方交給誰與 AI 先查的結果', (40, 120, 70)),
         scaled(after, AFTER_H)]
canvas = Image.new('RGB', (W, sum(p.height for p in parts)), (20, 20, 24))
y = 0
for p in parts:
    canvas.paste(p, (0, y)); y += p.height
canvas.save(out, optimize=True)
print(out, canvas.size)

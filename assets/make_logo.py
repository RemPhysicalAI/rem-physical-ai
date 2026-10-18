#!/usr/bin/env python3
"""Compose the RemPhysicalAI logos from the generated mark."""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(
    HERE, "media-generation-remphysicalai-mark-0-111660d6-44f2-4e8a-9a32-3cdb55827b80.webp")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

mark = Image.open(SRC).convert("RGB")
mark.save(os.path.join(HERE, "logo-mark.png"))

# Full lockup: deep-night panel, mark left, REM huge, PHYSICAL AI small.
W, H = 1680, 660
bg = Image.new("RGB", (W, H), (7, 10, 24))
px = bg.load()
for y in range(H):  # vertical indigo gradient
    t = y / H
    c = (int(10 + 14 * t), int(13 + 12 * t), int(30 + 26 * t))
    for x in range(0, W, 6):
        for dx in range(6):
            if x + dx < W:
                px[x + dx, y] = c

def rounded(img, rad):
    m = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, img.size[0], img.size[1]], rad, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), m)
    return out

tile = mark.resize((520, 520))
bg.paste(rounded(tile, 90).convert("RGB"), (70, 70),
         rounded(tile, 90).split()[3])

def gradient_text(base, xy, text, font, c1, c2, spacing=0):
    layer = Image.new("L", base.size, 0)
    d = ImageDraw.Draw(layer)
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=255)
        w = d.textlength(ch, font=font)
        x += w + spacing
    grad = Image.new("RGB", base.size)
    gp = grad.load()
    x0, y0, x1 = int(xy[0]), int(xy[1]), int(x)
    for gx in range(x0, min(x1, base.size[0])):
        t = (gx - x0) / max(1, (x1 - x0))
        c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        for gy in range(base.size[1]):
            gp[gx, gy] = c
    base.paste(grad, (0, 0), layer)
    return x

draw = ImageDraw.Draw(bg)
rem_font = ImageFont.truetype(BOLD, 300)
end_x = gradient_text(bg, (660, 88), "REM", rem_font,
                      (142, 168, 255), (216, 178, 255), spacing=6)
sub_font = ImageFont.truetype(REG, 84)
x = 672
for ch in "PHYSICAL AI":
    draw.text((x, 442), ch, font=sub_font, fill=(168, 182, 230))
    x += draw.textlength(ch, font=sub_font) + 26
draw.rounded_rectangle([676, 420, x - 8, 428], 4, fill=(245, 197, 107))
bg.save(os.path.join(HERE, "logo-full.png"))
print("logo-mark.png + logo-full.png written; REM ends at x =", end_x)

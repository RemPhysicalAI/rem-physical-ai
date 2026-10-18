#!/usr/bin/env python3
"""Rebuild the /about slides in the REM PhysicalAI brand world:
deep indigo night, golden moon, violet-blue glow — same as the logo."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "about")
W, H = 1600, 1000
GOLD = (245, 197, 107)
GOLD_L = (255, 233, 168)
INDIGO_T = (16, 20, 48)
INDIGO_B = (7, 9, 26)


def bg(seed=7):
    img = Image.new("RGB", (W, H), INDIGO_B)
    px = img.load()
    for y in range(H):
        t = y / H
        c = tuple(int(INDIGO_T[i] + (INDIGO_B[i] - INDIGO_T[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 700, -420, W + 260, 540], fill=(46, 40, 96))
    gd.ellipse([-320, H - 380, 420, H + 320], fill=(30, 26, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(190))
    img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), 0)
    from PIL import ImageChops
    img = ImageChops.add(img, glow)
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(130):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(1, 2.6)
        c = GOLD_L if rnd.random() < 0.4 else (215, 224, 255)
        a = rnd.uniform(90, 230)
        star = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        sd = ImageDraw.Draw(star)
        sd.ellipse([12 - r, 12 - r, 12 + r, 12 + r], fill=c + (int(a),))
        img.paste(star, (int(x), int(y)), star)
    return img


def crescent(d, cx, cy, r, color=GOLD):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.ellipse([cx - r * 0.28, cy - r * 1.06, cx + r * 1.28, cy + r * 0.62],
              fill=INDIGO_B)


def rounded(img, rad):
    m = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(m)
    md.rounded_rectangle([0, 0, img.size[0], img.size[1]], rad, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), m)
    return out


def framed_photo(src, seed):
    img = bg(seed)
    ph = Image.open(src).convert("RGB")
    tw = 1180
    th = int(tw * ph.size[1] / ph.size[0])
    if th > 800:
        th = 800
        tw = int(th * ph.size[0] / ph.size[1])
    ph = ph.resize((tw, th))
    x, y = (W - tw) // 2, (H - th) // 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x - 6, y + 14, x + tw + 6, y + th + 26], 36,
                         fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img.convert("RGBA"),
                                shadow.filter(ImageFilter.GaussianBlur(18)))
    img.paste(rounded(ph, 30), (x, y), rounded(ph, 30))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - 3, y - 3, x + tw + 3, y + th + 3], 33,
                        outline=GOLD + (255,), width=4)
    return img.convert("RGB")


def slide1():
    img = bg(11)
    mark = Image.open(os.path.join(ROOT, "assets", "logo-mark.png")).convert("RGB")
    mark = mark.resize((700, 700))
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([450 - 60, 150 - 60, 450 + 700 + 60, 150 + 700 + 60],
               fill=(255, 206, 110, 60))
    img = Image.alpha_composite(img.convert("RGBA"),
                                halo.filter(ImageFilter.GaussianBlur(60)))
    img.paste(rounded(mark, 120), (450, 150), rounded(mark, 120))
    return img.convert("RGB")


def slide3():
    img = bg(23)
    d = ImageDraw.Draw(img, "RGBA")
    panels = [(90, 210), (570, 210), (1050, 210)]
    pw, ph = 460, 580
    for (x, y) in panels:
        d.rounded_rectangle([x, y, x + pw, y + ph], 44,
                            fill=(24, 30, 64, 235), outline=(150, 168, 255, 120), width=2)
    cx = [90 + 230, 570 + 230, 1050 + 230]
    cy = 500
    # eye — it watches itself
    d.ellipse([cx[0] - 150, cy - 95, cx[0] + 150, cy + 95], fill=(233, 237, 255))
    d.ellipse([cx[0] - 62, cy - 62, cx[0] + 62, cy + 62], fill=(92, 120, 246))
    d.ellipse([cx[0] - 28, cy - 28, cx[0] + 28, cy + 28], fill=(10, 13, 30))
    d.ellipse([cx[0] - 2, cy - 44, cx[0] + 22, cy - 20], fill=(255, 255, 255))
    # heart — people teach it, with love
    hx, hy = cx[1], cy - 10
    d.ellipse([hx - 118, hy - 108, hx - 4, hy + 6], fill=(255, 138, 168))
    d.ellipse([hx + 4, hy - 108, hx + 118, hy + 6], fill=(255, 138, 168))
    d.polygon([(hx - 112, hy - 30), (hx + 112, hy - 30), (hx, hy + 138)],
              fill=(255, 138, 168))
    # moon — it dreams
    crescent(d, cx[2] + 26, cy, 118)
    for sx, sy, sr in [(cx[2] - 130, cy - 130, 7), (cx[2] + 120, cy + 110, 6),
                       (cx[2] - 90, cy + 130, 5)]:
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=GOLD_L)
    return img.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    slide1().save(os.path.join(OUT, "slide1.jpg"), quality=90)
    framed_photo(os.path.join(OUT, "slide2.jpg"), 31).save(
        os.path.join(OUT, "slide2.jpg"), quality=90)
    slide3().save(os.path.join(OUT, "slide3.jpg"), quality=90)
    framed_photo(os.path.join(OUT, "slide4.jpg"), 47).save(
        os.path.join(OUT, "slide4.jpg"), quality=90)
    framed_photo(os.path.join(ROOT, "..", "odc-in-frame-1800.jpg"), 59).save(
        os.path.join(OUT, "slide5.jpg"), quality=90)
    print("slides rebuilt in the brand world")


if __name__ == "__main__":
    main()

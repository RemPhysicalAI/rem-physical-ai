#!/usr/bin/env python3
"""REM PhysicalAI — the presentation, as fully designed slides.

Each slide is a complete poster in the logo's world: deep indigo night,
golden moonlight, the sleeping pup. Title + text are baked into the
image, so the deck looks identical everywhere (board, video, print).
Texts are plain language, concepts first — short enough to read at a
glance. Run: python3 build_slides.py
"""
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = HERE
W, H = 1600, 1000
GOLD = (245, 197, 107)
GOLD_L = (255, 233, 168)
PINK = (255, 138, 168)
WHITE = (240, 244, 255)
BODY = (203, 213, 250)
INDIGO_T = (16, 20, 48)
INDIGO_B = (7, 9, 26)
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

F_TITLE = ImageFont.truetype(BOLD, 92)
F_BODY = ImageFont.truetype(REG, 45)
F_CAP = ImageFont.truetype(BOLD, 30)
F_FOOT = ImageFont.truetype(REG, 27)
F_BRAND = ImageFont.truetype(BOLD, 27)


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
    img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(190)))
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(120):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H * 0.92)
        r = rnd.uniform(1, 2.6)
        c = GOLD_L if rnd.random() < 0.4 else (215, 224, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    return img


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def crescent(d, cx, cy, r, color=GOLD):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.ellipse([cx - r * 0.26, cy - r * 1.04, cx + r * 1.3, cy + r * 0.66],
              fill=INDIGO_T)


def rounded(img, rad):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.size[0], img.size[1]], rad, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), m)
    return out


def header(img, title, body, n, colw=760, seed=7):
    d = ImageDraw.Draw(img, "RGBA")
    d.text((108, 108), title, font=F_TITLE, fill=WHITE)
    tw = d.textlength(title, font=F_TITLE)
    d.rounded_rectangle([112, 232, 112 + min(tw, 300), 240], 4, fill=GOLD)
    y = 300
    for line in wrap(d, body, F_BODY, colw):
        d.text((110, y), line, font=F_BODY, fill=BODY)
        y += 63
    footer(img, n)
    return img


def footer(img, n):
    d = ImageDraw.Draw(img, "RGBA")
    crescent(d, 128, H - 62, 17)
    d.text((158, H - 78), "REM PhysicalAI", font=F_BRAND, fill=GOLD_L)
    label = f"{n} / 5"
    d.text((W - 110 - d.textlength(label, font=F_FOOT), H - 76), label,
           font=F_FOOT, fill=(150, 163, 212))


def photo_panel(img, src, box, caption=None):
    x0, y0, x1, y1 = box
    ph = Image.open(src).convert("RGB")
    tw, th = x1 - x0, y1 - y0
    scale = max(tw / ph.size[0], th / ph.size[1])
    ph = ph.resize((int(ph.size[0] * scale) + 1, int(ph.size[1] * scale) + 1))
    ox = (ph.size[0] - tw) // 2
    oy = (ph.size[1] - th) // 2
    ph = ph.crop((ox, oy, ox + tw, oy + th))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [x0 - 4, y0 + 12, x1 + 4, y1 + 22], 30, fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img.convert("RGBA"),
                                shadow.filter(ImageFilter.GaussianBlur(16)))
    img.paste(rounded(ph, 26), (x0, y0), rounded(ph, 26))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], 29, outline=GOLD, width=4)
    if caption:
        d.text((x0 + 6, y1 + 18), caption, font=ImageFont.truetype(REG, 29),
               fill=GOLD_L)
    return img.convert("RGB")


def slide1():
    img = bg(11)
    mark = Image.open(os.path.join(ROOT, "assets", "logo-mark.png")).convert("RGB")
    mark = mark.resize((600, 600))
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([830, 120, 1570, 860], fill=(255, 206, 110, 55))
    img = Image.alpha_composite(img.convert("RGBA"),
                                halo.filter(ImageFilter.GaussianBlur(60)))
    img.paste(rounded(mark, 105), (880, 170), rounded(mark, 105))
    img = img.convert("RGB")
    return header(img, "REM PhysicalAI",
                  "A system that lets any robot learn by itself. It watches, "
                  "it learns — and while it sleeps it dreams, practices in "
                  "its own little world, and wakes up better.", 1, colw=700)


def slide2():
    img = bg(31)
    img = photo_panel(img, os.path.join(OUT, "src-photo-side.jpg"),
                      (880, 190, 1500, 770))
    return header(img, "The problem",
                  "Robots leave the factory and never learn again. The "
                  "smart ones cost a fortune, and their brains live far "
                  "away, in the cloud. The affordable ones cannot learn "
                  "at all.", 2, colw=700)


def slide3():
    img = bg(23)
    img = header(img, "How it works",
                 "It watches itself and learns from what it sees. People "
                 "can teach it — show it once, and it remembers. And it "
                 "dreams: it practices in a little simulated world, and "
                 "only keeps a change if it truly got better.",
                 3, colw=1330)
    d = ImageDraw.Draw(img, "RGBA")
    panels = [(108, 620), (570, 620), (1032, 620)]
    pw, ph = 420, 250
    for (x, y) in panels:
        d.rounded_rectangle([x, y, x + pw, y + ph], 36, fill=(24, 30, 64, 235),
                            outline=(150, 168, 255, 120), width=2)
    cy = 712
    cxs = [108 + 210, 570 + 210, 1032 + 210]
    d.ellipse([cxs[0] - 92, cy - 58, cxs[0] + 92, cy + 58], fill=(233, 237, 255))
    d.ellipse([cxs[0] - 38, cy - 38, cxs[0] + 38, cy + 38], fill=(92, 120, 246))
    d.ellipse([cxs[0] - 17, cy - 17, cxs[0] + 17, cy + 17], fill=(10, 13, 30))
    d.ellipse([cxs[0] + 2, cy - 30, cxs[0] + 16, cy - 16], fill=(255, 255, 255))
    hx, hy = cxs[1], cy - 6
    d.ellipse([hx - 62, hy - 56, hx - 2, hy + 4], fill=PINK)
    d.ellipse([hx + 2, hy - 56, hx + 62, hy + 4], fill=PINK)
    d.polygon([(hx - 59, hy - 16), (hx + 59, hy - 16), (hx, hy + 72)], fill=PINK)
    crescent(d, cxs[2] + 14, cy, 62)
    for i, word in enumerate(["WATCH", "TEACH", "DREAM"]):
        wlen = d.textlength(word, font=F_CAP)
        d.text((cxs[i] - wlen / 2, 796), word, font=F_CAP, fill=GOLD_L)
    return img


def slide4():
    img = bg(47)
    img = photo_panel(img, os.path.join(OUT, "src-photo-front.jpg"),
                      (880, 170, 1500, 740),
                      caption="The robot in this photo is real —")
    d = ImageDraw.Draw(img)
    cap2 = "it is right here at this event."
    d.text((886, 792), cap2, font=ImageFont.truetype(REG, 29), fill=GOLD_L)
    return header(img, "It is already alive",
                  "All of this is already running, live, inside one small "
                  "robot — no internet, no cloud. Tonight it dreamed and "
                  "improved by itself, again and again. A person taught it "
                  "something new, and it learned on the spot.", 4, colw=700)


def slide5():
    img = bg(59)
    img = photo_panel(img, os.path.join(ROOT, "..", "odc-in-frame-1800.jpg"),
                      (920, 230, 1480, 710))
    d = ImageDraw.Draw(img, "RGBA")
    crescent(d, 1430, 130, 44)
    return header(img, "The vision",
                  "Any robot can have it: a one-dollar walker, this "
                  "PuppyPi, any body at all. One system, many bodies. The "
                  "intelligence lives inside the robot — where it "
                  "belongs. Robots that dream themselves better.", 5, colw=730)


def main():
    for fn, out in [(slide1, "slide1.jpg"), (slide2, "slide2.jpg"),
                    (slide3, "slide3.jpg"), (slide4, "slide4.jpg"),
                    (slide5, "slide5.jpg")]:
        fn().save(os.path.join(OUT, out), quality=90)
    print("designed slides rebuilt")


if __name__ == "__main__":
    main()

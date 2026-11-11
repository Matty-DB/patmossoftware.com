"""RunFlow coming-soon teaser for Instagram (1080x1350), matching the patmossoftware.com look."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1])
ICON = "/Users/toxic/outside-icloud/running-app/RunFlow/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png"
ROUND = "/System/Library/Fonts/SFNSRounded.ttf"
W, H = 1080, 1350
TOP, BOT = (237, 235, 255), (250, 237, 245)
INK, INK_DARK, MUTED = (92, 82, 158), (63, 55, 111), (113, 106, 145)


def font(size, weight="Heavy"):
    f = ImageFont.truetype(ROUND, size)
    f.set_variation_by_name(weight)
    return f


img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=tuple(round(TOP[i] + (BOT[i] - TOP[i]) * t) for i in range(3)))

# pill label
lab = sys.argv[2] if len(sys.argv) > 2 else "COMING SOON · IPHONE"
lf = font(30, "Black")
lw = d.textlength(lab, font=lf)
d.rounded_rectangle([(W - lw) / 2 - 28, 110, (W + lw) / 2 + 28, 168], 29, fill=(255, 255, 255))
d.text(((W - lw) / 2, 120), lab, font=lf, fill=INK)

# icon with hard shadow
icon = Image.open(ICON).convert("RGBA").resize((300, 300), Image.LANCZOS)
mask = Image.new("L", (300, 300), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, 299, 299], 68, fill=255)
ix, iy = (W - 300) // 2, 230
d.rounded_rectangle([ix, iy + 14, ix + 300, iy + 314], 68, fill=(213, 205, 238))
img.paste(icon, (ix, iy), mask)

# name with pink -> purple gradient
name, nf = "RunFlow", font(150, "Black")
nw = d.textlength(name, font=nf)
x, y = (W - nw) / 2, 575
l, t, r, b = d.textbbox((x, y), name, font=nf)
m = Image.new("L", img.size, 0)
ImageDraw.Draw(m).text((x, y), name, font=nf, fill=255)
g = Image.new("RGB", img.size)
gd = ImageDraw.Draw(g)
c0, c1 = (255, 59, 115), (140, 87, 219)
for yy in range(t, b + 1):
    k = (yy - t) / max(1, b - t)
    gd.line([(l, yy), (r, yy)], fill=tuple(round(c0[i] + (c1[i] - c0[i]) * k) for i in range(3)))
d.text((x, y + 5), name, font=nf, fill=(255, 255, 255))
img.paste(g, (0, 0), m)

for i, line in enumerate(["Running plans that", "grow with you."]):
    f = font(60, "Heavy")
    lw = d.textlength(line, font=f)
    d.text(((W - lw) / 2, 790 + i * 74), line, font=f, fill=INK_DARK)

chips = ["0 to 5K", "5K Speed", "5K to 10K", "Half Marathon", "AI plan import"]
cf = font(34, "Bold")
rows = [chips[:3], chips[3:]]
yy = 1010
for row in rows:
    widths = [d.textlength(c, font=cf) + 56 for c in row]
    total = sum(widths) + 18 * (len(row) - 1)
    xx = (W - total) / 2
    for c, cw in zip(row, widths):
        d.rounded_rectangle([xx, yy + 6, xx + cw, yy + 72], 33, fill=(213, 205, 238))
        d.rounded_rectangle([xx, yy, xx + cw, yy + 66], 33, fill=(255, 255, 255))
        d.text((xx + 28, yy + 13), c, font=cf, fill=INK)
        xx += cw + 18
    yy += 92

foot = "patmossoftware.com"
ff = font(32, "Bold")
fw = d.textlength(foot, font=ff)
d.text(((W - fw) / 2, 1250), foot, font=ff, fill=MUTED)
img.save(OUT / (sys.argv[3] if len(sys.argv) > 3 else "runflow-teaser.png"), "PNG", optimize=True)
print("ok")

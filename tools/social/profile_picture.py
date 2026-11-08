"""Patmos social profile picture (1080x1080): pink sparkle on lavender, reads in a circle crop."""
import sys
from PIL import Image, ImageDraw

S = 1080
img = Image.new("RGB", (S, S))
d = ImageDraw.Draw(img)
top, bot = (237, 235, 255), (250, 237, 245)
for y in range(S):
    t = y / S
    d.line([(0, y), (S, y)], fill=tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)))

# white puffy tile with hard shadow, kept well inside the circle crop
tile = 600
x0 = (S - tile) // 2
y0 = (S - tile) // 2 - 12
d.rounded_rectangle([x0, y0 + 24, x0 + tile, y0 + tile + 24], 150, fill=(213, 205, 238))
d.rounded_rectangle([x0, y0, x0 + tile, y0 + tile], 150, fill=(255, 255, 255))

cx, cy, r = S // 2, y0 + tile // 2, 210
k = 0.32
pts = [(cx, cy - r), (cx + r * k, cy - r * k), (cx + r, cy), (cx + r * k, cy + r * k),
       (cx, cy + r), (cx - r * k, cy + r * k), (cx - r, cy), (cx - r * k, cy - r * k)]
d.polygon(pts, fill=(255, 59, 115))
d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(92, 82, 158))
img.save(sys.argv[1], "PNG", optimize=True)
print("ok")

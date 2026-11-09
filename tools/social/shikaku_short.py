"""Render a vertical Shikaku Short (1080x1920, 30 fps) that solves a puzzle from puzzles.json.

Usage: python3 shikaku_short.py <puzzles.json> <index> <out.mp4>
"""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import shikaku_posts as sp

W, H, FPS = 1080, 1920, 30
sp.W = W  # helpers centre text on sp.W
ICON = Path(__file__).resolve().parents[2] / "assets" / "shikaku-icon.png"
FFMPEG = "ffmpeg"

puzzles = json.loads(Path(sys.argv[1]).read_text())
p = puzzles[int(sys.argv[2])]
OUT = Path(sys.argv[3])

BG = Image.new("RGB", (W, H))
_d = ImageDraw.Draw(BG)
for y in range(H):
    t = y / H
    _d.line([(0, y), (W, y)], fill=tuple(round(sp.BG_TOP[i] + (sp.BG_BOTTOM[i] - sp.BG_TOP[i]) * t) for i in range(3)))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def board(img, shown, pops, solved_glow=0.0):
    """shown: rect indices fully placed; pops: {index: progress 0..1} for the one animating in."""
    d = ImageDraw.Draw(img)
    w, h = p["w"], p["h"]
    size = 860
    cell = size // max(w, h)
    bw, bh = cell * w, cell * h
    ox, oy = (W - bw) // 2, 560 + (size - bh) // 2
    pad = 28
    d.rounded_rectangle([ox - pad, oy - pad + 14, ox + bw + pad, oy + bh + pad + 14], 44, fill=(213, 205, 238))
    edge = tuple(round(255 - (255 - c) * solved_glow) for c in (126, 217, 181))
    d.rounded_rectangle([ox - pad, oy - pad, ox + bw + pad, oy + bh + pad], 44, fill=(255, 255, 255),
                        outline=edge if solved_glow else None, width=10 if solved_glow else 0)
    line = (226, 222, 242)
    for i in range(w + 1):
        d.line([ox + i * cell, oy, ox + i * cell, oy + bh], fill=line, width=3)
    for j in range(h + 1):
        d.line([ox, oy + j * cell, ox + bw, oy + j * cell], fill=line, width=3)
    items = [(i, 1.0) for i in shown] + list(pops.items())
    for i, k in items:
        x, y, rw, rh = p["solution"][i]
        k = ease(k)
        inset = 6 + (1 - k) * cell * 0.35
        x0, y0 = ox + x * cell + inset, oy + y * cell + inset
        x1, y1 = ox + (x + rw) * cell - inset, oy + (y + rh) * cell - inset
        if x1 > x0 and y1 > y0:
            d.rounded_rectangle([x0, y0, x1, y1], 20, fill=sp.FILLS[i % len(sp.FILLS)])
    nf = sp.font(int(cell * .5), "Black")
    for cx, cy, a in p["clues"]:
        t = str(a)
        tw = d.textlength(t, font=nf)
        l, tt, r, bb = d.textbbox((0, 0), t, font=nf)
        d.text((ox + cx * cell + (cell - tw) / 2, oy + cy * cell + (cell - (bb - tt)) / 2 - tt), t,
               font=nf, fill=sp.INK_DARK)


def caption(img, lines, alpha=1.0):
    """Big headline above the board. alpha fades it in."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = 230
    for i, (text, size) in enumerate(lines):
        f = sp.font(size, "Black")
        tw = d.textlength(text, font=f)
        d.text(((W - tw) / 2, y), text, font=f, fill=sp.INK_DARK + (round(255 * alpha),))
        y += size + 22
    img.paste(layer, (0, 0), layer)


def footer(img):
    d = ImageDraw.Draw(img)
    sp.mark(d, 1640)


def end_card(t):
    img = BG.copy()
    d = ImageDraw.Draw(img)
    k = ease(t / 0.6)
    s = round(320 * (0.85 + 0.15 * k))
    icon = Image.open(ICON).convert("RGBA").resize((s, s), Image.LANCZOS)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], round(s * .225), fill=255)
    ix, iy = (W - s) // 2, 560 + (320 - s) // 2
    d.rounded_rectangle([ix, iy + 16, ix + s, iy + s + 16], round(s * .225), fill=(213, 205, 238))
    img.paste(icon, (ix, iy), mask)
    big = sp.font(150, "Black")
    tw = d.textlength("Shikaku", font=big)
    sp.gradient_text(img, ((W - tw) / 2, 960), "Shikaku", big)
    d = ImageDraw.Draw(img)
    sp.centered(d, 1170, "Free on iPhone", sp.font(72, "Heavy"), sp.INK_DARK)
    sp.centered(d, 1270, "Link on the channel", sp.font(44, "Bold"), sp.INK)
    footer(img)
    return img


# timeline (seconds)
n = len(p["solution"])
STEP = 0.7
T_RULE1, T_RULE2, T_SOLVE = 0.0, 1.8, 4.2
T_DONE = T_SOLVE + n * STEP + 0.3
T_END = T_DONE + 2.0
T_TOTAL = T_END + 2.5
order = sorted(range(n), key=lambda i: (p["solution"][i][1], p["solution"][i][0]))

with tempfile.TemporaryDirectory() as tmp:
    for f in range(round(T_TOTAL * FPS)):
        t = f / FPS
        if t >= T_END:
            img = end_card(t - T_END)
        else:
            img = BG.copy()
            shown, pops = [], {}
            if t >= T_SOLVE:
                k = (t - T_SOLVE) / STEP
                done = min(n, int(k))
                shown = order[:done]
                if done < n:
                    pops = {order[done]: k - done}
            glow = ease((t - T_DONE) / 0.4) if t >= T_DONE else 0.0
            board(img, shown, pops, glow)
            if t < T_RULE2:
                caption(img, [("One rule.", 120)], ease(t / 0.4))
            elif t < T_DONE:
                caption(img, [("Every number is", 92), ("its rectangle's size.", 92)], ease((t - T_RULE2) / 0.4))
            else:
                caption(img, [("That's it.", 120), ("Can you solve harder ones?", 64)], ease((t - T_DONE) / 0.4))
            footer(img)
        img.save(f"{tmp}/f{f:04d}.png", compress_level=1)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                    "-f", "lavfi", "-t", str(T_TOTAL), "-i", "anullsrc=r=44100:cl=stereo",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-shortest",
                    "-movflags", "+faststart", str(OUT)], check=True)
print(OUT, f"{T_TOTAL:.1f}s")

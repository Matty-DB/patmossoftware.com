"""Shikaku Short v2: hook-first, timer race, pop sounds (1080x1920, 30 fps, about 10 s).

Changes from v1 after the first Reel's 32% hook rate: headline fully visible on frame 0,
first rectangle lands within 0.5 s, a draining timer bar, shorter, and audio pops.

Usage: python3 shikaku_short_v2.py <puzzles.json> <index> <out.mp4>
"""
import json, math, struct, subprocess, sys, tempfile, wave
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import shikaku_posts as sp

W, H, FPS, SR = 1080, 1920, 30, 44100
sp.W = W
ICON = Path(__file__).resolve().parents[2] / "assets" / "shikaku-icon.png"

p = json.loads(Path(sys.argv[1]).read_text())[int(sys.argv[2])]
OUT = Path(sys.argv[3])
n = len(p["solution"])
order = sorted(range(n), key=lambda i: (p["solution"][i][1], p["solution"][i][0]))

START, STEP, POP = 0.25, 0.95, 0.25
T_SOLVED = START + (n - 1) * STEP + POP
T_END = T_SOLVED + 1.5
T_TOTAL = T_END + 1.6
lands = [START + i * STEP + POP for i in range(n)]

BG = Image.new("RGB", (W, H))
_d = ImageDraw.Draw(BG)
for y in range(H):
    t = y / H
    _d.line([(0, y), (W, y)], fill=tuple(round(sp.BG_TOP[i] + (sp.BG_BOTTOM[i] - sp.BG_TOP[i]) * t) for i in range(3)))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def overshoot(t):
    t = max(0.0, min(1.0, t))
    c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def board(img, t, glow):
    d = ImageDraw.Draw(img)
    w, h = p["w"], p["h"]
    size = 860
    cell = size // max(w, h)
    bw, bh = cell * w, cell * h
    ox, oy = (W - bw) // 2, 600 + (size - bh) // 2
    pad = 28
    d.rounded_rectangle([ox - pad, oy - pad + 14, ox + bw + pad, oy + bh + pad + 14], 44, fill=(213, 205, 238))
    d.rounded_rectangle([ox - pad, oy - pad, ox + bw + pad, oy + bh + pad], 44, fill=(255, 255, 255),
                        outline=(126, 217, 181) if glow else None, width=round(12 * glow) if glow else 0)
    line = (226, 222, 242)
    for i in range(w + 1):
        d.line([ox + i * cell, oy, ox + i * cell, oy + bh], fill=line, width=3)
    for j in range(h + 1):
        d.line([ox, oy + j * cell, ox + bw, oy + j * cell], fill=line, width=3)
    for k, i in enumerate(order):
        prog = (t - (START + k * STEP)) / POP
        if prog <= 0:
            continue
        s = overshoot(prog)
        x, y, rw, rh = p["solution"][i]
        cx, cy = ox + (x + rw / 2) * cell, oy + (y + rh / 2) * cell
        hw, hh = (rw * cell / 2 - 6) * s, (rh * cell / 2 - 6) * s
        if hw > 2 and hh > 2:
            d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], 20, fill=sp.FILLS[i % len(sp.FILLS)])
    nf = sp.font(int(cell * .5), "Black")
    for cx, cy, a in p["clues"]:
        s = str(a)
        tw = d.textlength(s, font=nf)
        l, tt, r, bb = d.textbbox((0, 0), s, font=nf)
        d.text((ox + cx * cell + (cell - tw) / 2, oy + cy * cell + (cell - (bb - tt)) / 2 - tt), s,
               font=nf, fill=sp.INK_DARK)


def headline(img, lines):
    d = ImageDraw.Draw(img)
    y = 210
    for text, size, grad in lines:
        f = sp.font(size, "Black")
        tw = d.textlength(text, font=f)
        if grad:
            sp.gradient_text(img, ((W - tw) / 2, y), text, f)
            d = ImageDraw.Draw(img)
        else:
            d.text(((W - tw) / 2, y), text, font=f, fill=sp.INK_DARK)
        y += size + 18


def timer(img, t):
    d = ImageDraw.Draw(img)
    x0, x1, y0 = 140, W - 140, 500
    left = max(0.0, 1 - t / T_SOLVED)
    d.rounded_rectangle([x0, y0, x1, y0 + 26], 13, fill=(255, 255, 255))
    if left > 0:
        col = sp.PINK if left < 0.3 else (123, 92, 224)
        d.rounded_rectangle([x0, y0, x0 + max(26, (x1 - x0) * left), y0 + 26], 13, fill=col)


def end_card(t):
    img = BG.copy()
    d = ImageDraw.Draw(img)
    k = ease(t / 0.5)
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
    sp.centered(d, 1270, "Search Shikaku Patmos", sp.font(44, "Bold"), sp.INK)
    sp.mark(d, 1640)
    return img


def audio(path):
    """Soft rising pop on each landing, a brighter chime when solved. Quiet so music can sit on top."""
    total = int(T_TOTAL * SR)
    buf = [0.0] * total

    def tone(at, freq, dur, vol, decay):
        s0 = int(at * SR)
        for j in range(int(dur * SR)):
            if s0 + j >= total:
                break
            tt = j / SR
            env = math.exp(-tt * decay) * min(1.0, tt * 400)
            buf[s0 + j] += vol * env * math.sin(2 * math.pi * freq * tt * (1 + 0.6 * math.exp(-tt * 60)))

    for k, at in enumerate(lands):
        tone(at - 0.03, 520 * 2 ** (k / 12 * 2), 0.18, 0.35, 28)
    for f in (784, 988, 1175):
        tone(T_SOLVED + 0.05, f, 0.9, 0.18, 5)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(v * 32767)))) for v in buf))


with tempfile.TemporaryDirectory() as tmp:
    for f in range(round(T_TOTAL * FPS)):
        t = f / FPS
        if t >= T_END:
            img = end_card(t - T_END)
        else:
            img = BG.copy()
            glow = ease((t - T_SOLVED) / 0.3) if t >= T_SOLVED else 0.0
            board(img, t, glow)
            if t < T_SOLVED:
                headline(img, [("Can you beat", 104, True), ("the timer?", 104, False)])
                timer(img, t)
            else:
                headline(img, [("Solved.", 120, True), ("Did you beat it?", 76, False)])
            sp.mark(ImageDraw.Draw(img), 1640)
        img.save(f"{tmp}/f{f:04d}.png", compress_level=1)
    audio(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                    "-i", f"{tmp}/a.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(OUT)], check=True)
print(OUT, f"{T_TOTAL:.1f}s")

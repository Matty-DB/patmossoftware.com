"""RunFlow launch Short (1080x1920, 30 fps, about 10 s): hook on frame 0, plan path lights up, pops.

Usage: python3 runflow_short.py <out.mp4>
"""
import math, struct, subprocess, sys, tempfile, wave
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import shikaku_posts as sp

W, H, FPS, SR = 1080, 1920, 30, 44100
sp.W = W
ICON = Path(__file__).resolve().parents[2] / "assets" / "runflow-icon.png"
OUT = Path(sys.argv[1])
PINK, PURPLE = (255, 59, 115), (140, 87, 219)
GREEN = (107, 199, 64)

STEPS = [("0 to 5K", "From no running at all"), ("5K Speed", "Get faster"), ("Zone 2 Base", "Build endurance"),
         ("5K to 10K", "Eight weeks"), ("Half Marathon", "21.1 km")]
START, STEP = 0.35, 1.0
T_PATH_DONE = START + len(STEPS) * STEP
T_END = T_PATH_DONE + 0.9
T_TOTAL = T_END + 2.4

BG = Image.new("RGB", (W, H))
_d = ImageDraw.Draw(BG)
for y in range(H):
    t = y / H
    _d.line([(0, y), (W, y)], fill=tuple(round(sp.BG_TOP[i] + (sp.BG_BOTTOM[i] - sp.BG_TOP[i]) * t) for i in range(3)))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def grad_text(img, xy, text, f, c0=PINK, c1=PURPLE):
    d = ImageDraw.Draw(img)
    l, t, r, b = d.textbbox(xy, text, font=f)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).text(xy, text, font=f, fill=255)
    g = Image.new("RGB", img.size)
    gd = ImageDraw.Draw(g)
    for yy in range(t, b + 1):
        k = (yy - t) / max(1, b - t)
        gd.line([(l, yy), (r, yy)], fill=tuple(round(c0[i] + (c1[i] - c0[i]) * k) for i in range(3)))
    d.text((xy[0], xy[1] + 5), text, font=f, fill=(255, 255, 255))
    img.paste(g, (0, 0), m)


def headline(img):
    d = ImageDraw.Draw(img)
    f1, f2 = sp.font(100, "Black"), sp.font(100, "Black")
    a, b = "Never run before?", "Start here."
    grad_text(img, ((W - d.textlength(a, font=f1)) / 2, 200), a, f1)
    d = ImageDraw.Draw(img)
    d.text(((W - d.textlength(b, font=f2)) / 2, 320), b, font=f2, fill=sp.INK_DARK)


def path(img, t):
    d = ImageDraw.Draw(img)
    x_line, y0, gap = 210, 540, 200
    ys = [y0 + i * gap for i in range(len(STEPS))]
    # track
    d.rounded_rectangle([x_line - 9, ys[0], x_line + 9, ys[-1]], 9, fill=(225, 220, 245))
    prog = max(0.0, min(len(STEPS) - 1, (t - START) / STEP))
    fill_to = ys[0] + (ys[-1] - ys[0]) * prog / (len(STEPS) - 1)
    if t > START:
        d.rounded_rectangle([x_line - 9, ys[0], x_line + 9, fill_to], 9, fill=PINK)
    nf, sf = sp.font(64, "Black"), sp.font(38, "Bold")
    for i, (name, sub) in enumerate(STEPS):
        k = ease((t - (START + i * STEP)) / 0.3)
        y = ys[i]
        r = 34 + 8 * k * (1 - ease((t - (START + i * STEP) - 0.3) / 0.3)) if k > 0 else 34
        d.ellipse([x_line - r, y - r, x_line + r, y + r], fill=GREEN if k >= 1 else ((255, 255, 255) if k == 0 else PINK),
                  outline=(213, 205, 238), width=6)
        if k >= 1:
            d.line([(x_line - 13, y + 1), (x_line - 3, y + 12), (x_line + 15, y - 11)], fill=(255, 255, 255), width=9)
        col = sp.INK_DARK if k > 0 else (190, 184, 214)
        card_x = x_line + 80 + round(30 * (1 - k))
        d.text((card_x, y - 58), name, font=nf, fill=col)
        d.text((card_x, y + 16), sub, font=sf, fill=sp.INK if k > 0 else (205, 200, 226))


def end_card(t):
    img = BG.copy()
    d = ImageDraw.Draw(img)
    k = ease(t / 0.5)
    s = round(320 * (0.85 + 0.15 * k))
    icon = Image.open(ICON).convert("RGBA").resize((s, s), Image.LANCZOS)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], round(s * .225), fill=255)
    ix, iy = (W - s) // 2, 520 + (320 - s) // 2
    d.rounded_rectangle([ix, iy + 16, ix + s, iy + s + 16], round(s * .225), fill=(213, 205, 238))
    img.paste(icon, (ix, iy), mask)
    f = sp.font(160, "Black")
    grad_text(img, ((W - d.textlength("RunFlow", font=f)) / 2, 900), "RunFlow", f)
    d = ImageDraw.Draw(img)
    sp.centered(d, 1120, "Couch to 5K, then keep going.", sp.font(56, "Heavy"), sp.INK_DARK)
    sp.centered(d, 1210, "Free on iPhone · link in bio", sp.font(46, "Bold"), sp.INK)
    return img


def audio(path):
    total = int(T_TOTAL * SR)
    buf = [0.0] * total

    def tone(at, freq, dur, vol, decay):
        s0 = int(at * SR)
        for j in range(int(dur * SR)):
            if s0 + j >= total:
                break
            tt = j / SR
            env = math.exp(-tt * decay) * min(1.0, tt * 400)
            buf[s0 + j] += vol * env * math.sin(2 * math.pi * freq * tt * (1 + 0.5 * math.exp(-tt * 60)))

    for i in range(len(STEPS)):
        tone(START + i * STEP + 0.25, 523 * 2 ** ([0, 2, 4, 7, 9][i] / 12), 0.25, 0.35, 22)
    for f in (784, 988, 1175, 1568):
        tone(T_PATH_DONE + 0.1, f, 1.0, 0.14, 4)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(v * 32767)))) for v in buf))


with tempfile.TemporaryDirectory() as tmp:
    for fno in range(round(T_TOTAL * FPS)):
        t = fno / FPS
        if t >= T_END:
            img = end_card(t - T_END)
        else:
            img = BG.copy()
            headline(img)
            path(img, t)
        sp.mark(ImageDraw.Draw(img), 1640, "app")
        img.save(f"{tmp}/f{fno:04d}.png", compress_level=1)
    audio(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                    "-i", f"{tmp}/a.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(OUT)], check=True)
print(OUT, f"{T_TOTAL:.1f}s")

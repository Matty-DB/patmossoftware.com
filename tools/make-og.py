#!/usr/bin/env python3
"""
Generate the Open Graph preview images.

    python3 tools/make-og.py

Writes /og.png (site-wide default) and /shikaku/og.png (the app page and the
blog). Both are 1200x630, which is what Facebook, Twitter/X, LinkedIn, Slack,
Discord and iMessage all expect.

These were referenced in every page's <head> long before they existed, so any
link shared anywhere previewed as a blank rectangle. Regenerate after changing
the palette or the mark.

Everything is drawn at 4x and downsampled, because PIL has no antialiasing on
primitives and the mark's thin strokes alias badly at final size.
"""

from PIL import Image, ImageChops, ImageDraw, ImageFont

W, H, SS = 1200, 630, 4

BG = (10, 15, 22)
BG_END = (6, 10, 15)
INK = (238, 243, 248)
MUTED = (142, 163, 181)
GOLD = (201, 162, 39)
SEA = (95, 127, 150)

SERIF = "/System/Library/Fonts/Supplemental/Iowan Old Style.ttc"
SANS = "/System/Library/Fonts/Supplemental/Verdana.ttf"


def font(path, size, index=0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except OSError:
        return ImageFont.load_default(size)


def backdrop():
    """Vertical gradient plus the gold horizon glow from the site's CSS."""
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)
    for y in range(H * SS):
        t = y / (H * SS)
        d.line(
            [(0, y), (W * SS, y)],
            fill=tuple(round(BG[i] + (BG_END[i] - BG[i]) * t) for i in range(3)),
        )

    glow = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy, r = W * SS // 2, int(H * SS * 1.08), int(W * SS * 0.62)
    steps = 90
    for i in range(steps, 0, -1):
        f = i / steps
        rr = int(r * f)
        v = int(46 * (1 - f) ** 1.7)
        gd.ellipse([cx - rr, cy - int(rr * 0.62), cx + rr, cy + int(rr * 0.62)],
                   fill=(int(v * 0.86), int(v * 0.72), int(v * 0.22)))

    return ImageChops.add(img, glow)


def tracked(d, xy, text, fnt, fill, tracking):
    """Draw text with letter-spacing. PIL has no native tracking."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + tracking
    return x


def tracked_width(d, text, fnt, tracking):
    return sum(d.textlength(c, font=fnt) for c in text) + tracking * (len(text) - 1)


def mark(d, cx, cy, size):
    """The Patmos mark: sun over a horizon. Mirrors the inline SVG on the site."""
    s = size / 64
    r = 11 * s
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=max(1, round(1.75 * s)))
    r2 = 4 * s
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=GOLD)
    y1 = cy + 20 * s
    d.line([cx - 24 * s, y1, cx + 24 * s, y1], fill=SEA, width=max(1, round(1.75 * s)))
    y2 = cy + 26 * s
    d.line([cx - 18 * s, y2, cx + 2 * s, y2], fill=SEA, width=max(1, round(1.5 * s)))
    d.line([cx + 6 * s, y2, cx + 18 * s, y2], fill=SEA, width=max(1, round(1.5 * s)))


def rule(d, cx, y, width, thickness=2):
    """The site's gold-centred hairline."""
    half = width // 2
    for i in range(-half, half):
        t = 1 - abs(i) / half
        v = t ** 1.6
        col = tuple(round(SEA[c] * 0.35 + (GOLD[c] - SEA[c] * 0.35) * v) for c in range(3))
        a = 0.25 + 0.75 * v
        col = tuple(round(BG[c] + (col[c] - BG[c]) * a) for c in range(3))
        d.line([cx + i, y, cx + i, y + thickness], fill=col)


def site_og(path):
    img = backdrop()
    d = ImageDraw.Draw(img)
    f_title = font(SERIF, 78 * SS)
    f_tag = font(SANS, 25 * SS)

    mark(d, W * SS // 2, 208 * SS, 128 * SS)

    tr = 11 * SS
    title = "PATMOS SOFTWARE"
    x = (W * SS - tracked_width(d, title, f_title, tr)) / 2
    tracked(d, (x, 300 * SS), title, f_title, INK, tr)

    rule(d, W * SS // 2, 425 * SS, 300 * SS, 2 * SS)

    tag = "An app development studio"
    d.text(((W * SS - d.textlength(tag, font=f_tag)) / 2, 460 * SS), tag,
           font=f_tag, fill=MUTED)

    img.resize((W, H), Image.LANCZOS).save(path, "PNG", optimize=True)
    return path


def board(d, ox, oy, cell, n=5):
    """A small Shikaku board: faint grid, three solved rectangles, their clues."""
    faint = tuple(round(BG[i] + (SEA[i] - BG[i]) * 0.30) for i in range(3))
    for i in range(n + 1):
        d.line([ox, oy + i * cell, ox + n * cell, oy + i * cell], fill=faint, width=max(1, SS))
        d.line([ox + i * cell, oy, ox + i * cell, oy + n * cell], fill=faint, width=max(1, SS))

    # (col, row, w, h, clue-col, clue-row)
    #
    # These MUST tile the board exactly: 10 + 9 + 6 = 25. An image that shows
    # uncovered squares next to the words "cover the whole grid" is the first
    # thing a pencil-puzzle reader will notice, and they will be right.
    rects = [(0, 0, 2, 5, 0, 2), (2, 0, 3, 3, 3, 1), (2, 3, 3, 2, 3, 4)]
    assert sum(w * h for _, _, w, h, _, _ in rects) == n * n
    for cx0, cy0, w, h, qx, qy in rects:
        x0, y0 = ox + cx0 * cell, oy + cy0 * cell
        d.rectangle([x0, y0, x0 + w * cell, y0 + h * cell], outline=GOLD, width=max(1, round(2.5 * SS)))

    f = font(SANS, round(cell * 0.42))
    for cx0, cy0, w, h, qx, qy in rects:
        label = str(w * h)
        tx = ox + qx * cell + cell / 2 - d.textlength(label, font=f) / 2
        ty = oy + qy * cell + cell / 2 - f.size * 0.62
        d.text((tx, ty), label, font=f, fill=INK)


def shikaku_og(path):
    img = backdrop()
    d = ImageDraw.Draw(img)
    f_title = font(SERIF, 92 * SS)
    f_tag = font(SANS, 27 * SS)
    f_by = font(SANS, 19 * SS)

    cell = 62 * SS
    board(d, 128 * SS, (H * SS - 5 * cell) // 2, cell)

    left = 128 * SS + 5 * cell + 92 * SS
    tr = 13 * SS
    tracked(d, (left, 208 * SS), "SHIKAKU", f_title, INK, tr)
    d.text((left, 330 * SS), "Split the grid into rectangles.", font=f_tag, fill=MUTED)
    d.text((left, 372 * SS), "Every rectangle holds one number,", font=f_tag, fill=MUTED)
    d.text((left, 414 * SS), "and that number is its size.", font=f_tag, fill=MUTED)

    d.line([left, 470 * SS, left + 120 * SS, 470 * SS], fill=GOLD, width=2 * SS)
    d.text((left, 492 * SS), "PATMOS SOFTWARE", font=f_by, fill=SEA)

    img.resize((W, H), Image.LANCZOS).save(path, "PNG", optimize=True)
    return path


if __name__ == "__main__":
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in (site_og(os.path.join(root, "og.png")),
              shikaku_og(os.path.join(root, "shikaku", "og.png"))):
        print(f"{os.path.relpath(p, root):20} {os.path.getsize(p) / 1024:.0f} KB")

#!/usr/bin/env python3
"""
Genera assets/icon.png e assets/icon.icns per Images Grid Split.
Esegui: python make_icon.py
Richiede: Pillow
"""

import struct
from pathlib import Path

from PIL import Image, ImageDraw

# ── parametri icona ─────────────────────────────────────────────────────────
SIZE = 1024
CORNER = 220  # raggio angoli
BG_TOP = (18, 18, 24)
BG_BOT = (28, 34, 48)
ACCENT = (46, 204, 113)  # verde
ACCENT2 = (52, 152, 219)  # blu
GRID_LINE = (255, 255, 255, 40)
CELL_ALPHA = 180


def _round_rect_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
    return mask


def make_icon(size: int = SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── sfondo sfumato ──────────────────────────────────────────────────────
    for y in range(size):
        t = y / size
        r = int(BG_TOP[0] * (1 - t) + BG_BOT[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOT[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOT[2] * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # ── griglia 2×2 visiva ──────────────────────────────────────────────────
    margin = int(size * 0.13)
    grid_size = size - 2 * margin
    half = grid_size // 2
    gap = int(size * 0.025)

    cells = [
        (margin, margin, margin + half - gap, margin + half - gap),
        (margin + half + gap, margin, margin + grid_size, margin + half - gap),
        (margin, margin + half + gap, margin + half - gap, margin + grid_size),
        (
            margin + half + gap,
            margin + half + gap,
            margin + grid_size,
            margin + grid_size,
        ),
    ]

    # colori celle con leggera variazione
    cell_colors = [
        (*ACCENT, CELL_ALPHA),
        (*ACCENT2, CELL_ALPHA),
        (*ACCENT2, CELL_ALPHA),
        (*ACCENT, CELL_ALPHA),
    ]

    for (x0, y0, x1, y1), color in zip(cells, cell_colors):
        cr = int(size * 0.04)
        cell_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        cd = ImageDraw.Draw(cell_layer)
        cd.rounded_rectangle([(x0, y0), (x1, y1)], radius=cr, fill=color)
        img = Image.alpha_composite(img, cell_layer)

    # ── freccia "split" al centro ───────────────────────────────────────────
    draw2 = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    ar = int(size * 0.07)  # raggio frecce
    lw = int(size * 0.025)  # spessore

    # 4 frecce diagonali che puntano agli angoli
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        x0 = cx + dx * int(ar * 0.15)
        y0 = cy + dy * int(ar * 0.15)
        x1 = cx + dx * ar
        y1 = cy + dy * ar
        draw2.line([(x0, y0), (x1, y1)], fill=(255, 255, 255, 240), width=lw)
        # punta
        head = int(lw * 1.6)
        px, py = x1, y1
        draw2.ellipse(
            [(px - head // 2, py - head // 2), (px + head // 2, py + head // 2)],
            fill=(255, 255, 255, 255),
        )

    # ── maschera angoli arrotondati ─────────────────────────────────────────
    mask = _round_rect_mask(size, CORNER)
    img.putalpha(mask)

    return img


# ── salvataggio PNG multi-size → ICNS manuale ────────────────────────────────


def _png_bytes(img: Image.Image) -> bytes:
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


ICNS_TYPES = {
    16: b"icp4",
    32: b"icp5",
    64: b"icp6",
    128: b"ic07",
    256: b"ic08",
    512: b"ic09",
    1024: b"ic10",
}


def make_icns(icon_1024: Image.Image, dest: Path) -> None:
    chunks = []
    for px, tag in ICNS_TYPES.items():
        resized = icon_1024.resize((px, px), Image.LANCZOS)
        data = _png_bytes(resized)
        # each ICNS entry: 4-byte type + 4-byte length (includes header) + data
        length = 8 + len(data)
        chunks.append(tag + struct.pack(">I", length) + data)

    body = b"".join(chunks)
    total = 8 + len(body)
    with open(dest, "wb") as f:
        f.write(b"icns" + struct.pack(">I", total) + body)


# ── main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    assets = Path(__file__).parent / "assets"
    assets.mkdir(exist_ok=True)

    icon = make_icon()

    png_path = assets / "icon.png"
    icon.save(png_path)
    print(f"✓  {png_path}")

    icns_path = assets / "icon.icns"
    make_icns(icon, icns_path)
    print(f"✓  {icns_path}")


if __name__ == "__main__":
    main()

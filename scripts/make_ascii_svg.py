"""Step 3b: convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each row is revealed by a left-to-right clip wipe with a block cursor riding
the edge, staggered top to bottom. Plays once, then freezes (SMIL, which
GitHub renders inside <img>).

Usage:  python scripts/make_ascii_svg.py [--cols 100] [--out ascii-portrait.svg]
        STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for previews
"""
import argparse
import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears background

FONT_SIZE = 10
CHAR_W = FONT_SIZE * 0.6   # monospace advance width
LINE_H = FONT_SIZE * 1.12
PAD = 14
FG = "#c9d1d9"             # one light-gray fill: monochrome looks clean, colour looks like static
BG = "#0d1117"
ROW_DUR = 0.35             # seconds to wipe one row
ROW_GAP = 0.06             # stagger between rows


def to_grid(img: Image.Image, cols: int) -> list[str]:
    img = ImageEnhance.Contrast(img.convert("L")).enhance(1.15)
    w, h = img.size
    # characters are ~2x taller than wide, so squash rows
    rows = max(1, round(h / w * cols * (CHAR_W / LINE_H)))
    small = np.array(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    idx = ((1.0 - small) * (len(RAMP) - 1)).round().astype(int)
    lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]
    # trim blank rows top and bottom
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def build_svg(lines: list[str], static: bool) -> str:
    cols = max(len(l) for l in lines)
    width = round(cols * CHAR_W + PAD * 2)
    height = round(len(lines) * LINE_H + PAD * 2)
    full_w = cols * CHAR_W

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="ASCII portrait">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        "<defs>",
    ]
    for i in range(len(lines)):
        y = PAD + i * LINE_H
        begin = i * ROW_GAP
        if static:
            out.append(f'<clipPath id="r{i}"><rect x="{PAD}" y="{y:.1f}" width="{full_w:.1f}" height="{LINE_H:.1f}"/></clipPath>')
        else:
            out.append(
                f'<clipPath id="r{i}"><rect x="{PAD}" y="{y:.1f}" width="0" height="{LINE_H:.1f}">'
                f'<animate attributeName="width" from="0" to="{full_w:.1f}" begin="{begin:.2f}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
            )
    out.append("</defs>")
    out.append(
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace" '
        f'font-size="{FONT_SIZE}" fill="{FG}" xml:space="preserve">'
    )
    for i, line in enumerate(lines):
        if not line:
            continue
        base = PAD + i * LINE_H + FONT_SIZE * 0.85
        out.append(
            f'<text x="{PAD}" y="{base:.1f}" clip-path="url(#r{i})" '
            f'textLength="{len(line) * CHAR_W:.1f}" lengthAdjust="spacing">{escape(line)}</text>'
        )
    out.append("</g>")

    if not static:
        # block cursor that rides each wipe edge, then hides
        out.append(f'<rect x="{PAD}" y="{PAD}" width="{CHAR_W:.1f}" height="{LINE_H:.1f}" fill="{FG}" opacity="0">')
        for i in range(len(lines)):
            y = PAD + i * LINE_H
            begin = i * ROW_GAP
            out.append(f'<set attributeName="y" to="{y:.1f}" begin="{begin:.2f}s"/>')
            out.append(
                f'<animate attributeName="x" from="{PAD}" to="{PAD + full_w:.1f}" '
                f'begin="{begin:.2f}s" dur="{ROW_DUR}s"/>'
            )
        end = (len(lines) - 1) * ROW_GAP + ROW_DUR
        out.append('<set attributeName="opacity" to="0.85" begin="0s"/>')
        out.append(f'<set attributeName="opacity" to="0" begin="{end:.2f}s"/>')
        out.append("</rect>")

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=str(ROOT / "ascii-portrait.svg"))
    args = ap.parse_args()

    lines = to_grid(Image.open(args.src), args.cols)
    svg = build_svg(lines, static=os.environ.get("STATIC") == "1")
    Path(args.out).write_text(svg, encoding="utf-8")
    print(f"wrote {Path(args.out).name} ({len(lines)} rows x {args.cols} cols)")


if __name__ == "__main__":
    main()

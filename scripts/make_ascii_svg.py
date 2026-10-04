"""Step 3b: convert source-prepped.png into a self-typing ASCII SVG.

Default "terminal" style: each glyph is shaded dim-to-bright green by its
brightness (matching the contribution graph), a soft phosphor glow, faint CRT scanlines, a title bar that matches
the info card, a one-time scan sweep and a blinking prompt at the end.
Every row types itself in left to right with a block cursor, then freezes
(SMIL + CSS inside the SVG, which GitHub plays inside <img>).

Usage:  python scripts/make_ascii_svg.py [--cols 76] [--out ascii-portrait.svg]
        python scripts/make_ascii_svg.py --mono      # plain blog style
        STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for previews
"""
import argparse
import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"

RAMP = " .'`^,:;Il!i~+_-?]}1)|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@"  # sparse -> dense
def _ramp(c0, c1, c2, n):
    """n colours from c0 through c1 to c2 (dark green -> green -> mint white)."""
    h = lambda c: [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    a, b, c = h(c0), h(c1), h(c2)
    out = []
    for k in range(n):
        t = k / (n - 1)
        p, q, u = (a, b, t * 2) if t < 0.5 else (b, c, t * 2 - 1)
        out.append("#" + "".join(f"{round(p[i] + (q[i] - p[i]) * u):02x}" for i in range(3)))
    return out


SHADES = _ramp("#123d24", "#2ea043", "#effff4", 10)  # glyph colour follows brightness

FONT_SIZE = 10
CHAR_W = FONT_SIZE * 0.6    # monospace advance width
LINE_H = FONT_SIZE * 1.12
PAD = 16
BAR = 28                    # title bar height (terminal style)
FOOT = 24                   # prompt line height (terminal style)
BG = "#0d1117"
BORDER = "#30363d"
DIM = "#8b949e"
MONO_FG = "#c9d1d9"
ROW_DUR = 0.35
GAMMA = 1.25               # >1 deepens shadows so highlights (face) pop
FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace"


def to_grid(img: Image.Image, cols: int, negative: bool) -> list[str]:
    """Light-on-dark by default: bright pixels -> dense glyphs, so the picture
    reads like the photo on a dark background. --negative gives the blog's
    dark -> dense mapping (best on a light background)."""
    img = img.convert("LA")
    w, h = img.size
    rows = max(1, round(h / w * cols * (CHAR_W / LINE_H)))
    small = np.array(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    lum, alpha = small[:, :, 0], small[:, :, 1]

    # stretch the subject's own tonal range so the ramp is fully used
    subj = lum[alpha > 0.5]
    if subj.size:
        lo, hi = np.percentile(subj, [3, 97])
        lum = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
    tone = (1.0 - lum) if negative else lum
    tone = tone ** GAMMA

    idx = 1 + np.round(tone * (len(RAMP) - 2)).astype(int)  # subject never blank
    idx[alpha < 0.5] = 0                                      # background blank
    shade = np.minimum((tone * len(SHADES)).astype(int), len(SHADES) - 1)
    rows_out = []
    for r in range(idx.shape[0]):
        line = "".join(RAMP[i] for i in idx[r]).rstrip()
        rows_out.append((line, list(shade[r][: len(line)])))
    while rows_out and not rows_out[0][0].strip():
        rows_out.pop(0)
    while rows_out and not rows_out[-1][0].strip():
        rows_out.pop()
    return rows_out


def nb(t: str) -> str:
    # non-breaking spaces: browsers collapse runs of normal spaces even with xml:space
    return escape(t).replace(" ", "&#160;")


def coloured(line: str, shades: list) -> str:
    """Group runs of equal shade into tspans; spaces join the current run."""
    out, run, cur = [], "", None
    for ch, sh in zip(line, shades):
        if ch == " " or sh == cur:
            run += ch
            continue
        if run:
            out.append(f'<tspan fill="{SHADES[cur]}">{nb(run)}</tspan>' if cur is not None else nb(run))
        run, cur = ch, sh
    if run:
        out.append(f'<tspan fill="{SHADES[cur]}">{nb(run)}</tspan>' if cur is not None else nb(run))
    return "".join(out)


def text_rows(rows, x0, y0, clip_prefix=None, colour=False):
    out = []
    for i, (line, shades) in enumerate(rows):
        if not line:
            continue
        y = y0 + i * LINE_H + FONT_SIZE * 0.85
        clip = f' clip-path="url(#{clip_prefix}{i})"' if clip_prefix else ""
        body = coloured(line, shades) if colour else nb(line)
        out.append(
            f'<text x="{x0}" y="{y:.1f}"{clip} textLength="{len(line) * CHAR_W:.1f}" '
            f'lengthAdjust="spacing">{body}</text>'
        )
    return out


def build_mono(lines, static):
    cols = max(len(l) for l, _ in lines)
    width = round(cols * CHAR_W + PAD * 2)
    height = round(len(lines) * LINE_H + PAD * 2)
    full_w = cols * CHAR_W
    gap = min(0.06, 2.4 / len(lines))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'width="{width}" height="{height}" role="img" aria-label="ASCII portrait">',
           f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>', "<defs>"]
    for i in range(len(lines)):
        out.append(clip_rect(i, PAD, PAD + i * LINE_H, full_w, i * gap, static))
    out.append("</defs>")
    out.append(f'<g font-family="{FAMILY}" font-size="{FONT_SIZE}" fill="{MONO_FG}" xml:space="preserve">')
    out += text_rows(lines, PAD, PAD, "r")
    out.append("</g>")
    if not static:
        out += cursor(lines, PAD, PAD, full_w, gap, MONO_FG)
    out.append("</svg>")
    return "\n".join(out)


def clip_rect(i, x, y, full_w, begin, static, row_dur=ROW_DUR):
    if static:
        return f'<clipPath id="r{i}"><rect x="{x}" y="{y:.1f}" width="{full_w:.1f}" height="{LINE_H:.1f}"/></clipPath>'
    return (f'<clipPath id="r{i}"><rect x="{x}" y="{y:.1f}" width="0" height="{LINE_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{full_w:.1f}" begin="{begin:.2f}s" '
            f'dur="{row_dur}s" fill="freeze"/></rect></clipPath>')


def cursor(lines, x0, y0, full_w, gap, colour, row_dur=ROW_DUR, delay=0.0):
    out = [f'<rect x="{x0}" y="{y0}" width="{CHAR_W:.1f}" height="{LINE_H:.1f}" fill="{colour}" opacity="0">']
    for i in range(len(lines)):
        begin = delay + i * gap
        out.append(f'<set attributeName="y" to="{y0 + i * LINE_H:.1f}" begin="{begin:.2f}s"/>')
        out.append(f'<animate attributeName="x" from="{x0}" to="{x0 + full_w:.1f}" begin="{begin:.2f}s" dur="{row_dur}s"/>')
    end = delay + (len(lines) - 1) * gap + row_dur
    out.append('<set attributeName="opacity" to="0.9" begin="0s"/>')
    out.append(f'<set attributeName="opacity" to="0" begin="{end:.2f}s"/>')
    out.append("</rect>")
    return out


def build_terminal(lines, static, title, prompt, type_time=2.4, row_dur=ROW_DUR, delay=0.0, ghost=False,
                   bg=BG, aspect=None):
    """type_time: seconds from first to last row starting; row_dur: seconds each
    row takes to type; delay: pause (cursor blinking) before typing starts;
    ghost: show a faint preview of the whole portrait while it types in."""
    cols = max(len(l) for l, _ in lines)
    full_w = cols * CHAR_W
    art_h = len(lines) * LINE_H
    H = round(BAR + PAD + art_h + PAD + FOOT)
    pad_x = PAD
    if aspect:  # widen with side margins so the panel has this height/width ratio
        pad_x = max(PAD, (H / aspect - full_w) / 2)
    W = round(full_w + pad_x * 2)
    x0, y0 = round(pad_x, 1), BAR + PAD
    gap = type_time / max(len(lines) - 1, 1)
    end = delay + (len(lines) - 1) * gap + row_dur

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="ASCII portrait">',
        "<style>.blink{animation:b 1.1s steps(1) infinite}@keyframes b{50%{opacity:0}}</style>",
        "<defs>",
        '<filter id="glow" x="-5%" y="-5%" width="110%" height="110%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="1.2" result="b"/>'
        '<feColorMatrix in="b" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.45 0" result="g"/>'
        '<feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#000" opacity="0.16"/></pattern>',
        f'<linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#39d353" stop-opacity="0"/>'
        f'<stop offset="0.5" stop-color="#39d353" stop-opacity="0.10"/>'
        f'<stop offset="1" stop-color="#39d353" stop-opacity="0"/></linearGradient>',
        f'<clipPath id="frame"><rect x="1" y="{BAR}" width="{W - 2}" height="{H - BAR - 1}" rx="9"/></clipPath>',
    ]
    for i in range(len(lines)):
        out.append(clip_rect(i, x0, y0 + i * LINE_H, full_w, delay + i * gap, static, row_dur))
    out.append("</defs>")

    # frame + title bar, matching the info card
    out += [
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{bg}" stroke="{BORDER}"/>',
        f'<path d="M0.5 10.5 a10 10 0 0 1 10 -10 h{W - 21} a10 10 0 0 1 10 10 v18 h-{W - 1} z" fill="#161b22"/>',
        f'<line x1="0.5" y1="28.5" x2="{W - 0.5}" y2="28.5" stroke="{BORDER}"/>',
        '<circle cx="16" cy="14.5" r="5" fill="#f85149"/>',
        '<circle cx="32" cy="14.5" r="5" fill="#d29922"/>',
        '<circle cx="48" cy="14.5" r="5" fill="#39d353"/>',
        f'<text x="{W / 2:.0f}" y="18.5" text-anchor="middle" font-family="{FAMILY}" font-size="11" fill="{DIM}">{escape(title)}</text>',
    ]

    # optional ghost: the whole portrait faintly visible, fading out once typed
    if ghost and not static:
        out.append(f'<g font-family="{FAMILY}" font-size="{FONT_SIZE}" fill="{SHADES[2]}" xml:space="preserve" opacity="0">'
                   f'<animate attributeName="opacity" values="0;0.14;0.14;0" keyTimes="0;0.15;0.85;1" '
                   f'dur="{end + 0.6:.2f}s" fill="freeze"/>')
        out += text_rows(lines, x0, y0, None, colour=True)
        out.append("</g>")

    # the portrait, brightening slightly once fully printed
    bright = "" if static else (f' opacity="0.82"><animate attributeName="opacity" from="0.82" to="1" '
                                f'begin="{end:.2f}s" dur="1.2s" fill="freeze"/')
    out.append(f'<g font-family="{FAMILY}" font-size="{FONT_SIZE}" fill="{SHADES[2]}" filter="url(#glow)" xml:space="preserve"{bright}>')
    out += text_rows(lines, x0, y0, "r", colour=True)
    out.append("</g>")

    # CRT scanlines + one sweep after printing
    out.append(f'<g clip-path="url(#frame)">')
    out.append(f'<rect x="0" y="{BAR}" width="{W}" height="{H - BAR}" fill="url(#scan)"/>')
    if not static:
        out.append(
            f'<rect x="0" y="{BAR - 60}" width="{W}" height="60" fill="url(#sweep)" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{end:.2f}s"/>'
            f'<animate attributeName="y" from="{BAR - 60}" to="{H}" begin="{end:.2f}s" dur="{max(1.4, row_dur * 2.5):.1f}s" fill="freeze"/>'
            f'</rect>'
        )
    out.append("</g>")

    if not static:
        out += cursor(lines, x0, y0, full_w, gap, "#69f0a0", row_dur, delay)

    # prompt line with a blinking cursor
    py = H - 10
    fade = "" if static else f' opacity="0"><set attributeName="opacity" to="1" begin="{end:.2f}s"/'
    out.append(f'<g font-family="{FAMILY}" font-size="11"{fade}>')
    out.append(f'<text x="{x0}" y="{py}"><tspan fill="#39d353">{escape(prompt)}</tspan></text>')
    cx = x0 + len(prompt) * 6.6 + 4
    blink = "" if static else ' class="blink"'
    out.append(f'<rect{blink} x="{cx:.1f}" y="{py - 9}" width="7" height="11" fill="#69f0a0"/>')
    out.append("</g>")

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cols", type=int, default=80)
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=str(ROOT / "ascii-portrait.svg"))
    ap.add_argument("--mono", action="store_true", help="plain one-colour style from the blog")
    ap.add_argument("--negative", action="store_true", help="dark pixels -> dense glyphs")
    ap.add_argument("--title", default="~/portrait.ascii")
    ap.add_argument("--prompt", default="deepak@dublin:~$")
    ap.add_argument("--type-time", type=float, default=7.0, help="seconds for all rows to start typing")
    ap.add_argument("--row-dur", type=float, default=0.8, help="seconds to type one row")
    ap.add_argument("--delay", type=float, default=0.8, help="pause before typing starts")
    ap.add_argument("--no-ghost", dest="ghost", action="store_false", help="skip the faint preview before typing")
    ap.add_argument("--bg", default="#000000", help="panel background colour, e.g. #000000")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark",
                    help="light: dark glyphs on white for GitHub's light mode (writes the same layout)")
    ap.add_argument("--aspect", type=float, default=1.3, help="panel height/width ratio; 1.3 matches the info card at 370px")
    args = ap.parse_args()

    static = os.environ.get("STATIC") == "1"
    global SHADES
    if args.theme == "light":
        # on white, dense glyphs read dark, so map darkness to density and shade
        # light-green (highlights) to deep green (shadows)
        SHADES = _ramp("#c3ead0", "#2ea043", "#06301a", 10)
        args.negative = True
    lines = to_grid(Image.open(args.src), args.cols, args.negative)
    svg = build_mono(lines, static) if args.mono else build_terminal(lines, static, args.title, args.prompt,
                                                                       args.type_time, args.row_dur, args.delay, args.ghost,
                                                                       args.bg, args.aspect)
    if args.theme == "light":
        from theme_light import to_light
        svg = to_light(svg.replace(' filter="url(#glow)"', ""), heatmap=False)
    Path(args.out).write_text(svg, encoding="utf-8")
    print(f"wrote {Path(args.out).name} ({len(lines)} rows x {args.cols} cols)")


if __name__ == "__main__":
    main()

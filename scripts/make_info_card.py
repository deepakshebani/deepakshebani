"""Step 4: neofetch-style info card.

Edit the TITLE and ROWS below, then run:
    python scripts/make_info_card.py          # writes info-card.svg
    STATIC=1 python scripts/make_info_card.py # frozen frame for previews
"""
import os
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- content ---
TITLE = "deepak@github"
ROWS = [
    ("Role",       "Sales, account management and business development"),
    ("Location",   "Dublin, Ireland"),
    ("Now",        "Open to sales and account management roles in Dublin"),
    ("Prev",       "Digital advertising sales (Amazon Ads, Google Ads, Meta Ads) at Cognizant and Tech Mahindra"),
    ("Prev",       "Energy Adviser at BillSave; Marketing Intern at RakFort"),
    ("Education",  "Master's in Management, DCU (2025); Mechanical Engineering degree"),
    ("Certs",      "Salesforce Agentforce Specialist, Google Ads, Amazon Ads"),
    ("Building",   "Leaflet + Firebase field map; Google Sheets outreach automation"),
    ("Web",        "deepakshebani.com"),
    ("Contact",    "deepakshebani@gmail.com"),
]
# ----------------------------------------------------------------------------

W = 490
PAD = 20
FONT = 12.5
LINE_H = 19
KEY_W = 92          # px column for keys
WRAP = 44           # chars per value line
BG = "#0d1117"
BORDER = "#30363d"
KEY = "#58a6ff"
VAL = "#c9d1d9"
ACCENT = "#39d353"
DIM = "#8b949e"
SWATCHES = ["#f85149", "#d29922", "#39d353", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9", "#6e7681"]
STEP = float(os.environ.get("CARD_STEP", 0.38))    # seconds between lines
START = float(os.environ.get("CARD_START", 1.2))   # pause before the first line
FADE = float(os.environ.get("CARD_FADE", 0.8))    # each line's fade-in


def main() -> None:
    static = os.environ.get("STATIC") == "1"

    # flatten into printable lines: (key or None, text, colour)
    lines = [(None, TITLE, ACCENT), (None, "-" * len(TITLE), DIM)]
    for key, value in ROWS:
        wrapped = textwrap.wrap(value, WRAP) or [""]
        for j, part in enumerate(wrapped):
            lines.append((key if j == 0 else "", part, VAL))

    top = PAD + 34  # below the title bar
    swatch_y = top + len(lines) * LINE_H + 10
    H = swatch_y + 18 + PAD

    css = "" if static else (
        "<style>"
        f".l{{opacity:0;transform:translateX(-6px);animation:in {FADE}s ease-out forwards}}"
        "@keyframes in{to{opacity:1;transform:translateX(0)}}"
        "</style>"
    )

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Profile info card">',
        css,
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        # title bar
        f'<path d="M0.5 10.5 a10 10 0 0 1 10 -10 h{W-21} a10 10 0 0 1 10 10 v18 h-{W-1} z" fill="#161b22"/>',
        f'<line x1="0.5" y1="28.5" x2="{W-0.5}" y2="28.5" stroke="{BORDER}"/>',
        '<circle cx="16" cy="14.5" r="5" fill="#f85149"/>',
        '<circle cx="32" cy="14.5" r="5" fill="#d29922"/>',
        '<circle cx="48" cy="14.5" r="5" fill="#39d353"/>',
        f'<text x="{W/2}" y="18.5" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace" '
        f'font-size="11" fill="{DIM}">~/neofetch</text>',
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace" font-size="{FONT}">',
    ]

    for i, (key, text, colour) in enumerate(lines):
        y = top + i * LINE_H
        style = "" if static else f' style="animation-delay:{START + i * STEP:.2f}s"'
        cls = "" if static else ' class="l"'
        parts = [f'<g{cls}{style}>']
        if key is None:
            parts.append(f'<text x="{PAD}" y="{y}" fill="{colour}" font-weight="bold">{escape(text)}</text>')
        else:
            if key:
                parts.append(f'<text x="{PAD}" y="{y}" fill="{KEY}" font-weight="bold">{escape(key)}</text>')
                parts.append(f'<text x="{PAD + KEY_W - 10}" y="{y}" fill="{DIM}">:</text>')
            parts.append(f'<text x="{PAD + KEY_W}" y="{y}" fill="{colour}">{escape(text)}</text>')
        parts.append("</g>")
        out.append("".join(parts))

    # neofetch colour blocks
    delay = START + len(lines) * STEP
    style = "" if static else f' class="l" style="animation-delay:{delay:.2f}s"'
    out.append(f"<g{style}>")
    for k, c in enumerate(SWATCHES):
        out.append(f'<rect x="{PAD + k * 26}" y="{swatch_y - 4}" width="22" height="14" rx="2" fill="{c}"/>')
    out.append("</g>")

    out.append("</g></svg>")
    (ROOT / "info-card.svg").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote info-card.svg ({W}x{H}, {len(lines)} lines)")


if __name__ == "__main__":
    main()

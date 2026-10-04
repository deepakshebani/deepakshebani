"""Extra profile panels, in the same terminal style as the info card.

    career-log.svg  `git log` of your career, then your certifications as tags
    toolkit.svg     `pip list` of the tools you use, and where you used them
    tagline.svg     one typed line that cycles through short role phrases

Edit the content blocks below, then run:
    python scripts/make_extras.py
    STATIC=1 python scripts/make_extras.py   # frozen frames for previews

Pace follows the info card (CARD_STEP / CARD_START env vars).
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------ content --
CAREER = [  # newest first, like git log
    ("HEAD -> main", "Open to sales, account management and BD roles in Dublin"),
    ("", "Dublin: Energy Adviser at BillSave, Marketing Intern at RakFort"),
    ("", "Master's in Management, Dublin City University (2025)"),
    ("", "4+ years digital ad sales (Amazon, Google, Meta Ads) at Cognizant and Tech Mahindra"),
    ("", "Degree in Mechanical Engineering"),
]
TAGS = ["salesforce-agentforce-specialist", "google-ads-certified", "amazon-ads-certified"]

TOOLKIT = [  # (tool, where you actually used it, certified?)
    ("google-ads", "ad sales and accounts, 4+ years", True),
    ("amazon-ads", "ad sales and accounts, 4+ years", True),
    ("meta-ads", "ad sales and accounts, 4+ years", False),
    ("salesforce", "Agentforce Specialist", True),
    ("google-sheets", "CRM for my outreach automation", False),
    ("apps-script", "sequenced emails, reply detection", False),
    ("looker-studio", "outreach dashboards", False),
    ("firebase", "energy adviser field map", False),
    ("leaflet", "energy adviser field map", False),
    ("tableau", "Master's project dashboard", False),
    ("python", "Master's project report (Quarto)", False),
]

TAGLINES = [
    "Digital ad sales: Google, Amazon and Meta Ads",
    "Account management and business development",
    "Salesforce Agentforce Specialist",
    "Building sales tools with Sheets, Apps Script and Firebase",
    "Open to roles in Dublin",
]
PROMPT = "deepak@dublin:~$ whoami --role"
# ---------------------------------------------------------------------------

STATIC = os.environ.get("STATIC") == "1"
STEP = float(os.environ.get("CARD_STEP", 0.38))
START = float(os.environ.get("CARD_START", 1.2))
FADE = float(os.environ.get("CARD_FADE", 0.8))

W = 860
PAD = 22
FONT = 12.5
LINE_H = 21
CW = FONT * 0.6
BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
DIM = "#8b949e"
GREEN = "#39d353"
MINT = "#69f0a0"
BLUE = "#58a6ff"
AMBER = "#d29922"
FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace"


def frame(h: int, title: str) -> list[str]:
    css = "" if STATIC else (
        "<style>"
        f".l{{opacity:0;transform:translateX(-6px);animation:in {FADE}s ease-out forwards}}"
        "@keyframes in{to{opacity:1;transform:translateX(0)}}"
        ".blink{animation:b 1.1s steps(1) infinite}@keyframes b{50%{opacity:0}}"
        "</style>"
    )
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{escape(title)}">',
        css,
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M0.5 10.5 a10 10 0 0 1 10 -10 h{W - 21} a10 10 0 0 1 10 10 v18 h-{W - 1} z" fill="{BAR}"/>',
        f'<line x1="0.5" y1="28.5" x2="{W - 0.5}" y2="28.5" stroke="{BORDER}"/>',
        '<circle cx="16" cy="14.5" r="5" fill="#f85149"/><circle cx="32" cy="14.5" r="5" fill="#d29922"/><circle cx="48" cy="14.5" r="5" fill="#39d353"/>',
        f'<text x="{W / 2:.0f}" y="18.5" text-anchor="middle" font-family="{FAMILY}" font-size="11" fill="{DIM}">{escape(title)}</text>',
        f'<g font-family="{FAMILY}" font-size="{FONT}" xml:space="preserve">',
    ]


def line(i: int, inner: str) -> str:
    if STATIC:
        return f"<g>{inner}</g>"
    return f'<g class="l" style="animation-delay:{START + i * STEP:.2f}s">{inner}</g>'


def career_log() -> str:
    top = 28 + PAD + 10
    rows = len(CAREER) + 2 + 1  # command, commits, gap, tag command, tags row
    h = top + (rows + 1) * LINE_H + PAD
    out = frame(h, "~/career (main)")
    y = top
    out.append(line(0, f'<text x="{PAD}" y="{y}"><tspan fill="{GREEN}">$</tspan><tspan fill="{FG}"> git log --oneline --graph</tspan></text>'))
    hashes = ["a3f9c21", "7c1e0b4", "5d2a9f8", "1b8e3c7", "9f0d6a2", "0a1b2c3", "e4d5f60"]
    for n, (ref, msg) in enumerate(CAREER):
        y += LINE_H
        x = PAD
        parts = [f'<text x="{x}" y="{y}"><tspan fill="{MINT}">*</tspan>']
        parts.append(f'<tspan fill="{AMBER}"> {hashes[n % len(hashes)]}</tspan>')
        if ref:
            head, _, branch = ref.partition(" -> ")
            parts.append(f'<tspan fill="{DIM}"> (</tspan><tspan fill="#39c5cf" font-weight="bold">{escape(head)}</tspan>')
            if branch:
                parts.append(f'<tspan fill="{DIM}"> -&gt; </tspan><tspan fill="{GREEN}" font-weight="bold">{escape(branch)}</tspan>')
            parts.append(f'<tspan fill="{DIM}">)</tspan>')
        parts.append(f'<tspan fill="{FG}"> {escape(msg)}</tspan></text>')
        if n < len(CAREER) - 1:
            parts.append(f'<line x1="{PAD + CW / 2:.1f}" y1="{y + 5}" x2="{PAD + CW / 2:.1f}" y2="{y + LINE_H - 12}" stroke="{MINT}" stroke-opacity=".5"/>')
        out.append(line(n + 1, "".join(parts)))
    y += LINE_H * 2
    k = len(CAREER) + 1
    out.append(line(k, f'<text x="{PAD}" y="{y}"><tspan fill="{GREEN}">$</tspan><tspan fill="{FG}"> git tag --list "certs/*"</tspan></text>'))
    y += LINE_H + 2
    x = PAD
    chips = []
    for t in TAGS:
        label = f"certs/{t}"
        w = len(label) * CW + 18
        chips.append(f'<rect x="{x:.1f}" y="{y - 14}" width="{w:.1f}" height="20" rx="10" fill="#04260f" stroke="{GREEN}" stroke-opacity=".7"/>'
                     f'<text x="{x + 9:.1f}" y="{y}" fill="{MINT}">{escape(label)}</text>')
        x += w + 10
    out.append(line(k + 1, "".join(chips)))
    out.append("</g></svg>")
    return "\n".join(out)


def toolkit() -> str:
    top = 28 + PAD + 10
    h = top + (len(TOOLKIT) + 2) * LINE_H + PAD
    out = frame(h, "~/toolkit")
    y = top
    out.append(line(0, f'<text x="{PAD}" y="{y}"><tspan fill="{GREEN}">$</tspan><tspan fill="{FG}"> pip list --user --verbose</tspan></text>'))
    y += LINE_H
    col2 = PAD + 22 * CW
    col3 = W - PAD - 11 * CW
    out.append(line(1, f'<text x="{PAD}" y="{y}" fill="{DIM}">Package</text><text x="{col2:.1f}" y="{y}" fill="{DIM}">Where I used it</text>'
                       f'<text x="{col3:.1f}" y="{y}" fill="{DIM}">Status</text>'
                       f'<line x1="{PAD}" y1="{y + 7}" x2="{W - PAD}" y2="{y + 7}" stroke="{BORDER}"/>'))
    for n, (tool, where, cert) in enumerate(TOOLKIT):
        y += LINE_H
        status = (f'<rect x="{col3 - 6:.1f}" y="{y - 13}" width="{9 * CW + 12:.1f}" height="18" rx="9" fill="#04260f" stroke="{GREEN}" stroke-opacity=".7"/>'
                  f'<text x="{col3:.1f}" y="{y}" fill="{MINT}">certified</text>') if cert else f'<text x="{col3:.1f}" y="{y}" fill="{DIM}">used</text>'
        out.append(line(n + 2, f'<text x="{PAD}" y="{y}" fill="{BLUE}">{escape(tool)}</text>'
                               f'<text x="{col2:.1f}" y="{y}" fill="{FG}">{escape(where)}</text>{status}'))
    out.append("</g></svg>")
    return "\n".join(out)


def tagline() -> str:
    h = 56
    fs = 15
    cw = fs * 0.6
    px = 22
    tx = px + (len(PROMPT) + 1) * cw
    type_s, hold, delete_s, gap = 1.6, 2.2, 0.6, 0.3
    slot = type_s + hold + delete_s + gap
    T = slot * len(TAGLINES)
    yb = 34
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{escape(" / ".join(TAGLINES))}">',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        "<defs>",
    ]
    widths = [len(t) * cw for t in TAGLINES]

    def kt(i):
        a = i * slot / T
        b = (i * slot + type_s) / T
        c = (i * slot + type_s + hold) / T
        d = (i * slot + type_s + hold + delete_s) / T
        return a, b, c, d

    for i, (t, w) in enumerate(zip(TAGLINES, widths)):
        if STATIC:
            if i == 0:
                out.append(f'<clipPath id="t{i}"><rect x="{tx:.1f}" y="10" width="{w + 2:.1f}" height="36"/></clipPath>')
            else:
                out.append(f'<clipPath id="t{i}"><rect x="{tx:.1f}" y="10" width="0" height="36"/></clipPath>')
            continue
        a, b, c, d = kt(i)
        e = 1e-4
        keys, vals = ["0"], ["0"]
        for kk, vv in ((max(a, e) if i else e, 0), (b, w + 2), (c, w + 2), (d, 0)):
            keys.append(f"{kk:.4f}")
            vals.append(f"{vv:.1f}")
        keys.append("1")
        vals.append("0")
        out.append(f'<clipPath id="t{i}"><rect x="{tx:.1f}" y="10" width="0" height="36">'
                   f'<animate attributeName="width" values="{";".join(vals)}" keyTimes="{";".join(keys)}" dur="{T:.2f}s" repeatCount="indefinite" calcMode="linear"/>'
                   f'</rect></clipPath>')
    out.append("</defs>")
    out.append(f'<g font-family="{FAMILY}" font-size="{fs}" xml:space="preserve">')
    out.append(f'<text x="{px}" y="{yb}" fill="{GREEN}">{escape(PROMPT)}</text>')
    for i, t in enumerate(TAGLINES):
        out.append(f'<text x="{tx:.1f}" y="{yb}" fill="{MINT}" font-weight="bold" clip-path="url(#t{i})">{escape(t).replace(" ", "&#160;")}</text>')
    # cursor follows the end of whichever phrase is typing
    if STATIC:
        out.append(f'<rect x="{tx + widths[0] + 3:.1f}" y="{yb - 14}" width="9" height="18" fill="{MINT}"/>')
    else:
        keys, vals = [], []
        for i, w in enumerate(widths):
            a, b, c, d = kt(i)
            for kk, vv in ((a, tx), (b, tx + w + 3), (c, tx + w + 3), (d, tx)):
                keys.append(kk)
                vals.append(vv)
        keys.append(1.0)
        vals.append(tx)
        out.append(f'<rect x="{tx:.1f}" y="{yb - 14}" width="9" height="18" fill="{MINT}">'
                   f'<animate attributeName="x" values="{";".join(f"{v:.1f}" for v in vals)}" keyTimes="{";".join(f"{k:.4f}" for k in keys)}" dur="{T:.2f}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/>'
                   f'</rect>')
    out.append("</g></svg>")
    return "\n".join(out)


def main() -> None:
    for name, fn in (("career-log.svg", career_log), ("toolkit.svg", toolkit), ("tagline.svg", tagline)):
        (ROOT / name).write_text(fn(), encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()

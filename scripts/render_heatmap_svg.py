"""Step 5b: render data/contributions.json as an animated 53x7 heatmap SVG.

Boxes slide down diagonally (CSS keyframes, play once and freeze), with
month labels, weekday labels, a Less -> More legend and a stats footer.

Usage:  python scripts/render_heatmap_svg.py
        STATIC=1 python scripts/render_heatmap_svg.py
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# none -> brightest (level 5 is a neon top end for your biggest days)

W = 860
CELL = 12
GAP = 3
STEP = CELL + GAP
LEFT = 44            # room for weekday labels
TOP = 46             # room for header + month labels
BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#8b949e"
BRIGHT = "#c9d1d9"
HEAT_STEP = float(os.environ.get("HEAT_STEP", 0.055))  # delay per diagonal
HEAT_DROP = float(os.environ.get("HEAT_DROP", 0.6))   # each box's drop-in
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace"


def level_for(count: int, gh_level: int, top: int) -> int:
    if count <= 0:
        return 0
    # neon level 5 for days in the top slice of your own range
    if top and count >= max(top * 0.75, 1) and gh_level >= 4:
        return 5
    return max(1, min(gh_level, 4))


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    data = json.loads(SRC.read_text(encoding="utf-8"))
    days = data["days"]
    s = data["stats"]
    top = max(d["count"] for d in days)

    first = date.fromisoformat(days[0]["date"])
    # GitHub columns start on Sunday
    start = first - timedelta(days=(first.weekday() + 1) % 7)

    cells = []
    month_labels = {}
    for d in days:
        dt = date.fromisoformat(d["date"])
        col = (dt - start).days // 7
        row = (dt.weekday() + 1) % 7
        cells.append((col, row, d))
        if dt.day <= 7 and row == 0 or (col == 0 and row == 0):
            month_labels.setdefault(col, dt.strftime("%b"))

    cols = max(c for c, _, _ in cells) + 1
    grid_w = cols * STEP - GAP
    x0 = LEFT + (W - LEFT - 20 - grid_w) / 2 if grid_w < W - LEFT - 20 else LEFT
    grid_h = 7 * STEP - GAP
    H = TOP + grid_h + 62

    css = "" if static else (
        "<style>"
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
        f"animation:drop {HEAT_DROP}s cubic-bezier(.2,.8,.2,1) forwards}}"
        "@keyframes drop{0%{opacity:0;transform:translateY(-8px) scale(.6)}"
        "100%{opacity:1;transform:translateY(0) scale(1)}}"
        ".f{opacity:0;animation:fade .6s ease-out forwards}"
        "@keyframes fade{to{opacity:1}}"
        "</style>"
    )

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{s["total"]} contributions in the last year">',
        css,
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<g font-family="{FONT}" font-size="11" fill="{TEXT}">',
        f'<text x="20" y="22" fill="{BRIGHT}" font-size="12.5" font-weight="bold">'
        f'{s["total"]:,} contributions in the last year</text>',
        f'<text x="{W-20}" y="22" text-anchor="end">@{data["username"]}</text>',
    ]

    for col, label in month_labels.items():
        if col * STEP + 24 < grid_w:
            out.append(f'<text x="{x0 + col * STEP:.1f}" y="{TOP - 8}">{label}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{x0 - 8:.1f}" y="{TOP + row * STEP + 9.5}" text-anchor="end">{name}</text>')
    out.append("</g>")

    last_delay = 0.0
    for col, row, d in cells:
        lvl = level_for(d["count"], d["level"], top)
        x = x0 + col * STEP
        y = TOP + row * STEP
        delay = (col + row) * HEAT_STEP
        last_delay = max(last_delay, delay)
        anim = "" if static else f' class="c" style="animation-delay:{delay:.3f}s"'
        title = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {d["date"]}'
        out.append(
            f'<rect{anim} x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[lvl]}"><title>{title}</title></rect>'
        )

    fy = TOP + grid_h + 26
    fade = "" if static else f' class="f" style="animation-delay:{last_delay + 0.3:.2f}s"'
    best = s["best_day"]
    best_txt = date.fromisoformat(best["date"]).strftime("%d %b %Y")
    out.append(f'<g{fade} font-family="{FONT}" font-size="11" fill="{TEXT}">')
    out.append(
        f'<text x="20" y="{fy}">current streak <tspan fill="{BRIGHT}">{s["current_streak"]}d</tspan>'
        f'  ·  longest <tspan fill="{BRIGHT}">{s["longest_streak"]}d</tspan>'
        f'  ·  best day <tspan fill="{BRIGHT}">{best["count"]}</tspan> ({best_txt})'
        f'  ·  active days <tspan fill="{BRIGHT}">{s["active_days"]}</tspan></text>'
    )
    lx = W - 20 - (len(PALETTE) * 15 + 70)
    out.append(f'<text x="{lx}" y="{fy}">Less</text>')
    for i, c in enumerate(PALETTE):
        out.append(f'<rect x="{lx + 32 + i * 15}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    out.append(f'<text x="{lx + 36 + len(PALETTE) * 15}" y="{fy}">More</text>')
    out.append(f'<text x="20" y="{fy + 20}" font-size="10" fill="#6e7681">updated {data["generated_at"][:10]}</text>')
    out.append("</g></svg>")

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.name} ({cols} weeks, {len(cells)} days)")


if __name__ == "__main__":
    main()

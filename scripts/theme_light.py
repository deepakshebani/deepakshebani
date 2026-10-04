"""Make light-mode copies of the dark SVGs by swapping the palette.

    python scripts/theme_light.py info-card.svg career-log.svg ...
    -> info-card-light.svg, career-log-light.svg, ...

GitHub shows the light copy to visitors using light mode, via <picture> in
the README. The ASCII portrait is not remapped here (it needs its glyphs
re-chosen); build it with `make_ascii_svg.py --theme light` instead.
"""
import re
import sys
from pathlib import Path

# dark (GitHub dark) -> light (GitHub light), one pass so swaps never chain
PALETTE = {
    "#0d1117": "#ffffff",  # page / panel background
    "#000000": "#ffffff",
    "#161b22": "#f6f8fa",  # title bars
    "#30363d": "#d0d7de",  # borders
    "#c9d1d9": "#24292f",  # main text
    "#8b949e": "#57606a",  # dim text
    "#6e7681": "#6e7781",
    "#58a6ff": "#0969da",  # blue
    "#39c5cf": "#1b7c83",  # cyan
    "#bc8cff": "#8250df",  # purple
    "#d29922": "#9a6700",  # amber
    "#39d353": "#1a7f37",  # green accent
    "#69f0a0": "#116329",  # mint accent
    "#04260f": "#dafbe1",  # chip fill
    # contribution heatmap ramp (none -> most)
    "#0e4429": "#9be9a8",
    "#006d32": "#40c463",
    "#26a641": "#30a14e",
}
# heatmap cells: level 0 and the neon top level read better with these
HEATMAP_EXTRA = {"#161b22": "#ebedf0", "#39d353": "#216e39", "#69f0a0": "#0a3d1f"}


def to_light(svg: str, heatmap: bool) -> str:
    table = {**PALETTE, **(HEATMAP_EXTRA if heatmap else {})}
    pat = re.compile("|".join(re.escape(k) for k in table), re.IGNORECASE)
    svg = pat.sub(lambda m: table[m.group(0).lower()], svg)
    # dark glows and black scanlines are too heavy on white
    svg = svg.replace('opacity="0.16"/></pattern>', 'opacity="0.04"/></pattern>')
    return svg


def main() -> None:
    for name in sys.argv[1:]:
        src = Path(name)
        out = src.with_name(src.stem + "-light" + src.suffix)
        out.write_text(to_light(src.read_text(encoding="utf-8"), "heatmap" in src.name), encoding="utf-8")
        print("wrote", out.name)


if __name__ == "__main__":
    main()

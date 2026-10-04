"""Step 5a: scrape the public contribution calendar (no token needed).

Source: https://github.com/users/<username>/contributions
Output: data/contributions.json with raw days plus derived stats.

Username comes from $GITHUB_USER, then $GITHUB_REPOSITORY_OWNER (set in
Actions), then the USERNAME constant below.
"""
import json
import os
import re
from collections import OrderedDict
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "deepakshebani"  # fallback for local runs

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def username() -> str:
    return os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or USERNAME


def parse_count(text: str) -> int:
    text = text.strip()
    if text.lower().startswith("no contribution"):
        return 0
    m = re.match(r"([\d,]+)\s+contribution", text)
    return int(m.group(1).replace(",", "")) if m else 0


def fetch(user: str) -> list[dict]:
    url = f"https://github.com/users/{user}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-readme-heatmap"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # tooltips hold the counts; they point at day cells by id
    tips = {t.get("for"): parse_count(t.get_text()) for t in soup.select("tool-tip[for]")}

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        d = td["data-date"]
        level = int(td.get("data-level", 0))
        count = tips.get(td.get("id"))
        if count is None:  # older markup kept the count on the cell
            count = int(td.get("data-count", 0))
        days.append({"date": d, "count": count, "level": level})

    if not days:
        raise SystemExit("no contribution cells found; GitHub may have changed its markup")
    days.sort(key=lambda x: x["date"])
    return days


def stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # current streak: count back from today (today being empty doesn't break it)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["count"] > 0:
            current += 1
        elif i == 0:
            continue
        else:
            break

    months: "OrderedDict[str, int]" = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"] > 0),
        "monthly": months,
    }


def main() -> None:
    user = username()
    days = fetch(user)
    data = {
        "username": user,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "stats": stats(days),
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    s = data["stats"]
    print(f"{user}: {s['total']} contributions, {len(days)} days, "
          f"current streak {s['current_streak']}, longest {s['longest_streak']}")


if __name__ == "__main__":
    main()

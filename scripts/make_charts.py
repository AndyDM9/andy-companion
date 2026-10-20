"""Charts for the README and the Devpost gallery, drawn from the scorecards, so a chart never says more than
its scorecard (PLAN B30).

    uv run python scripts/make_charts.py      writes docs/images/scam-check-five-ways.svg, and a .png beside it
                                              for the Devpost gallery when rsvg-convert is installed

The scam check, measured five ways: for each way, the scams caught (of 60) and the ordinary messages wrongly
flagged (of 60), the mean of three runs (the word rules need one), each with its Wilson 95% interval over the 60
messages (PLAN B33), and what Andy's check costs per 1,000. Plain SVG, no library; text stays text, so it reads at
any size.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from andy_companion.measure import wilson  # noqa: E402

SCORECARD = ROOT / "evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json"
BASELINE = ROOT / "evals/results/scam-word-rules-2026-10-20-1552.json"
OUT = ROOT / "docs/images/scam-check-five-ways.svg"
WAYS = [("word_rules", "Word rules alone (no model, no web)", False),
        ("lightning", "Nemotron 3.5 Lightning alone", False),
        ("ultra", "Nemotron 3 Ultra alone, no web", False),
        ("tavily_lightning", "Tavily's warnings, matched by Lightning", False),
        ("tavily_ultra", "Andy: Tavily's warnings, matched by Ultra", True)]
CAUGHT, FLAGGED, INK, SOFT, RULE, GROUND = "#1c5244", "#a3341c", "#1d2a1f", "#3d4d3f", "#c7d5c1", "#f6f8f4"


def number(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:.1f}"


def band(value: float, n: float = 60) -> str:
    lo, hi = wilson(value, int(round(n)))
    return f"{lo * 100:.0f}–{hi * 100:.0f}%"


def scam_chart(card: dict, baseline: dict) -> str:
    s = {**card["summary"], **baseline["summary"]}
    cost = baseline["cost_per_1000_checks_usd"]
    w, left, bar_w, row_h, top = 1000, 390, 410, 86, 104
    scale = bar_w / 60
    h = top + row_h * len(WAYS) + 116
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
           'aria-labelledby="t d" font-family="Atkinson Hyperlegible, Segoe UI, Helvetica, Arial, sans-serif">',
           '<title id="t">The scam check, measured five ways</title>',
           '<desc id="d">' + html.escape("; ".join(
               f"{label}: {number(s[k]['all']['caught_mean'])} of 60 scams caught, "
               f"{number(s[k]['all']['flagged_mean'])} of 60 ordinary messages flagged" for k, label, _ in WAYS)
               + f"; 95% intervals over the 60 messages; Andy's check about ${cost['total']:.0f} per 1,000") + "</desc>",
           f'<rect width="{w}" height="{h}" rx="18" fill="{GROUND}"/>',
           f'<text x="32" y="46" font-size="24" font-weight="700" fill="{INK}">The scam check, measured five ways</text>',
           f'<rect x="{left}" y="64" width="16" height="16" rx="3" fill="{CAUGHT}"/>'
           f'<text x="{left + 24}" y="77" font-size="16" fill="{INK}">Scams caught, of 60</text>',
           f'<rect x="{left + 210}" y="64" width="16" height="16" rx="3" fill="{FLAGGED}"/>'
           f'<text x="{left + 234}" y="77" font-size="16" fill="{INK}">Ordinary messages flagged, of 60</text>']
    for i, (key, label, ours) in enumerate(WAYS):
        a = s[key]["all"]
        y = top + i * row_h
        weight = "700" if ours else "400"
        if ours:
            out.append(f'<rect x="16" y="{y - 8}" width="{w - 32}" height="{row_h - 6}" rx="12" fill="none" '
                       f'stroke="{CAUGHT}" stroke-width="2"/>')
        words = label.split(": ") if ": " in label else [label]
        for j, part in enumerate(words):
            out.append(f'<text x="32" y="{y + 26 + j * 22}" font-size="17" font-weight="{weight}" fill="{INK}">'
                       f'{html.escape(part + (":" if j == 0 and len(words) > 1 else ""))}</text>')
        for j, (value, colour) in enumerate(((a["caught_mean"], CAUGHT), (a["flagged_mean"], FLAGGED))):
            by = y + 6 + j * 32
            out.append(f'<rect x="{left}" y="{by}" width="{bar_w}" height="24" rx="5" fill="{RULE}" opacity=".45"/>')
            if value:
                out.append(f'<rect x="{left}" y="{by}" width="{value * scale:.1f}" height="24" rx="5" fill="{colour}"/>')
            out.append(f'<text x="{left + bar_w + 12}" y="{by + 18}" font-size="17" font-weight="700" fill="{INK}">'
                       f'{number(value)}<tspan font-size="14" font-weight="400" fill="{SOFT}" dx="8">'
                       f'{band(value)}</tspan></text>')
    notes = (f"120 messages read aloud (60 with scam signs, 60 ordinary); the models' mean of three runs, as Nebius "
             f"Serverless Jobs, {card['ran'][:10]}.",
             f"Grey: the 95% interval over the 60 messages. Ultra alone: {card['errors']} failed answers are left out of its totals.",
             f"Andy's check costs about ${cost['total']:.0f} per 1,000 (Tavily ${cost['tavily']:.0f}, the two Nemotron "
             f"calls ${cost['models']:.2f}), at pay-as-you-go prices.")
    for j, note in enumerate(notes):
        out.append(f'<text x="32" y="{h - 70 + j * 22}" font-size="14" fill="{SOFT}">{html.escape(note)}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    import shutil
    import subprocess

    card = json.loads(SCORECARD.read_text())
    OUT.write_text(scam_chart(card, json.loads(BASELINE.read_text())))
    print(f"Wrote {OUT.relative_to(ROOT)}")
    if shutil.which("rsvg-convert"):          # Devpost's gallery takes pictures, not SVG: twice the size, sharp
        png = OUT.with_suffix(".png")
        subprocess.run(["rsvg-convert", "--zoom", "2", "-o", str(png), str(OUT)], check=True)
        print(f"Wrote {png.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

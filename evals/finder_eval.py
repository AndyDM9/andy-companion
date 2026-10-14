"""How well does Andy find things? Scores the tries kept by the finder (PLAN B11).

    ANDY_FINDER_RECORD=~/andy-finder-tries ./scripts/andy        record: hide something, ask Andy, repeat
    uv run python evals/finder_eval.py sheet ~/andy-finder-tries  a contact sheet of every try, to label
    uv run python evals/finder_eval.py score ~/andy-finder-tries  the score, from labels.csv

Each try (src/andy_companion/finder.record) holds the four views Andy took, left to right, what NVIDIA
Nemotron Nano VL said of each, the view Andy chose and the times. Ground truth comes from the person who hid
the thing, in labels.csv beside the tries, one line per try:

    try-20261015-101500,2          the thing was in view 2 (0 is Andy's far left)
    try-20261015-101730,1 2        in views 1 and 2 (either is right)
    try-20261015-102000,none       not in any view (hidden out of sight on purpose)

The score: of the tries where the thing was in sight, how often Andy pointed at a right view, chose a wrong
one, or said it couldn't see it; of the tries where it wasn't, how often Andy said so rather than pointing at
something; and the median time from the question's sweep to the point. The frames stay on this computer; the
scorecard keeps only numbers and try names. Delete the tries once scored.
"""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def tries(folder: Path) -> list:
    out = []
    for d in sorted(folder.glob("try-*")):
        if (d / "try.json").exists():
            out.append({"name": d.name, "dir": d, **json.loads((d / "try.json").read_text())})
    return out


def labels(folder: Path) -> dict:
    found = {}
    path = folder / "labels.csv"
    for line in path.read_text().splitlines() if path.exists() else []:
        line = line.split("#")[0].strip()
        if not line or "," not in line:
            continue
        name, truth = (x.strip() for x in line.split(",", 1))
        found[name] = set() if truth.lower() == "none" else {int(v) for v in truth.split()}
    return found


def score(all_tries: list, truth: dict) -> dict:
    rows = []
    for t in all_tries:
        if t["name"] not in truth:
            continue
        want, got = truth[t["name"]], t.get("chosen")
        if want:
            outcome = "right" if got in want else ("wrong view" if got is not None else "missed")
        else:
            outcome = "said not seen" if got is None else "pointed at nothing"
        rows.append({"try": t["name"], "what": t.get("what", ""), "truth": sorted(want), "chosen": got,
                     "outcome": outcome, "to_point_s": t.get("seconds", {}).get("to_point")})
    in_sight = [r for r in rows if r["truth"]]
    out_of_sight = [r for r in rows if not r["truth"]]
    times = sorted(r["to_point_s"] for r in rows if r["to_point_s"] is not None)
    count = lambda rs, o: sum(1 for r in rs if r["outcome"] == o)  # noqa: E731
    return {"labelled": len(rows), "unlabelled": len(all_tries) - len(rows),
            "in_sight": {"tries": len(in_sight), "right": count(in_sight, "right"),
                         "wrong_view": count(in_sight, "wrong view"), "missed": count(in_sight, "missed")},
            "out_of_sight": {"tries": len(out_of_sight), "said_not_seen": count(out_of_sight, "said not seen"),
                             "pointed_at_nothing": count(out_of_sight, "pointed at nothing")},
            "median_to_point_s": times[len(times) // 2] if times else None, "rows": rows}


def sheet(folder: Path) -> Path:
    """One page with every try's four views; Andy's choice outlined; what the model said under each."""
    parts = ["<!doctype html><meta charset='utf-8'><title>Finder tries</title><style>body{font:16px system-ui;"
             "margin:16px}figure{display:inline-block;margin:4px;width:23%;vertical-align:top}img{width:100%}"
             ".chosen img{outline:6px solid #0a7}h2{margin:24px 0 4px}</style><h1>Finder tries</h1>"
             "<p>Write one line per try in labels.csv: the try's name, then the view numbers that show the thing "
             "(0 is Andy's far left), or none.</p>"]
    for t in tries(folder):
        parts.append(f"<h2>{html.escape(t['name'])}: {html.escape(t.get('what', ''))}</h2>")
        for i, r in enumerate(t.get("results", [])):
            chosen = " class='chosen'" if t.get("chosen") == i else ""
            said = "seen, " + html.escape(str(r.get("where", ""))) if r.get("seen") else "not seen"
            img = f"<img src='{t['name']}/view-{i}.jpg' alt='view {i}'>" if (t["dir"] / f"view-{i}.jpg").exists() else ""
            parts.append(f"<figure{chosen}>{img}<figcaption>view {i}: {said}</figcaption></figure>")
    out = folder / "sheet.html"
    out.write_text("\n".join(parts))
    return out


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("sheet", "score"):
        print(__doc__)
        return 2
    folder = Path(sys.argv[2]).expanduser()
    if sys.argv[1] == "sheet":
        print(f"Open {sheet(folder)} and write labels.csv beside it.")
        return 0
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), **score(tries(folder), labels(folder))}
    s, n = card["in_sight"], card["out_of_sight"]
    print(f"In sight: right {s['right']} of {s['tries']}, wrong view {s['wrong_view']}, missed {s['missed']}")
    print(f"Out of sight: said so {n['said_not_seen']} of {n['tries']}, pointed at nothing {n['pointed_at_nothing']}")
    print(f"Median time to point: {card['median_to_point_s']} s; {card['unlabelled']} tries not labelled")
    out = HERE / "results" / f"finder-eval-{datetime.now():%Y-%m-%d-%H%M}.json"
    out.write_text(json.dumps(card, indent=1))
    print(f"Scorecard: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

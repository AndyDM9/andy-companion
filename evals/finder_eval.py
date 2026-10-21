"""How well does Andy find things? Scores the tries kept by the finder (PLAN B11).

    ANDY_FINDER_RECORD=~/andy-finder-tries ./scripts/andy        record: hide something, ask Andy, repeat
    uv run python evals/finder_eval.py sheet ~/andy-finder-tries  a contact sheet of every try, to label
    uv run python evals/finder_eval.py score ~/andy-finder-tries  the score, from labels.csv
    uv run python evals/finder_eval.py compare ~/andy-finder-tries token-factory endpoint
                                                                  the same saved views read again by each
                                                                  of Andy's eyes (vision.eyes; PLAN B34)

Each try (src/andy_companion/finder.record) holds the four views Andy took, left to right, what NVIDIA
Nemotron vision model said of each, the view Andy chose and the times. Ground truth comes from the person who hid
the thing, in labels.csv beside the tries, one line per try:

    try-20261015-101500,2          the thing was in view 2 (0 is Andy's far left)
    try-20261015-101730,1 2        in views 1 and 2 (either is right)
    try-20261015-102000,none       not in any view (hidden out of sight on purpose)

The score: of the tries where the thing was in sight, how often Andy pointed at a right view, chose a wrong
one, or said it couldn't see it; of the tries where it wasn't, how often Andy said so rather than pointing at
something; and the median time from the question's sweep to the point. Each share carries its Wilson 95%
interval (andy_companion.measure). The frames stay on this computer (they go only to the model being
compared); the scorecard keeps only numbers and try names. Delete the tries once scored.
"""

from __future__ import annotations

import html
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from andy_companion.measure import wilson  # noqa: E402


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


def interval(k: int, n: int) -> list:
    """[low, high] as percentages, or None when there were no tries."""
    return [round(x * 100, 1) for x in wilson(k, n)] if n else None


def outcome(want: set, got) -> str:
    if want:
        return "right" if got in want else ("wrong view" if got is not None else "missed")
    return "said not seen" if got is None else "pointed at nothing"


def score(all_tries: list, truth: dict) -> dict:
    rows = []
    for t in all_tries:
        if t["name"] not in truth:
            continue
        want, got = truth[t["name"]], t.get("chosen")
        rows.append({"try": t["name"], "truth": sorted(want), "chosen": got,      # never what was asked for
                     "outcome": outcome(want, got), "to_point_s": t.get("seconds", {}).get("to_point")})
    in_sight = [r for r in rows if r["truth"]]
    out_of_sight = [r for r in rows if not r["truth"]]
    times = sorted(r["to_point_s"] for r in rows if r["to_point_s"] is not None)
    count = lambda rs, o: sum(1 for r in rs if r["outcome"] == o)  # noqa: E731
    return {"labelled": len(rows), "unlabelled": len(all_tries) - len(rows),
            "in_sight": {"tries": len(in_sight), "right": count(in_sight, "right"),
                         "right_95": interval(count(in_sight, "right"), len(in_sight)),
                         "wrong_view": count(in_sight, "wrong view"), "missed": count(in_sight, "missed")},
            "out_of_sight": {"tries": len(out_of_sight), "said_not_seen": count(out_of_sight, "said not seen"),
                             "said_not_seen_95": interval(count(out_of_sight, "said not seen"), len(out_of_sight)),
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


def reread(t: dict, eyes: str, asker=None) -> dict:
    """One saved try read again by `eyes` ('token-factory' or 'endpoint'): what it says of each view, the view it
    would choose, and the time for all four at once (as Andy asks them)."""
    import cv2

    from andy_companion import finder

    os.environ["ANDY_VISION"] = eyes
    asker = asker or finder.ask
    frames = [cv2.imread(str(t["dir"] / f"view-{i}.jpg")) for i in range(len(t.get("results", [])))]
    nothing = {"seen": False, "x": 0.5, "where": ""}
    start = time.monotonic()
    with ThreadPoolExecutor(4) as pool:
        # Each view as the finder reads it now: zoomed tiles unless ANDY_FINDER_ZOOM=off (finder.read_view).
        said = list(pool.map(lambda f: dict(nothing) if f is None else finder.read_view(f, t.get("what", "things"), asker), frames))
    return {"results": said, "chosen": finder.best(said), "seconds": round(time.monotonic() - start, 2)}


def compare(folder: Path, eyes_list: list, asker=None) -> dict:
    """Each labelled try's views read again by each of the eyes, scored the same way as the robot's own tries."""
    truth = labels(folder)
    labelled = [t for t in tries(folder) if t["name"] in truth]
    card = {"tries": len(labelled), "eyes": {}}
    for eyes in eyes_list:
        reads = {t["name"]: reread(t, eyes, asker) for t in labelled}
        redone = [{**t, "chosen": reads[t["name"]]["chosen"], "seconds": {"to_point": reads[t["name"]]["seconds"]}}
                  for t in labelled]
        views_right = sum(1 for t in labelled for i, r in enumerate(reads[t["name"]]["results"])
                          if bool(r.get("seen")) == (i in truth[t["name"]]))
        views = sum(len(reads[t["name"]]["results"]) for t in labelled)
        scored = score(redone, truth)
        scored.pop("rows")
        card["eyes"][eyes] = {**scored, "views_right": views_right, "views": views,
                              "views_right_95": interval(views_right, views)}
    return card


def main() -> int:
    if {"-h", "--help"} & set(sys.argv[1:]):     # the description, and nothing else run
        print(__doc__)
        return 0
    if len(sys.argv) >= 4 and sys.argv[1] == "compare":
        folder, eyes_list = Path(sys.argv[2]).expanduser(), sys.argv[3:]
        if not folder.is_dir():
            print(f"No folder of tries at {folder}.", file=sys.stderr)
            return 2
        card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), **compare(folder, eyes_list)}
        for eyes, c in card["eyes"].items():
            s = c["in_sight"]
            print(f"{eyes}: right {s['right']} of {s['tries']} {s['right_95']}, views read right {c['views_right']} of "
                  f"{c['views']}, median {c['median_to_point_s']} s for four views")
        out = HERE / "results" / f"finder-compare-{datetime.now():%Y-%m-%d-%H%M}.json"
        out.write_text(json.dumps(card, indent=1))
        print(f"Scorecard: {out}")
        return 0
    if len(sys.argv) != 3 or sys.argv[1] not in ("sheet", "score"):
        print(__doc__)
        return 2
    folder = Path(sys.argv[2]).expanduser()
    if not folder.is_dir():
        print(f"No folder of tries at {folder} (the finder keeps them where ANDY_FINDER_RECORD points).", file=sys.stderr)
        return 2
    if sys.argv[1] == "sheet":
        print(f"Open {sheet(folder)} and write labels.csv beside it.")
        return 0
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), **score(tries(folder), labels(folder))}
    s, n = card["in_sight"], card["out_of_sight"]
    print(f"In sight: right {s['right']} of {s['tries']} (95%: {s['right_95']}), wrong view {s['wrong_view']}, missed {s['missed']}")
    print(f"Out of sight: said so {n['said_not_seen']} of {n['tries']}, pointed at nothing {n['pointed_at_nothing']}")
    print(f"Median time to point: {card['median_to_point_s']} s; {card['unlabelled']} tries not labelled")
    out = HERE / "results" / f"finder-eval-{datetime.now():%Y-%m-%d-%H%M}.json"
    out.write_text(json.dumps(card, indent=1))
    print(f"Scorecard: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

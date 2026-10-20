"""Does zooming in find small things? The finder's own code on labelled frames, zoom off against zoom on (PLAN B44).

    uv run python evals/zoom_check.py FOLDER          FOLDER holds 1920x1080 frames and truth.json

truth.json lists each frame: {"file": ..., "glasses": true or false, "x" and "y": where they are (0..1), or for a
frame without them, optionally where they used to be}. Each frame
is read the old way (one 768-pixel copy, ANDY_FINDER_ZOOM=off) and the new way (six full-size tiles), with
andy_companion.finder.read_view and the eyes in use (vision.eyes). Then the closer look: for a frame with glasses,
the middle of a frame centred on them (as when the head has turned there); for one without, centred on what the
tiles thought they saw, if anything. A find counts only in the right place (within 0.08 of the frame's width).
The scorecard keeps file names and numbers, never the pictures.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from andy_companion import finder, vision  # noqa: E402
from andy_companion.measure import wilson  # noqa: E402


def centred(frame, x, y):
    """A frame-sized picture centred on (x, y), as if the head had turned there (edges padded by reflection)."""
    import cv2

    h, w = frame.shape[:2]
    big = cv2.copyMakeBorder(frame, h // 2, h // 2, w // 2, w // 2, cv2.BORDER_REFLECT)
    cx, cy = int(x * w) + w // 2, int(y * h) + h // 2
    return big[cy - h // 2:cy - h // 2 + h, cx - w // 2:cx - w // 2 + w]


def one(path: Path, t: dict) -> dict:
    import cv2

    frame = cv2.imread(str(path))
    row = {"file": t["file"], "glasses": bool(t["glasses"])}
    for mode in ("off", "on"):
        os.environ["ANDY_FINDER_ZOOM"] = mode
        start = time.monotonic()
        out = finder.read_view(frame, "glasses", finder.ask)
        hit = out["seen"] and t["glasses"] and abs(out["x"] - t["x"]) <= 0.08
        row[mode] = {"seen": out["seen"], "right_place": bool(hit), "x": round(out["x"], 3), "s": round(time.monotonic() - start, 2)}
    os.environ["ANDY_FINDER_ZOOM"] = "on"
    # Without glasses: centred on what the tiles thought they saw; or, when the frame says where they used to be
    # ("x" on a frame without them: the same spot, painted out), there, the hardest place to say no.
    if t["glasses"] or "x" in t:
        at = (t["x"], t.get("y", 0.5))
    else:
        at = (row["on"]["x"], 0.5) if row["on"]["seen"] else None
    if at:
        start = time.monotonic()
        checked = finder.look_closer(centred(frame, *at), "glasses")
        row["closer"] = {"yes": checked["yes"], "s": round(time.monotonic() - start, 2)}
    return row


def summary(rows: list) -> dict:
    pos = [r for r in rows if r["glasses"]]
    neg = [r for r in rows if not r["glasses"]]
    out = {}
    for mode in ("off", "on"):
        k = sum(r[mode]["right_place"] for r in pos)
        fp = sum(r[mode]["seen"] for r in neg)
        out[mode] = {"found": k, "of": len(pos), "found_95": [round(v * 100, 1) for v in wilson(k, len(pos))] if pos else None,
                     "false_sightings": fp, "of_without": len(neg),
                     "median_s": sorted(r[mode]["s"] for r in rows)[len(rows) // 2]}
    yes_pos = sum(1 for r in pos if r.get("closer", {}).get("yes"))
    checked_neg = [r for r in neg if "closer" in r]
    out["closer"] = {"confirmed": yes_pos, "of": len(pos), "wrongly_confirmed": sum(r["closer"]["yes"] for r in checked_neg),
                     "of_checked_without": len(checked_neg)}
    found_and_confirmed = sum(1 for r in pos if r["on"]["right_place"] and r.get("closer", {}).get("yes"))
    out["end_to_end"] = {"found_and_confirmed": found_and_confirmed, "of": len(pos),
                         "false_finds": sum(1 for r in checked_neg if r["closer"]["yes"])}
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    folder = Path(sys.argv[1]).expanduser()
    truth = json.loads((folder / "truth.json").read_text())
    rows = [one(folder / t["file"], t) for t in truth]
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), "eyes": vision.name(),
            "frames": len(rows), "summary": summary(rows), "rows": rows}
    s = card["summary"]
    print(f"zoom off: right place {s['off']['found']}/{s['off']['of']}, false sightings {s['off']['false_sightings']}/{s['off']['of_without']}")
    print(f"zoom on:  right place {s['on']['found']}/{s['on']['of']} {s['on']['found_95']}, false sightings {s['on']['false_sightings']}/{s['on']['of_without']}")
    print(f"closer:   confirmed {s['closer']['confirmed']}/{s['closer']['of']}, wrongly confirmed {s['closer']['wrongly_confirmed']}/{s['closer']['of_checked_without']}")
    out = HERE / "results" / f"zoom-check-{datetime.now():%Y-%m-%d-%H%M}.json"
    out.write_text(json.dumps(card, indent=1) + "\n")
    print(f"Scorecard: {out.relative_to(HERE.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

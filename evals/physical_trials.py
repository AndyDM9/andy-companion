"""Plan and score 30 real finder trials without storing speech or pictures.

  uv run python evals/physical_trials.py init /tmp/andy-trials.csv
  uv run python evals/physical_trials.py record /tmp/andy-trials.csv 1 --outcome found --seconds 18
  uv run python evals/physical_trials.py score /tmp/andy-trials.csv --out /tmp/andy-scorecard.json

Place the object as the row asks; ask Andy normally. Time from the end of your
question until it points or finishes saying it could not find it. Record every
attempt in order. Use absent for a correct response when the object is not there,
and false_find if Andy claims to find it anyway. No free-text notes are accepted.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from andy_companion.measure import percentile, wilson

FIELDS = ("trial", "object", "position", "light", "present", "outcome", "seconds")
PRESENT = {"found", "missed", "wrong_point", "error"}
ABSENT = {"absent", "false_find", "error"}


def plan():
    objects = ("glasses", "keys", "remote")
    positions = ("centre", "left", "right", "side_70_90_degrees", "lower_shelf")
    return [{"trial": str(i + 1), "object": objects[i % 3], "position": positions[i % 5],
             "light": "ordinary" if i < 15 else "dim",
             "present": "0" if (i // 3 + i % 3) % 3 == 2 else "1",
             "outcome": "", "seconds": ""} for i in range(30)]


def read(path):
    with Path(path).open(newline="") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or []) != FIELDS:
            raise ValueError("Use the CSV made by init, with its columns unchanged.")
        rows = list(reader)
    expected = plan()
    if len(rows) != len(expected):
        raise ValueError("Keep all 30 planned attempts, including errors and misses.")
    for row, original in zip(rows, expected, strict=True):
        if any(row[k] != original[k] for k in FIELDS[:5]):
            raise ValueError("Do not change the planned trial, object, position, light or presence.")
        allowed = PRESENT if row["present"] == "1" else ABSENT
        if row["outcome"]:
            if row["outcome"] not in allowed:
                raise ValueError("Choose an outcome appropriate to whether the object was present.")
            try:
                seconds = float(row["seconds"])
            except (TypeError, ValueError):
                raise ValueError("Each recorded attempt needs its elapsed seconds.") from None
            if not math.isfinite(seconds) or not 0 < seconds <= 600:
                raise ValueError("Seconds must be finite, greater than zero and at most 600.")
        elif row["seconds"]:
            raise ValueError("A time needs an outcome.")
    return rows


def write(path, rows):
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def score(rows):
    completed = [r for r in rows if r["outcome"]]
    if len(completed) != 30:
        raise ValueError(f"Only {len(completed)} of 30 recorded. Finish the plan; no incomplete success rate is published.")
    present = [r for r in rows if r["present"] == "1"]
    absent = [r for r in rows if r["present"] == "0"]
    found = sum(r["outcome"] == "found" for r in present)
    false = sum(r["outcome"] == "false_find" for r in absent)
    times = [float(r["seconds"]) for r in rows]
    return {"ran": datetime.now().astimezone().isoformat(timespec="seconds"),
            "scope": "30 physical robot attempts; manually scored and timed from end of question to point or final answer; no audio or images kept",
            "planned": 30, "completed": 30,
            "present": {"trials": len(present), "found": found, "rate_95_interval": wilson(found, len(present)),
                        "missed": sum(r["outcome"] == "missed" for r in present),
                        "wrong_point": sum(r["outcome"] == "wrong_point" for r in present)},
            "absent": {"trials": len(absent), "false_find": false, "false_find_95_interval": wilson(false, len(absent))},
            "errors": sum(r["outcome"] == "error" for r in rows),
            "seconds": {"p50": percentile(times, 50), "p95": percentile(times, 95), "max": max(times)},
            "trials": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("csv", type=Path)
    record = sub.add_parser("record"); record.add_argument("csv", type=Path)
    record.add_argument("trial", type=int); record.add_argument("--outcome", required=True, choices=sorted(PRESENT | ABSENT))
    record.add_argument("--seconds", required=True, type=float)
    report = sub.add_parser("score"); report.add_argument("csv", type=Path); report.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            if args.csv.exists():
                raise ValueError("That file exists. Choose a new path to preserve previous attempts.")
            write(args.csv, plan())
            print("30 planned attempts: 20 present, 10 absent. No speech or pictures will be stored.")
        elif args.command == "record":
            rows = read(args.csv)
            if not 1 <= args.trial <= len(rows):
                raise ValueError("Trial must be 1 to 30.")
            row = rows[args.trial - 1]
            if row["outcome"]:
                raise ValueError("That attempt is already recorded. Keep it; do not replace failures.")
            row.update(outcome=args.outcome, seconds=str(args.seconds))
            # Validate the entire revised sheet before replacing the previous version.
            allowed = PRESENT if row["present"] == "1" else ABSENT
            if row["outcome"] not in allowed or not math.isfinite(args.seconds) or not 0 < args.seconds <= 600:
                raise ValueError("Check the outcome and seconds for this attempt.")
            if any(not r["outcome"] for r in rows[:args.trial - 1]):
                raise ValueError("Record attempts in order.")
            write(args.csv, rows)
            print(f"Recorded attempt {args.trial} of 30.")
        else:
            card = score(read(args.csv))
            revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
            card["commit"] = revision.stdout.strip() if revision.returncode == 0 else "unknown"
            card["working_tree_changed"] = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout)
            args.out.write_text(json.dumps(card, indent=2) + "\n")
            print(f"Found {card['present']['found']}/20; false finds {card['absent']['false_find']}/10; errors {card['errors']}.")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

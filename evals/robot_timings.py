"""How fast Andy answers on the robot (PLAN B34): every real turn's timing from Andy's own log, numbers only.

    uv run python evals/robot_timings.py            reads `journalctl --user -u andy`, writes a scorecard

Pollen's conversation app logs, for each turn on the Reachy Mini, two numbers after the person's words are
understood (the transcript from NVIDIA Parakeet): when Nemotron 3.5 Lightning's reply started on Token
Factory ("response.created") and when Andy's first sound started ("first audio delta"). Only those lines are
read; the log holds no words (decision 0003), and the scorecard keeps only dates and milliseconds. Turns
with a tool (the weather, a search) are in the same numbers: the log doesn't say which turn used one.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from andy_companion.measure import percentile  # noqa: E402

LINE = re.compile(r"^(\d{4}-\d{2}-\d{2})T\S+ .*Turn latency: (response\.created|first audio delta) (\d+) ms after user transcript")
NAMES = {"response.created": "reply_started_ms", "first audio delta": "first_sound_ms"}


def parse(lines) -> dict:
    """{'first_sound_ms': [(day, ms), ...], 'reply_started_ms': [...]} from the journal's lines."""
    out = {v: [] for v in NAMES.values()}
    for line in lines:
        m = LINE.match(line)
        if m:
            out[NAMES[m.group(2)]].append((m.group(1), int(m.group(3))))
    return out


def summary(found: dict) -> dict:
    card = {}
    for name, rows in found.items():
        ms = [v for _, v in rows]
        card[name] = {"turns": len(ms), "p50": percentile(ms, 50), "p90": percentile(ms, 90),
                      "p95": percentile(ms, 95), "max": max(ms) if ms else None,
                      "days": sorted({d for d, _ in rows})}
    return card


def main() -> int:
    log = subprocess.run(["journalctl", "--user", "-u", "andy", "-o", "short-iso", "--no-pager"],
                         capture_output=True, text=True).stdout.splitlines()
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"),
            "what": "Reachy Mini Lite, real turns; from the transcript (NVIDIA Parakeet) to Nemotron 3.5 Lightning's "
                    "reply starting and to Andy's first sound (Qwen3-TTS); tool turns included",
            **summary(parse(log))}
    f = card["first_sound_ms"]
    if not f["turns"]:
        print("No turn timings in the log yet: talk with Andy on the robot first.")
        return 1
    print(f"{f['turns']} turns on {', '.join(f['days'])}: first sound p50 {f['p50']} ms, p90 {f['p90']} ms, "
          f"p95 {f['p95']} ms, slowest {f['max']} ms")
    out = HERE / "results" / f"robot-timings-{datetime.now():%Y-%m-%d-%H%M}.json"
    out.write_text(json.dumps(card, indent=1) + "\n")
    print(f"Scorecard: {out.relative_to(HERE.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

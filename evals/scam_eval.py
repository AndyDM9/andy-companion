"""Does Tavily make Andy's scam check better? A measured answer, with real Tavily calls.

    uv run python evals/scam_eval.py --spend      (needs NEBIUS_API_KEY and TAVILY_API_KEY)

It spends about 160 Tavily credits a run (80 advanced searches), so it runs only with --spend. On
2026-10-14, five runs while tuning used up the free plan's 1,000 a month: check the balance first.

Each of the 80 messages in scam_messages.json (40 carrying known scam signs, 40 ordinary, Spanish
among both; 20 of them hard on purpose) is judged two ways by NVIDIA Nemotron 3.5 Lightning on Token Factory, with a strict JSON
schema:

- **alone:** the message only;
- **with Tavily:** Andy's real check first (andy_companion.web.check_message: numbers, links and
  emails removed, then an advanced Tavily search of consumer-protection sites), and the model judges
  with those warnings in hand, naming the source it relied on.

Both use andy_companion.scamcheck, as Andy's tool does: the model names the sign it sees and quotes the
message's words for it, and code accepts the sign only if those words are in the message. It reports, for
each: scams caught, ordinary messages wrongly flagged, and, with Tavily, how many scam
verdicts are backed by a named consumer-protection source (what Andy can say aloud: "the FTC warns
about this"). About 160 Tavily credits a run (advanced depth). The scorecard goes to evals/results/.
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from andy_companion import web  # noqa: E402

from andy_companion import scamcheck  # noqa: E402

MODEL = scamcheck.MODEL


def judge(message: str, warnings=None) -> dict:
    for attempt in range(3):
        try:
            return scamcheck.verdict(message, warnings)
        except scamcheck.ScamCheckError:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    return {}


def one(m: dict) -> dict:
    alone = judge(m["text"])
    t = time.time()
    warnings = []
    for attempt in range(4):           # the free plan limits bursts (HTTP 429): wait and try again
        try:
            warnings = web.check_message(m["text"])
            break
        except web.WebError:
            time.sleep(8 * (attempt + 1))
    tavily_s = time.time() - t
    with_tavily = judge(m["text"], warnings)
    sources = {w.get("source", "") for w in warnings}
    cited = str(with_tavily.get("source", "")).strip()
    backed = bool(cited) and any(cited.lower() in s.lower() or s.lower() in cited.lower() for s in sources if s)
    return {"id": m["id"], "scam": m["scam"], "alone": bool(alone.get("scam_signs")),
            "with_tavily": bool(with_tavily.get("scam_signs")), "sign": with_tavily.get("sign"),
            "warnings": len(warnings), "sources": sorted(s for s in sources if s), "cited": cited, "backed": backed,
            "tavily_s": round(tavily_s, 2)}


def score(rows, key):
    scams = [r for r in rows if r["scam"]]
    ordinary = [r for r in rows if not r["scam"]]
    caught = sum(r[key] for r in scams)
    false_alarms = sum(r[key] for r in ordinary)
    return {"scams_caught": caught, "of_scams": len(scams), "false_alarms": false_alarms, "of_ordinary": len(ordinary)}


def main() -> int:
    if not (os.environ.get("NEBIUS_API_KEY") and os.environ.get("TAVILY_API_KEY")):
        print("Needs NEBIUS_API_KEY and TAVILY_API_KEY.")
        return 2
    if "--spend" not in sys.argv:
        print("This run uses about 160 Tavily credits (80 searches at advanced depth). Check the balance, then run "
              "again with --spend.")
        return 2
    data = json.loads((HERE / "scam_messages.json").read_text())
    with cf.ThreadPoolExecutor(max_workers=2) as pool:   # gentle on Tavily's rate limit
        rows = list(pool.map(one, data["messages"]))
    alone, with_t = score(rows, "alone"), score(rows, "with_tavily")
    scam_verdicts = [r for r in rows if r["scam"] and r["with_tavily"]]
    backed = sum(r["backed"] for r in scam_verdicts)
    with_warnings = sum(1 for r in rows if r["scam"] and r["warnings"])
    hard = [r for r in rows if r["id"].startswith("h")]
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), "model": MODEL,
            # "alone" is the first model only; "with_tavily" adds Tavily's warnings and the second model's match.
            "match_model": scamcheck.MATCH_MODEL, "messages": len(rows), "alone": alone, "with_tavily": with_t,
            "scams_with_warnings_found": with_warnings, "hard_alone": score(hard, "alone"),
            "hard_with_tavily": score(hard, "with_tavily"),
            "scam_verdicts_backed_by_a_named_source": backed, "of_scam_verdicts": len(scam_verdicts),
            "median_tavily_s": sorted(r["tavily_s"] for r in rows)[len(rows) // 2], "rows": rows}
    out = HERE / "results" / f"scam-eval-{datetime.now():%Y-%m-%d-%H%M}.json"
    out.write_text(json.dumps(card, indent=1, ensure_ascii=False))
    print(f"Scam check, {len(rows)} messages ({MODEL}):")
    for name, s in (("alone", alone), ("with Tavily", with_t)):
        print(f"  {name:12} scams caught {s['scams_caught']}/{s['of_scams']}, ordinary flagged {s['false_alarms']}/{s['of_ordinary']}")
    for name, key in (("hard, alone", "hard_alone"), ("hard, Tavily", "hard_with_tavily")):
        h = card[key]
        print(f"  {name:12} scams caught {h['scams_caught']}/{h['of_scams']}, ordinary flagged {h['false_alarms']}/{h['of_ordinary']}")
    print(f"  with Tavily, warnings found for {with_warnings}/{alone['of_scams']} scams; {backed}/{len(scam_verdicts)} scam verdicts "
          f"name a consumer-protection source; median search {card['median_tavily_s']} s")
    print(f"Scorecard: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

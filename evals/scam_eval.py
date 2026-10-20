"""Does Tavily make Andy's scam check better, and is it Tavily or a bigger model? Measured with real calls.

    uv run python evals/scam_eval.py --lookup --spend     Tavily, once per message: the warnings are saved
    uv run python evals/scam_eval.py --warnings FILE --runs 3      the models only, no Tavily
    uv run python evals/scam_eval.py --word-rules       the baseline with no model and no web (no calls)
    cloud/scam-job.sh FILE                      the same as four Nebius Serverless Jobs, a quarter of the
                                                messages each (a job's request may hold 64 KB), merged

Each of the 120 messages in scam_messages.json is judged four ways, with strict JSON schemas and the same code
as Andy's tool (andy_companion.scamcheck: the model names the sign it sees and quotes the message's words for
it, and code accepts the sign only if those words are in the message):

- **lightning:** NVIDIA Nemotron 3.5 Lightning, the message alone;
- **ultra:** NVIDIA Nemotron 3 Ultra, the message alone: is a bigger model enough without the web?
- **tavily_lightning:** Lightning, then Tavily's consumer-protection warnings matched by Lightning: what Tavily
  adds with the model held the same;
- **tavily_ultra:** Andy's real check: Lightning, then the warnings matched by Ultra.

The warnings come from andy_companion.web.check_message (numbers, links and emails removed, then an advanced
Tavily search of consumer-protection sites), fetched once per message and saved (`--lookup`, about 240 credits
for 120 messages, so it runs only with --spend; on 2026-10-14 five runs while tuning used up a month's free
credits). The models then run as many times as asked against the same warnings, so the runs measure the models'
variation and the Tavily calls are paid once.

The messages: s, g and h (80) were written while the check was built; r and o (40) were added after it was
frozen, modelled on warnings published July to October 2026, so they are held out. Each arm reports scams
caught and ordinary messages flagged, overall, for the subtle ones (h) and for the held-out ones (r, o), as the
mean and range over runs, plus how many of the full check's scam verdicts name the source Andy says aloud.
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from andy_companion import scamcheck  # noqa: E402

LIGHTNING, ULTRA = scamcheck.MODEL, scamcheck.MATCH_MODEL
ARMS = {"lightning": (LIGHTNING, None, False), "ultra": (ULTRA, None, False),
        "tavily_lightning": (LIGHTNING, LIGHTNING, True), "tavily_ultra": (LIGHTNING, ULTRA, True)}
GROUPS = {"all": lambda m: True, "subtle (h)": lambda m: m["id"].startswith("h"),
          "held out (r, o)": lambda m: bool(m.get("recent"))}


def messages() -> list:
    return json.loads((HERE / "scam_messages.json").read_text())["messages"]


def lookup(m: dict) -> dict:
    from andy_companion import web

    t = time.time()
    for attempt in range(4):           # bursts can meet HTTP 429: wait and try again
        try:
            return {"id": m["id"], "warnings": web.check_message(m["text"]), "tavily_s": round(time.time() - t, 2)}
        except web.WebError:
            time.sleep(8 * (attempt + 1))
    return {"id": m["id"], "warnings": [], "tavily_s": round(time.time() - t, 2), "failed": True}


def judge(m: dict, warnings: list, arm: str) -> dict:
    model, match_model, with_web = ARMS[arm]
    for attempt in range(3):
        try:
            v = scamcheck.verdict(m["text"], warnings if with_web else None, model=model,
                                  match_model=match_model or ULTRA)
            return {"flagged": bool(v.get("scam_signs")), "source": v.get("source", "")}
        except scamcheck.ScamCheckError:
            time.sleep(2 * (attempt + 1))
    return {"flagged": False, "source": "", "error": True}


def score(rows: list, msgs: dict, arm: str, group) -> dict:
    # An answer that failed (the model's JSON never closed, a timeout) is neither caught nor flagged: it is
    # left out of that arm's totals and counted apart (2026-10-14 review: 17 failed Ultra answers had been
    # scored as correct "not flagged").
    chosen = [r for r in rows if group(msgs[r["id"]]) and not r[arm].get("error")]
    scams = [r for r in chosen if msgs[r["id"]]["scam"]]
    ordinary = [r for r in chosen if not msgs[r["id"]]["scam"]]
    return {"caught": sum(r[arm]["flagged"] for r in scams), "of_scams": len(scams),
            "flagged": sum(r[arm]["flagged"] for r in ordinary), "of_ordinary": len(ordinary),
            "failed": sum(1 for r in rows if group(msgs[r["id"]]) and r[arm].get("error"))}


def one_run(msgs: list, warnings: dict, workers: int = 4) -> list:
    def row(m):
        w = warnings.get(m["id"], [])
        return {"id": m["id"], **{arm: judge(m, w, arm) for arm in ARMS}}
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(row, msgs))


def summary(runs: list, msgs: list, warnings: dict) -> dict:
    by_id = {m["id"]: m for m in msgs}
    out = {}
    for arm in ARMS:
        out[arm] = {}
        for gname, group in GROUPS.items():
            per_run = [score(rows, by_id, arm, group) for rows in runs]
            caught = [s["caught"] for s in per_run]
            flagged = [s["flagged"] for s in per_run]
            out[arm][gname] = {"of_scams": round(sum(s["of_scams"] for s in per_run) / len(per_run), 2),
                               "of_ordinary": round(sum(s["of_ordinary"] for s in per_run) / len(per_run), 2),
                               "failed": sum(s["failed"] for s in per_run),
                               "caught_mean": round(sum(caught) / len(caught), 2), "caught_range": [min(caught), max(caught)],
                               "flagged_mean": round(sum(flagged) / len(flagged), 2), "flagged_range": [min(flagged), max(flagged)]}
    full = [r["tavily_ultra"] for rows in runs for r in rows if by_id[r["id"]]["scam"] and r["tavily_ultra"]["flagged"]]
    out["full_check_scam_verdicts_naming_a_source"] = [sum(1 for v in full if v["source"]), len(full)]
    out["scams_with_warnings_found"] = [sum(1 for m in msgs if m["scam"] and warnings.get(m["id"])),
                                        sum(1 for m in msgs if m["scam"])]
    return out


# What one check costs (PLAN B33), measured 2026-10-20 on four of the messages: Lightning about 180 tokens in and
# 65 out, Ultra about 560 in and 10 out, and one advanced Tavily search (2 credits). Prices of 2026-10-14
# (docs/cost.md): Lightning $0.06 and $0.24 per million tokens in and out, Ultra $1.00 and $3.00, Tavily $0.008 a
# credit on pay-as-you-go.
COST = {"tavily_usd": 2 * 0.008, "models_usd": (180 * 0.06 + 65 * 0.24 + 560 * 1.00 + 10 * 3.00) / 1e6,
        "measured": "2026-10-20", "prices": "2026-10-14"}


def per_thousand() -> dict:
    """The cost of 1,000 of Andy's scam checks, in US dollars, split into Tavily and the two Nemotron calls."""
    return {"tavily": round(COST["tavily_usd"] * 1000, 2), "models": round(COST["models_usd"] * 1000, 2),
            "total": round((COST["tavily_usd"] + COST["models_usd"]) * 1000, 2)}


def word_rules(msgs: list) -> dict:
    """The baseline with no model and no web: Andy's own warning-sign rules for paper letters (letters.SIGNS:
    gift cards, wire transfers, crypto, arrest, cut-offs, "act now", passwords, prizes), on the same messages,
    in the summary's shape. Deterministic, so one run."""
    from andy_companion import letters

    rows = [{"id": m["id"], "word_rules": {"flagged": bool(letters.warning_signs(m["text"])), "source": ""}}
            for m in msgs]
    by_id = {m["id"]: m for m in msgs}
    out = {}
    for gname, group in GROUPS.items():
        sc = score(rows, by_id, "word_rules", group)
        out[gname] = {"of_scams": sc["of_scams"], "of_ordinary": sc["of_ordinary"], "failed": 0,
                      "caught_mean": sc["caught"], "caught_range": [sc["caught"]] * 2,
                      "flagged_mean": sc["flagged"], "flagged_range": [sc["flagged"]] * 2}
    return out


def show(card: dict) -> None:
    names = {"lightning": "Lightning alone", "ultra": "Ultra alone", "tavily_lightning": "Tavily + Lightning",
             "tavily_ultra": "Tavily + Ultra (Andy)"}
    print(f"Scam check, {card['messages']} messages, {card['runs']} runs (mean, range):")
    for gname in GROUPS:
        print(f"  {gname}")
        for arm, label in names.items():
            s = card["summary"][arm][gname]
            failed = f", {s['failed']} answers failed (left out)" if s.get("failed") else ""
            print(f"    {label:22} caught {s['caught_mean']:>5}/{s['of_scams']} {s['caught_range']}, "
                  f"ordinary flagged {s['flagged_mean']:>4}/{s['of_ordinary']} {s['flagged_range']}{failed}")
    named, of = card["summary"]["full_check_scam_verdicts_naming_a_source"]
    found, scams = card["summary"]["scams_with_warnings_found"]
    print(f"  Andy's check named a consumer-protection source in {named} of {of} scam verdicts; "
          f"Tavily found warnings for {found} of {scams} scams")


def main() -> int:
    args = sys.argv[1:]
    if "--word-rules" in args:      # no model, no web: nothing to pay for
        msgs = messages()
        card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), "messages": len(msgs),
                "what": "Andy's warning-sign rules for letters (andy_companion.letters.SIGNS), no model and no web",
                "summary": {"word_rules": word_rules(msgs)}, "cost_per_1000_checks_usd": per_thousand(), "cost": COST}
        s = card["summary"]["word_rules"]["all"]
        print(f"Word rules alone: caught {s['caught_mean']} of {s['of_scams']}, flagged {s['flagged_mean']} of "
              f"{s['of_ordinary']} ordinary. Andy's check costs about ${card['cost_per_1000_checks_usd']['total']} "
              "per 1,000 at pay-as-you-go prices")
        out = HERE / "results" / f"scam-word-rules-{datetime.now():%Y-%m-%d-%H%M}.json"
        out.write_text(json.dumps(card, indent=1) + "\n")
        print(f"Scorecard: {out}")
        return 0
    if not os.environ.get("NEBIUS_API_KEY") and not {"--lookup", "--merge", "--rescore"} & set(args):
        print("Needs NEBIUS_API_KEY.")
        return 2
    msgs = messages()
    results = HERE / "results"
    if "--lookup" in args:
        if not os.environ.get("TAVILY_API_KEY"):
            print("Needs TAVILY_API_KEY.")
            return 2
        if "--spend" not in args:
            print(f"This makes {len(msgs)} advanced Tavily searches (about {2 * len(msgs)} credits). Check the balance, "
                  "then run again with --spend.")
            return 2
        with cf.ThreadPoolExecutor(max_workers=2) as pool:      # gentle on Tavily's rate limit
            found = list(pool.map(lookup, msgs))
        out = results / f"scam-warnings-{datetime.now():%Y-%m-%d-%H%M}.json"
        out.write_text(json.dumps({"fetched": datetime.now().astimezone().isoformat(timespec="seconds"),
                                   "messages": found}, indent=1, ensure_ascii=False))
        failed = sum(1 for f in found if f.get("failed"))
        print(f"Warnings for {len(found)} messages ({failed} lookups failed), median search "
              f"{sorted(f['tavily_s'] for f in found)[len(found) // 2]} s: {out}")
        return 0
    if "--rescore" in args:      # a scorecard's summary worked out again from its own rows; no model calls
        path = Path(args[args.index("--rescore") + 1])
        card = json.loads(path.read_text())
        seen = {r["id"] for r in card["rows"][0]}
        wfile = HERE / "results" / card.get("warnings_file", "")
        found = ({f["id"]: f["warnings"] for f in json.loads(wfile.read_text())["messages"]} if wfile.is_file()
                 else {k: [1] * v for k, v in card.get("warnings_found", {}).items()})
        card["summary"] = summary(card["rows"], [m for m in msgs if m["id"] in seen], found)
        path.write_text(json.dumps(card, indent=1, ensure_ascii=False))
        show(card)
        return 0
    if "--merge" in args:
        return merge([Path(a) for a in args[args.index("--merge") + 1:]], msgs)
    if "--warnings" not in args:
        print(__doc__)
        return 2
    if "--part" in args:                              # "1/2": every second message, from the first
        k, n_parts = (int(x) for x in args[args.index("--part") + 1].split("/"))
        msgs = msgs[k - 1::n_parts]
    wfile = Path(args[args.index("--warnings") + 1])
    warnings = {f["id"]: f["warnings"] for f in json.loads(wfile.read_text())["messages"]}
    n = int(args[args.index("--runs") + 1]) if "--runs" in args else 1
    started = time.time()
    runs = [one_run(msgs, warnings) for _ in range(n)]
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), "models": {"lightning": LIGHTNING, "ultra": ULTRA},
            "warnings_file": wfile.name, "messages": len(msgs), "runs": n, "minutes": round((time.time() - started) / 60, 1),
            "errors": sum(1 for rows in runs for r in rows for arm in ARMS if r[arm].get("error")),
            "warnings_found": {m["id"]: len(warnings.get(m["id"], [])) for m in msgs},
            "summary": summary(runs, msgs, warnings), "rows": runs}
    show(card)
    if os.environ.get("ANDY_IN_JOB"):
        # A job's log cuts lines at 16,384 characters and may not keep their order (2026-10-14), so the
        # scorecard goes out in short numbered chunks that cloud/scam-job.sh puts back together.
        text = json.dumps(card, ensure_ascii=False)
        chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
        for i, chunk in enumerate(chunks, 1):
            print(f"SCORECARD_CHUNK {i}/{len(chunks)} {chunk}", flush=True)
    else:
        out = results / f"scam-eval-{datetime.now():%Y-%m-%d-%H%M}.json"
        out.write_text(json.dumps(card, indent=1, ensure_ascii=False))
        print(f"Scorecard: {out}")
    return 0


def merge(cards: list, msgs: list, out: Optional[Path] = None) -> int:
    """One scorecard from the parts' scorecards (the same runs, different messages)."""
    parts = [json.loads(c.read_text()) for c in cards]
    runs = [sum((p["rows"][i] for p in parts), []) for i in range(min(p["runs"] for p in parts))]
    seen = {r["id"] for r in runs[0]}
    msgs = [m for m in msgs if m["id"] in seen]
    warnings = {}
    for p in parts:
        warnings.update(p.get("warnings_found", {}))
    card = {**{k: parts[0][k] for k in ("ran", "models", "warnings_file")}, "messages": len(msgs), "runs": len(runs),
            "minutes": max(p["minutes"] for p in parts), "errors": sum(p["errors"] for p in parts),
            "ran_on": parts[0].get("ran_on", ""), "jobs": [p.get("job", "") for p in parts],
            "warnings_found": warnings,
            "summary": summary(runs, msgs, {k: [1] * v for k, v in warnings.items()}), "rows": runs}
    show(card)
    out = out or HERE / "results" / f"scam-eval-{datetime.now():%Y-%m-%d-%H%M}-nebius-jobs.json"
    out.write_text(json.dumps(card, indent=1, ensure_ascii=False))
    print(f"Scorecard: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

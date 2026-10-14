"""The scam evaluation's messages and arithmetic (evals/scam_eval.py); no model or Tavily calls."""

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scam_eval", ROOT / "evals" / "scam_eval.py")
scam_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scam_eval)


def test_the_messages_are_balanced_held_out_and_name_no_one_real():
    msgs = scam_eval.messages()
    ids = [m["id"] for m in msgs]
    assert len(ids) == len(set(ids)) == 120
    assert sum(m["scam"] for m in msgs) == 60
    held = [m for m in msgs if m.get("recent")]
    assert len(held) == 40 and {m["id"][0] for m in held} == {"r", "o"}
    assert sum(m["scam"] for m in held) == 20
    for m in msgs:                      # no real phone numbers or links in a public test set
        assert not re.search(r"\d{3}[-. ]\d{3}[-. ]\d{4}|https?://|www\.", m["text"]), m["id"]


def test_four_arms_tell_tavily_from_a_bigger_model():
    arms = scam_eval.ARMS
    assert arms["lightning"] == (scam_eval.LIGHTNING, None, False)
    assert arms["ultra"] == (scam_eval.ULTRA, None, False)                  # a bigger model, no web
    assert arms["tavily_lightning"] == (scam_eval.LIGHTNING, scam_eval.LIGHTNING, True)   # the web, same model
    assert arms["tavily_ultra"] == (scam_eval.LIGHTNING, scam_eval.ULTRA, True)          # Andy's real check


def rows(flags):
    return [{"id": i, **{arm: {"flagged": f, "source": "consumer.ftc.gov" if f else ""} for arm in scam_eval.ARMS}}
            for i, f in flags.items()]


def test_the_summary_gives_mean_and_range_over_runs():
    msgs = [{"id": "s01", "scam": True}, {"id": "h01", "scam": True}, {"id": "g01", "scam": False},
            {"id": "r01", "scam": True, "recent": True}]
    runs = [rows({"s01": True, "h01": False, "g01": False, "r01": True}),
            rows({"s01": True, "h01": True, "g01": True, "r01": True})]
    out = scam_eval.summary(runs, msgs, {"s01": [1], "r01": [1]})
    a = out["tavily_ultra"]["all"]
    assert (a["caught_mean"], a["caught_range"], a["of_scams"]) == (2.5, [2, 3], 3)
    assert (a["flagged_mean"], a["flagged_range"], a["of_ordinary"]) == (0.5, [0, 1], 1)
    assert out["tavily_ultra"]["subtle (h)"]["caught_range"] == [0, 1]
    assert out["tavily_ultra"]["held out (r, o)"]["of_scams"] == 1
    assert out["scams_with_warnings_found"] == [2, 3]
    assert out["full_check_scam_verdicts_naming_a_source"] == [5, 5]


def test_parts_merge_into_one_scorecard(tmp_path, monkeypatch):
    msgs = scam_eval.messages()
    parts = []
    for k in (1, 2):
        mine = msgs[k - 1::2]
        card = {"ran": "x", "models": {}, "warnings_file": "w.json", "runs": 2, "minutes": 3.0, "errors": 0,
                "warnings_found": {m["id"]: 1 for m in mine}, "rows": [rows({m["id"]: m["scam"] for m in mine})] * 2}
        path = tmp_path / f"part{k}.json"
        path.write_text(json.dumps(card))
        parts.append(path)
    monkeypatch.setattr(scam_eval, "HERE", tmp_path)
    (tmp_path / "results").mkdir()
    assert scam_eval.merge(parts, msgs) == 0
    merged = json.loads(next((tmp_path / "results").glob("scam-eval-*-nebius-jobs.json")).read_text())
    assert merged["messages"] == 120 and merged["runs"] == 2
    assert merged["summary"]["tavily_ultra"]["all"]["caught_mean"] == 60


def test_the_lookup_spends_nothing_without_spend(monkeypatch, capsys):
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    monkeypatch.setattr("sys.argv", ["scam_eval.py", "--lookup"])
    assert scam_eval.main() == 2
    assert "--spend" in capsys.readouterr().out

"""Round 5, B33 and B34: intervals and percentiles, the robot's own turn timings (numbers only), and the
finder's saved tries read again by each of Andy's eyes."""

import importlib.util
import json
from pathlib import Path

import pytest

from andy_companion import measure

EVALS = Path(__file__).resolve().parents[1] / "evals"


def load(name):
    spec = importlib.util.spec_from_file_location(name, EVALS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_wilson_matches_the_published_figures():
    assert measure.percent_range(58, 60) == "88.6–99.1%"
    assert measure.percent_range(0, 60) == "0.0–6.0%"
    assert measure.percent_range(24, 60) == "28.6–52.6%"
    lo, hi = measure.wilson(60, 60)
    assert round(lo, 3) == 0.940 and hi == 1.0
    with pytest.raises(ValueError):
        measure.wilson(1, 0)


def test_percentiles_by_nearest_rank():
    xs = list(range(1, 101))
    assert measure.percentile(xs, 50) == 50 and measure.percentile(xs, 95) == 95 and measure.percentile(xs, 100) == 100
    assert measure.percentile([7], 95) == 7 and measure.percentile([], 50) is None


def test_robot_timings_read_only_the_timing_lines():
    rt = load("robot_timings")
    lines = [
        "2026-10-18T13:32:30-04:00 andy-dm andy[1]: 2026-10-18 13:32:30,785 INFO reachy_mini_conversation_app.huggingface_realtime:777 | Turn latency: response.created 840 ms after user transcript",
        "2026-10-18T13:32:30-04:00 andy-dm andy[1]: 2026-10-18 13:32:30,895 INFO reachy_mini_conversation_app.huggingface_realtime:848 | Turn latency: first audio delta 950 ms after user transcript",
        "2026-10-18T13:32:31-04:00 andy-dm andy[1]: INFO reachy_mini_conversation_app.console:899 | [not logged]",
        "2026-10-19T09:00:00-04:00 andy-dm andy[1]: x | Turn latency: first audio delta 1200 ms after user transcript",
    ]
    card = rt.summary(rt.parse(lines))
    assert card["first_sound_ms"] == {"turns": 2, "p50": 950, "p90": 1200, "p95": 1200, "max": 1200,
                                      "days": ["2026-10-18", "2026-10-19"]}
    assert card["reply_started_ms"]["turns"] == 1
    assert "not logged" not in json.dumps(card)


def test_compare_scores_each_eyes_on_the_same_saved_views(tmp_path):
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    ev = load("finder_eval")
    for name, truth in (("try-1", "2"), ("try-2", "none")):
        d = tmp_path / name
        d.mkdir()
        for i in range(4):
            shade = i * 60 if truth != "none" else 10      # the second try has nothing to find
            cv2.imwrite(str(d / f"view-{i}.jpg"), np.full((16, 16, 3), shade, np.uint8))
        (d / "try.json").write_text(json.dumps({"what": "glasses", "results": [{}] * 4, "chosen": None}))
    (tmp_path / "labels.csv").write_text("try-1,2\ntry-2,none\n")

    def sharp(frame, what):          # sees it only in the brightest-but-one view (view 2), as labelled
        return {"seen": int(frame[0, 0, 0]) in range(110, 130), "x": 0.5, "where": "on the table"}

    def blind(frame, what):
        return {"seen": False, "x": 0.5, "where": ""}

    card = ev.compare(tmp_path, ["token-factory"], asker=sharp)["eyes"]["token-factory"]
    assert card["in_sight"]["right"] == 1 and card["out_of_sight"]["said_not_seen"] == 1
    assert card["views_right"] == 8 and card["views"] == 8
    card = ev.compare(tmp_path, ["endpoint"], asker=blind)["eyes"]["endpoint"]
    assert card["in_sight"]["missed"] == 1 and card["views_right"] == 7


def test_the_word_rules_baseline_and_the_cost_per_thousand():
    ev = load("scam_eval")
    s = ev.word_rules(ev.messages())["all"]
    assert (s["caught_mean"], s["of_scams"], s["flagged_mean"], s["of_ordinary"]) == (28, 60, 3, 60)
    cost = ev.per_thousand()
    assert cost == {"tavily": 16.0, "models": 0.62, "total": 16.62}


def test_the_chart_carries_the_baseline_intervals_and_cost():
    spec = importlib.util.spec_from_file_location("make_charts", EVALS.parent / "scripts" / "make_charts.py")
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    svg = mc.scam_chart(json.loads(mc.SCORECARD.read_text()), json.loads(mc.BASELINE.read_text()))
    assert "Word rules alone" in svg and "89–99%" in svg and "0–6%" in svg and "$17 per 1,000" in svg
    assert svg == mc.OUT.read_text()          # the committed chart is the one the scorecards draw

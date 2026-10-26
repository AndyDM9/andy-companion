import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("physical_trials", Path(__file__).resolve().parents[1] / "evals" / "physical_trials.py")
trials = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trials)


def test_each_object_has_present_and_absent_trials_and_all_positions():
    rows = trials.plan()
    for name in ("glasses", "keys", "remote"):
        selected = [row for row in rows if row["object"] == name]
        present = [row for row in selected if row["present"] == "1"]
        assert len(selected) == 10
        assert len(present) in (6, 7)
        assert len({row["position"] for row in present}) == 5
        for presence in ("0", "1"):
            assert {row["light"] for row in selected if row["present"] == presence} == {"ordinary", "dim"}
        for position in {row["position"] for row in selected}:
            assert {row["light"] for row in selected if row["position"] == position} == {"ordinary", "dim"}


def test_all_planned_trials_count_including_errors_and_wrong_points():
    rows = trials.plan()
    for row in rows:
        row.update(outcome="found" if row["present"] == "1" else "absent", seconds="18")
    rows[0]["outcome"] = "error"
    rows[1]["outcome"] = "wrong_point"
    rows[2]["outcome"] = "false_find"
    card = trials.score(rows)
    assert card["present"]["trials"] == 20 and card["present"]["found"] == 18
    assert card["absent"]["trials"] == 10 and card["absent"]["false_find"] == 1
    assert card["errors"] == 1 and card["seconds"]["p95"] == 18


def test_incomplete_or_changed_plans_cannot_publish_a_rate(tmp_path):
    path = tmp_path / "trials.csv"
    rows = trials.plan()
    trials.write(path, rows)
    with pytest.raises(ValueError, match="Only 0"):
        trials.score(trials.read(path))
    rows.pop()
    trials.write(path, rows)
    with pytest.raises(ValueError, match="Keep all 30"):
        trials.read(path)


@pytest.mark.parametrize("bad", ["nan", "inf", "-1", "0", "601", "private words"])
def test_bad_times_and_free_text_are_rejected(tmp_path, bad):
    path = tmp_path / "trials.csv"
    rows = trials.plan()
    rows[0].update(outcome="found", seconds=bad)
    trials.write(path, rows)
    with pytest.raises(ValueError):
        trials.read(path)


def test_cli_preserves_prior_attempts_and_requires_order(tmp_path):
    path = tmp_path / "trials.csv"
    assert trials.main(["init", str(path)]) == 0
    with pytest.raises(SystemExit):
        trials.main(["record", str(path), "2", "--outcome", "found", "--seconds", "18"])
    assert trials.main(["record", str(path), "1", "--outcome", "missed", "--seconds", "22"]) == 0
    original = path.read_bytes()
    with pytest.raises(SystemExit):
        trials.main(["record", str(path), "1", "--outcome", "found", "--seconds", "18"])
    assert path.read_bytes() == original

import importlib.util
import csv
import json
import os
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


def completed_plan():
    """Invented outcomes only, never a physical result."""
    rows = trials.plan()
    for row in rows:
        row.update(outcome="found" if row["present"] == "1" else "absent", seconds="18")
    return rows


def test_an_extra_csv_cell_cannot_publish_private_notes(tmp_path, capsys):
    path, output = tmp_path / "invented.csv", tmp_path / "report.json"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(trials.FIELDS)
        for i, row in enumerate(completed_plan()):
            writer.writerow([row[k] for k in trials.FIELDS] + (["invented private note"] if i == 0 else []))
    original = path.read_bytes()
    with pytest.raises(SystemExit) as error:
        trials.main(["score", str(path), "--out", str(output)])
    report = capsys.readouterr()
    assert error.value.code == 2 and not output.exists() and path.read_bytes() == original
    assert "invented private note" not in report.err and report.out == ""
    assert "extra fields or notes" in report.err


def test_a_short_csv_row_is_refused_instead_of_becoming_null_fields(tmp_path):
    path = tmp_path / "invented.csv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(trials.FIELDS)
        for i, row in enumerate(completed_plan()):
            writer.writerow([row[k] for k in trials.FIELDS][:-1] if i == 0 else [row[k] for k in trials.FIELDS])
    with pytest.raises(ValueError, match="exactly the planned columns"):
        trials.read(path)


@pytest.mark.parametrize("change", ["extra_key", "extra_cell", "missing_cell", "null_cell", "numeric_seconds",
    "bad_outcome", "changed_plan", "nan", "inf", "zero", "repeat_id", "short_plan"])
def test_direct_scoring_validates_the_same_plan_and_field_boundary(change):
    rows = completed_plan()
    if change == "extra_key": rows[0]["note"] = "invented private note"
    elif change == "extra_cell": rows[0][None] = ["invented private note"]
    elif change == "missing_cell": del rows[0]["seconds"]
    elif change == "null_cell": rows[0]["seconds"] = None
    elif change == "numeric_seconds": rows[0]["seconds"] = 18
    elif change == "bad_outcome": rows[0]["outcome"] = "invented private note"
    elif change == "changed_plan": rows[0]["object"] = "invented private note"
    elif change in ("nan", "inf"): rows[0]["seconds"] = change
    elif change == "zero": rows[0]["seconds"] = "0"
    elif change == "repeat_id": rows[1]["trial"] = rows[0]["trial"]
    elif change == "short_plan": rows.pop()
    with pytest.raises(ValueError) as error:
        trials.score(rows)
    assert "invented private note" not in str(error.value)


@pytest.mark.parametrize("root", [None, {}, "invented private note"])
def test_wrong_plan_container_is_a_fixed_error(root):
    with pytest.raises(ValueError, match="Keep all 30"):
        trials.score(root)


def test_scored_rows_do_not_share_mutable_dictionaries_with_input():
    rows = completed_plan()
    card = trials.score(rows)
    rows[0]["note"] = "invented private note"
    rows[0]["outcome"] = "error"
    assert "invented private note" not in json.dumps(card)
    assert card["trials"][0]["outcome"] == "found"


def test_failed_absent_trials_are_errors_not_correct_rejections():
    rows = completed_plan()
    for row in rows:
        if row["present"] == "0":
            row["outcome"] = "error"
    card = trials.score(rows)
    assert card["completed"] == 30 and card["errors"] == 10
    assert card["absent"]["false_find"] == 0 and card["absent"]["correct_absent"] == 0
    assert card["absent"]["errors"] == 10 and card["present"]["errors"] == 0
    assert card["absent"]["correct_absent_95_interval"] == trials.wilson(0, 10)


def test_failed_atomic_record_write_preserves_prior_attempts(tmp_path, monkeypatch):
    path = tmp_path / "invented.csv"
    trials.write(path, trials.plan())
    original = path.read_bytes()

    def fail(*args):
        raise OSError("invented write failure")

    monkeypatch.setattr(trials.os, "replace", fail)
    with pytest.raises(OSError):
        trials.write(path, completed_plan())
    assert path.read_bytes() == original and not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("symlink", [False, True])
def test_exclusive_save_preserves_existing_file_or_symlink(tmp_path, symlink):
    original = tmp_path / "original.json"
    original.write_text("invented earlier result")
    output = tmp_path / "report.json" if symlink else original
    if symlink:
        output.symlink_to(original)
    with pytest.raises(FileExistsError):
        trials.save(output, "invented new result", create=True)
    assert original.read_text() == "invented earlier result" and not list(tmp_path.glob("*.tmp"))
    assert not symlink or output.is_symlink()


def test_score_cli_preserves_input_and_earlier_outputs_and_labels_revision_scope(tmp_path, capsys):
    path, output = tmp_path / "invented.csv", tmp_path / "report.json"
    trials.write(path, completed_plan())
    original = path.read_bytes()
    assert trials.main(["score", str(path), "--out", str(output)]) == 0
    capsys.readouterr()
    card = json.loads(output.read_text())
    assert "Checkout when scored" in card["commit_scope"]
    assert output.stat().st_mode & 0o777 == path.stat().st_mode & 0o777 == 0o600
    saved = output.read_bytes()
    for destination in (path, output):
        with pytest.raises(SystemExit):
            trials.main(["score", str(path), "--out", str(destination)])
        assert path.read_bytes() == original and output.read_bytes() == saved
        assert not list(tmp_path.glob("*.tmp"))


def test_init_race_does_not_replace_a_concurrently_created_plan(tmp_path, monkeypatch):
    path = tmp_path / "invented.csv"
    link = os.link

    def create_competing_file(src, destination):
        path.write_text("invented existing plan")
        return link(src, destination)

    monkeypatch.setattr(trials.os, "link", create_competing_file)
    with pytest.raises(SystemExit):
        trials.main(["init", str(path)])
    assert path.read_text() == "invented existing plan" and not list(tmp_path.glob("*.tmp"))

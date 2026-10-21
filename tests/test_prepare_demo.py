"""The demo's setup script: what it adds, it removes; the letters name no real company."""

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_demo", ROOT / "scripts" / "prepare_demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_set_and_clean_add_and_remove_exactly_the_demos_two_items(tmp_path, monkeypatch):
    from andy_companion import moments, reminders
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    monkeypatch.setattr(moments, "FILE", tmp_path / "moments.json")
    monkeypatch.setattr(demo, "DEMO", tmp_path / "demo.json")
    kept = reminders.add("take the bins out", minutes=60)
    assert demo.set_up(4) == 0 and demo.set_up(4) == 1          # once only
    texts = [r["text"] for r in reminders.pending()]
    assert "call Rosa" in texts and any("piano" in m["what"] for m in moments._load())
    assert demo.clean() == 0
    assert [r["id"] for r in reminders.pending()] == [kept["id"]]   # the person's own reminder stays
    assert not any("piano" in m["what"] for m in moments._load())


def test_the_letters_are_made_up_and_say_so(tmp_path):
    demo.write_letters(tmp_path)
    for page in tmp_path.glob("*.html"):
        text = page.read_text()
        assert "Made up for a demonstration" in text
        for number in re.findall(r"\(\d{3}\) (\d{3})-\d{4}", text):
            assert number == "555"                                  # a number reserved for fiction

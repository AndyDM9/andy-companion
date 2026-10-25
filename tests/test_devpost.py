"""scripts/devpost.py: the Devpost form's fields from docs/submission.md, ready to paste (no network here)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("devpost_for_tests", ROOT / "scripts" / "devpost.py")
devpost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(devpost)


def test_the_form_fields_come_from_the_submission_text():
    f = devpost.fields((ROOT / "docs" / "submission.md").read_text())
    assert f["Project name"] == "Andy"
    assert 0 < len(f["Tagline"]) <= 200 and not f["Tagline"].startswith("(")
    tags = [t for t in f["Built with"].split(",") if t.strip()]
    assert 0 < len(tags) <= 25
    story = f["About the project"]
    assert story.startswith("## For the judges") and "\n### " not in story          # Devpost's own heading level
    for heading in ("Inspiration", "What it does", "How we built it", "Challenges we ran into",
                    "Accomplishments that we're proud of", "What we learned", "What's next for Andy"):
        assert f"## {heading}" in story, heading


def test_a_draft_points_its_evidence_at_a_ref_that_exists():
    text = "[x](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/a.json)"
    assert devpost.at_ref(text, "main") == "[x](https://github.com/AndyDM9/andy-companion/blob/main/evals/results/a.json)"
    assert devpost.links(devpost.at_ref(text, "main")) == ["https://github.com/AndyDM9/andy-companion/blob/main/evals/results/a.json"]

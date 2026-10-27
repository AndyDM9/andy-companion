"""scripts/devpost.py: the Devpost form's fields from docs/submission.md, ready to paste (no network here)."""

import importlib.util
from pathlib import Path
import re
import subprocess

import pytest

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
    testing = f["Testing instructions"]
    assert "no connected" in testing and "do not" in testing and "purchase credits" in testing
    assert "robot" in testing and "organisers" in testing
    story = f["About the project"]
    assert story.startswith("## For the judges") and "\n### " not in story          # Devpost's own heading level
    for heading in ("Inspiration", "What it does", "How we built it", "Challenges we ran into",
                    "Accomplishments that we're proud of", "What we learned", "What's next for Andy"):
        assert f"## {heading}" in story, heading


def test_a_draft_points_its_evidence_at_a_ref_that_exists():
    text = "[x](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/a.json)"
    assert devpost.at_ref(text, "main") == "[x](https://github.com/AndyDM9/andy-companion/blob/main/evals/results/a.json)"
    assert devpost.links(devpost.at_ref(text, "main")) == ["https://github.com/AndyDM9/andy-companion/blob/main/evals/results/a.json"]


@pytest.mark.parametrize("status,blocked", [(404, False), (403, True)])
def test_failed_citations_stay_failed_and_a_404_is_not_excused_as_blocking(monkeypatch, capsys, status, blocked):
    monkeypatch.setattr(devpost, "opens", lambda url: status if "ftc.gov" in url else 200)
    assert devpost.main(["--check"]) == 1
    report = capsys.readouterr().err
    ftc_url = next(u for u in devpost.links((ROOT / "docs/submission.md").read_text()) if "ftc.gov" in u)
    assert f"{status}  {ftc_url}" in report
    assert ("an FTC request was blocked" in report) == blocked


@pytest.fixture
def release_tree(tmp_path):
    root = tmp_path / "release"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "--allow-empty", "-qm", "test release"], check=True, capture_output=True)
    (root / "reachy_app").mkdir()
    (root / "reachy_app/pyproject.toml").write_text(
        '[project]\ndependencies = ["andy-companion[robot] @ git+https://github.com/AndyDM9/andy-companion@main"]\n')
    return root


def commit_release(root):
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "-qm", "final files"], check=True, capture_output=True)


def test_final_export_blocks_a_draft_before_printing_or_network(release_tree, monkeypatch, capsys):
    (release_tree / "docs").mkdir()
    source = (ROOT / "docs/submission.md").read_text()
    source = re.sub(r"^- \*\*Video:\*\*.*$", "- **Video:** *[the YouTube link]*", source, flags=re.M)
    (release_tree / "docs/submission.md").write_text(source)
    monkeypatch.setattr(devpost, "ROOT", release_tree)
    monkeypatch.setattr(devpost, "opens", lambda url: pytest.fail("An incomplete final export should stop before networking"))
    assert devpost.main(["--ref", "hackathon-submission", "--final"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "Video placeholder" in output.err and "Pin the app" in output.err


def test_final_export_also_checks_public_links_after_local_release_checks(release_tree, monkeypatch, capsys):
    (release_tree / "docs").mkdir()
    source = (ROOT / "docs/submission.md").read_text()
    source = re.sub(r"^- \*\*Video:\*\*.*$", "- **Video:** https://youtu.be/abcdefghijk", source, flags=re.M)
    (release_tree / "docs/submission.md").write_text(source)
    (release_tree / "docs/feedback.md").write_text("# Feedback\nInvented feedback.\n")
    app = release_tree / "reachy_app/pyproject.toml"
    app.write_text(app.read_text().replace("@main", "@hackathon-submission"))
    commit_release(release_tree)
    subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
    monkeypatch.setattr(devpost, "ROOT", release_tree)
    checked = []

    def opens(url):
        checked.append(url)
        return 404 if "/blob/hackathon-submission/" in url else 200

    monkeypatch.setattr(devpost, "opens", opens)
    assert devpost.main(["--ref", "hackathon-submission", "--final"]) == 1
    assert any("/blob/hackathon-submission/" in url for url in checked)
    assert "404" in capsys.readouterr().err


def test_real_release_tag_and_app_pin_are_required(release_tree):
    form = {"Video": "https://youtu.be/abcdefghijk", "Tagline": "An invented tagline", "Built with": "python"}
    problems = devpost.final_problems(form, "hackathon-submission", release_tree)
    assert any("missing locally" in p for p in problems) and any("Pin the app" in p for p in problems)
    (release_tree / "docs").mkdir()
    (release_tree / "docs/submission.md").write_text("Invented final submission.\n")
    (release_tree / "docs/feedback.md").write_text("Invented final feedback.\n")
    app = release_tree / "reachy_app/pyproject.toml"
    app.write_text(app.read_text().replace("@main", "@hackathon-submission"))
    commit_release(release_tree)
    subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
    assert devpost.final_problems(form, "hackathon-submission", release_tree) == []
    assert any("Use --ref" in p for p in devpost.final_problems(form, "main", release_tree))


@pytest.mark.parametrize("change", ["tracked", "staged", "new_commit", "untracked_input"])
def test_final_export_rejects_files_that_are_not_in_its_tag(release_tree, change):
    form = {"Video": "https://youtu.be/abcdefghijk", "Tagline": "Invented", "Built with": "python"}
    docs = release_tree / "docs"
    docs.mkdir()
    (docs / "submission.md").write_text("Invented final submission.\n")
    (docs / "feedback.md").write_text("Invented final feedback.\n")
    app = release_tree / "reachy_app/pyproject.toml"
    app.write_text(app.read_text().replace("@main", "@hackathon-submission"))
    runtime = release_tree / "runtime.py"
    runtime.write_text("# Invented version one\n")
    if change == "untracked_input":
        # Even otherwise clean exports must not accept required files absent from the snapshot.
        subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
    else:
        commit_release(release_tree)
        subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
        assert devpost.final_problems(form, "hackathon-submission", release_tree) == []
        runtime.write_text("# Invented version two\n")
        if change == "staged":
            subprocess.run(["git", "-C", str(release_tree), "add", "runtime.py"], check=True, capture_output=True)
        elif change == "new_commit":
            commit_release(release_tree)
    assert any("working files differ" in p for p in devpost.final_problems(form, "hackathon-submission", release_tree))


@pytest.mark.parametrize("url", ["*[the YouTube link]*", "https://youtube.com/", "https://youtube.com/watch?v=TODO",
                                 "https://youtube.com/playlist?list=abcdefghijk", "https://youtube.com.evil.example/watch?v=abcdefghijk",
                                 "http://youtu.be/abcdefghijk", "https://[broken"])
def test_placeholders_and_nonvideo_links_are_not_final_video_urls(url):
    assert not devpost.youtube_video(url)


@pytest.mark.parametrize("url", ["https://youtu.be/abcdefghijk", "https://www.youtube.com/watch?v=abcdefghijk&t=1s",
                                 "[Video](https://www.youtube.com/watch?v=abcdefghijk)"])
def test_real_video_url_shapes_are_accepted_without_claiming_they_are_public(url):
    assert devpost.youtube_video(url)

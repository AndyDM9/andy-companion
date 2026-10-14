"""The Reachy Mini app (reachy_app/) stays publishable: what Pollen's checker
(`reachy-mini-app-assistant check reachy_app`, passed 2026-10-13) looks for, and its page's words."""

import re
import tomllib
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "reachy_app"


def test_the_app_has_what_pollen_s_checker_requires():
    project = tomllib.loads((APP / "pyproject.toml").read_text())["project"]
    assert project["name"] == "andy_companion_app"
    assert project["entry-points"]["reachy_mini_apps"] == {"andy_companion_app": "andy_companion_app.main:AndyCompanionApp"}
    # The checker reads the source: the class must inherit ReachyMiniApp by that name.
    assert "class AndyCompanionApp(ReachyMiniApp)" in (APP / "andy_companion_app" / "main.py").read_text()
    readme = (APP / "README.md").read_text()
    assert readme.startswith("---") and "reachy_mini_python_app" in readme
    for name in ("index.html", "style.css", "andy_companion_app/__init__.py"):
        assert (APP / name).exists(), name


def test_the_app_page_is_ours_not_the_template():
    page = (APP / "index.html").read_text()
    assert "Enter your tagline" not in page and "🛠️" not in page
    for src in re.findall(r'src="([^"]+)"', page):
        assert (APP / src).exists(), src
    assert 'alt="' in page and '<html lang="en">' in page


def test_the_app_s_words_follow_the_project_s_rules():
    text = " ".join((APP / name).read_text() for name in ("index.html", "README.md")).lower()
    for word in ("senior", "elderly", "peace of mind", "check on", "lonel", "keeps you safe", "monitor"):
        assert word not in text, word
    assert "older adults who live at home, and the family who help" in " ".join(text.split())

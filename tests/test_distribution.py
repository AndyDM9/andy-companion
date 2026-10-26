"""Also run with python -I against an installed wheel, without checkout imports or robot dependencies."""

import json
from importlib import resources
from pathlib import Path
import unittest

from andy_companion import app_mode


class DistributionTests(unittest.TestCase):
    def test_pages_and_fonts_are_packaged(self):
        package = resources.files("andy_companion")
        for page in ("screen", "hood", "family", "setup", "expired"):
            self.assertIn(b"<html", package.joinpath(f"pages/{page}.html").read_bytes().lower())
        for weight in (400, 700):
            self.assertEqual(package.joinpath(f"pages/fonts/atkinson-hyperlegible-{weight}.woff2").read_bytes()[:4], b"wOF2")
        self.assertTrue(package.joinpath("pages/fonts/OFL.txt").is_file())

    def test_recorded_prompts_and_stories_are_packaged(self):
        package = resources.files("andy_companion")
        for prompt in ("call_911_en", "call_911_es", "crisis_en", "crisis_es"):
            self.assertEqual(package.joinpath(f"urgent_audio/{prompt}.wav").read_bytes()[:4], b"RIFF")
        self.assertTrue(json.loads(package.joinpath("story_texts.json").read_text()))

    def test_profile_and_voice_tools_are_packaged(self):
        self.assertIn("robot", app_mode.data_dir("profiles").joinpath("companion/profile.md").read_text())
        for tool in ("remember", "share_with_family", "find_object", "read_letter", "look_into"):
            self.assertTrue(app_mode.data_dir("tools").joinpath(f"{tool}.py").is_file(), tool)


if __name__ == "__main__":
    # -I removes the source checkout from sys.path; refuse to mistake editable imports for wheel proof.
    checkout_source = Path(__file__).resolve().parents[1] / "src"
    if Path(app_mode.__file__).resolve().is_relative_to(checkout_source):
        raise SystemExit("Install the wheel in an isolated environment and run this file with python -I.")
    unittest.main()

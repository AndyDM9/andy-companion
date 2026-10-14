"""The suite gives the model exactly the tools the robot does (evals/tools.json).

If one of these fails, run `robot/.venv/bin/python evals/build_tools.py` and commit the result.
"""

import ast
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPECS = json.loads((ROOT / "evals" / "tools.json").read_text())


def profile_tools():
    block = re.search(r"default_tools\s*=\s*\[(.*?)\]", (ROOT / "profiles/companion/profile.md").read_text(), re.S)
    return re.findall(r'"([a-z_]+)"', block.group(1))


def class_attrs(path: Path, name: str) -> dict:
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ClassDef):
            attrs = {t.id: n.value for n in node.body if isinstance(n, ast.Assign)
                     for t in n.targets if isinstance(t, ast.Name)}
            if "name" in attrs and ast.literal_eval(attrs["name"]) == name:
                return {k: ast.literal_eval(v) for k, v in attrs.items() if k in ("description", "parameters_schema")}
    raise LookupError(name)


def test_the_suite_offers_every_tool_in_the_profile_in_order():
    assert [t["name"] for t in SPECS] == profile_tools()


@pytest.mark.parametrize("spec", [s for s in SPECS if s["source"] == "andy"], ids=lambda s: s["name"])
def test_each_of_andys_tools_reads_as_the_robot_sends_it(spec):
    real = class_attrs(ROOT / "tools" / f"{spec['name']}.py", spec["name"])
    assert spec["description"] == real["description"]
    assert spec["parameters"] == real["parameters_schema"]


def job_files():
    text = (ROOT / "cloud" / "suite-job.sh").read_text()
    return re.search(r"FILES=\(([^)]*)\)", text).group(1).split()


def test_the_job_carries_the_tools_file():
    assert "evals/tools.json" in job_files()


def test_the_job_carries_every_module_the_suite_imports_and_they_need_only_the_standard_library():
    """A missing module would not fail the job: the suite would quietly run without the net."""
    import sys

    runner = (ROOT / "evals" / "run_suite.py").read_text()
    files = job_files()
    names = re.search(r"from andy_companion import ([\w, ]+)", runner).group(1).replace(" ", "").split(",")
    assert {"urgent", "offers", "recall"} <= set(names)
    for path in ("evals/run_suite.py", "evals/suite.json", "profiles/companion/profile.md"):
        assert path in files
    for name in ["__init__", *names]:
        path = f"src/andy_companion/{name}.py"
        assert path in files, f"{path} is not sent with the job"
        for node in ast.parse((ROOT / path).read_text()).body:     # top level; robot-only imports sit in functions
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else (
                [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for mod in mods:
                top = mod.split(".")[0]
                assert top in sys.stdlib_module_names or top == "__future__", f"{path} imports {mod}"


def test_the_scorecard_line_for_the_job_log_stays_short(monkeypatch, capsys):
    """A Nebius job's log split the full scorecard line, so the job could not save it (2026-10-13)."""
    import sys

    sys.path.insert(0, str(ROOT / "evals"))
    import run_suite

    case = json.loads((ROOT / "evals" / "suite.json").read_text())["cases"][0]
    fake = {"id": case["id"], "area": case["area"], "pass": False, "why": "w" * 900, "reply": "r" * 900,
            "tools": [], "seconds": 1.0, "net": False}
    monkeypatch.setattr(run_suite, "run_case", lambda c, system: {**fake, "id": c["id"], "area": c["area"]})
    run_suite.main(["--runs", "3"])
    line = [x for x in capsys.readouterr().out.splitlines() if x.startswith("SCORECARD_JSON ")][0]
    assert len(line) < 16000 and json.loads(line[len("SCORECARD_JSON "):])["per_run"] == [0, 0, 0]

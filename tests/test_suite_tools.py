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


def test_the_job_carries_the_tools_file():
    assert "evals/tools.json:/andy/evals/tools.json" in (ROOT / "cloud" / "safety-job.sh").read_text()

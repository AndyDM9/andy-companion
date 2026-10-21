"""Write evals/tools.json: the tools the robot gives the model, exactly, for the suite.

    robot/.venv/bin/python evals/build_tools.py

Reads the profile's default_tools, imports each tool (Andy's from tools/, Pollen's from its
conversation app) and keeps its name, description and parameters, in the profile's order. Run it
whenever a tool or the profile changes; tests/test_suite_tools.py fails until it is run.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PROFILE = ROOT / "profiles" / "companion" / "profile.md"
OUT = ROOT / "evals" / "tools.json"


def profile_tools(text: str) -> list:
    block = re.search(r"default_tools\s*=\s*\[(.*?)\]", text, re.S)
    return re.findall(r'"([a-z_]+)"', block.group(1)) if block else []


def load(name: str):
    from reachy_mini_conversation_app.tools.core_tools import Tool

    ours = ROOT / "tools" / f"{name}.py"
    if ours.exists():
        spec = importlib.util.spec_from_file_location(f"andy_tool_{name}", ours)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(f"reachy_mini_conversation_app.tools.{name}")
    for value in vars(module).values():
        if isinstance(value, type) and issubclass(value, Tool) and getattr(value, "name", None) == name:
            return value
    raise LookupError(f"no tool class named {name}")


def main() -> int:
    if {"-h", "--help"} & set(sys.argv[1:]):     # the description, and nothing else run
        print(__doc__)
        return 0
    specs = []
    for name in profile_tools(PROFILE.read_text()):
        tool = load(name)
        specs.append({"name": name, "description": str(tool.description),
                      "parameters": tool.parameters_schema, "source": "andy" if (ROOT / "tools" / f"{name}.py").exists() else "pollen"})
    OUT.write_text(json.dumps(specs, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(specs)} tools written to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

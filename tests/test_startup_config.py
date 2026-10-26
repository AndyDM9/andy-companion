"""Load Pollen's actual startup configuration in a fresh process, without connecting to hardware."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(importlib.util.find_spec("reachy_mini_conversation_app") is None, reason="needs installed robot SDK")
def test_actual_startup_config_accepts_and_loads_andys_memory_tool(tmp_path):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(ROOT / "src"),
           "ANDY_DATA_DIR": str(tmp_path / "data"), "ANDY_ENV_FILE": str(tmp_path / "missing.env"),
           "XDG_CACHE_HOME": str(tmp_path / "cache"), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    code = """
import json
from andy_companion import app_mode
app_mode.configure_env()
from reachy_mini_conversation_app.config import config
from reachy_mini_conversation_app.tools.core_tools import get_tools
from pathlib import Path
registry = get_tools()
specs = json.loads((Path(app_mode.__file__).resolve().parents[2] / 'evals/tools.json').read_text())
assert set(registry) == {entry['name'] for entry in specs} | {'task_cancel', 'task_status'}
tool = registry['remember_fact']
assert '._external_tools.' in type(tool).__module__
print('STARTUP_OK ' + json.dumps({'memory_tool': tool.name}))
"""
    result = subprocess.run([sys.executable, "-c", code], env=env, cwd=tmp_path,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, "Pollen startup configuration or external tool loading failed."
    line = next(line for line in result.stdout.splitlines() if line.startswith("STARTUP_OK "))
    assert json.loads(line.removeprefix("STARTUP_OK ")) == {"memory_tool": "remember_fact"}


@pytest.mark.skipif(importlib.util.find_spec("reachy_mini_conversation_app") is None, reason="needs installed robot SDK")
def test_dashboard_import_defers_pollen_configuration_until_andy_is_configured(tmp_path):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT / "reachy_app"))),
           "ANDY_DATA_DIR": str(tmp_path / "data"), "XDG_CACHE_HOME": str(tmp_path / "cache")}
    code = """
import sys
from andy_companion_app.main import AndyCompanionApp
assert 'reachy_mini_conversation_app.config' not in sys.modules
from andy_companion import app_mode
app_mode.configure_env()
from reachy_mini_conversation_app.tools.core_tools import get_tools
assert 'remember_fact' in get_tools()
print('DASHBOARD_STARTUP_OK')
"""
    result = subprocess.run([sys.executable, "-c", code], env=env, cwd=tmp_path,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, "Dashboard imports configured Pollen before Andy's profile, or failed to load its tools."
    assert "DASHBOARD_STARTUP_OK" in result.stdout

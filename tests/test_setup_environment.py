"""Reproduce fresh-setup failures without credentials, a robot, services or external API calls."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from andy_companion import app_mode

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(f"setup_audit_{name}", ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_env_reader_strips_paired_quotes_without_executing_shell_text(tmp_path):
    marker = tmp_path / "must-not-exist"
    env = tmp_path / "settings.env"
    env.write_text(f'NEBIUS_API_KEY="invented key"\nANDY_SCREEN_PORT=\'8094\'\n'
                   f'UNKNOWN=$(touch {marker})\nANDY_VISION_MODEL="$(touch {marker})"\n')
    result = app_mode.read_env(app_mode.APP_KEYS, env)
    assert result["NEBIUS_API_KEY"] == "invented key" and result["ANDY_SCREEN_PORT"] == "8094"
    assert result["ANDY_VISION_MODEL"] == f"$(touch {marker})"
    assert "UNKNOWN" not in result and not marker.exists()


@pytest.mark.parametrize("shell_key", [None, "invented-shell-key"])
def test_desktop_launcher_preserves_the_app_readers_settings(tmp_path, shell_key):
    env_file = tmp_path / "settings.env"
    env_file.write_text('NEBIUS_API_KEY="invented-file-key"\nTAVILY_API_KEY=\'invented-web-key\'\n'
                        'ANDY_SCREEN_PORT="8094"\nANDY_VISION_MODEL="invented-model"\n'
                        'ANDY_FINDER_TURN=off\nANDY_VOICE_URL="ws://127.0.0.1:9876/v1/realtime"\n'
                        'UNRELATED_PRIVATE_SETTING=must-not-load\n')
    # Stand in for the interpreter at the real launch boundary. No upstream app or hardware is loaded.
    interpreter = tmp_path / "inspect-launch"
    interpreter.write_text(f"#!{sys.executable}\n"
                           "import json,os,sys\nfrom andy_companion import app_mode\n"
                           "app_mode.load_env(app_mode.APP_KEYS)\napp_mode.configure_env()\n"
                           "print(json.dumps({k:os.environ.get(k) for k in "
                           "(*app_mode.APP_KEYS,'HF_REALTIME_WS_URL','UNRELATED_PRIVATE_SETTING')}))\n")
    interpreter.chmod(0o700)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "ANDY_APP_PYTHON": str(interpreter),
           "ANDY_ENV_FILE": str(env_file)}
    if shell_key:
        env["NEBIUS_API_KEY"] = shell_key
    result = subprocess.run([str(ROOT / "scripts/run-robot.sh")], env=env, cwd=tmp_path,
                            capture_output=True, text=True, timeout=10, check=True)
    loaded = json.loads(result.stdout)
    assert loaded["NEBIUS_API_KEY"] == (shell_key or "invented-file-key")
    assert loaded["TAVILY_API_KEY"] == "invented-web-key"
    assert loaded["ANDY_SCREEN_PORT"] == "8094" and loaded["ANDY_VISION_MODEL"] == "invented-model"
    assert loaded["ANDY_FINDER_TURN"] == "off"
    assert loaded["HF_REALTIME_WS_URL"] == "ws://127.0.0.1:9876/v1/realtime"
    assert loaded["UNRELATED_PRIVATE_SETTING"] is None
    assert result.stderr == ""
    assert "NEBIUS_API_KEY" not in " ".join(result.args)


def test_doctor_uses_the_same_quoted_settings_and_shell_precedence(tmp_path, monkeypatch):
    doctor = script("doctor")
    env_file = tmp_path / "settings.env"
    env_file.write_text('NEBIUS_API_KEY="invented-file-key"\nANDY_SCREEN_PORT=\'8094\'\n')
    monkeypatch.setattr(doctor, "ENV_FILE", env_file)
    monkeypatch.setenv("NEBIUS_API_KEY", "invented-shell-key")
    monkeypatch.delenv("ANDY_SCREEN_PORT", raising=False)
    loaded = doctor.env()
    assert loaded["NEBIUS_API_KEY"] == "invented-shell-key" and loaded["ANDY_SCREEN_PORT"] == "8094"


def test_doctor_checks_the_configured_screen_port(monkeypatch, capsys):
    doctor = script("doctor")
    monkeypatch.setattr(doctor, "env", lambda: {"ANDY_SCREEN_PORT": "8094", "ANDY_VISION": "off"})
    ports = []
    monkeypatch.setattr(doctor, "port_open", lambda port: ports.append(port) or False)
    monkeypatch.setattr(doctor, "http", lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))
    monkeypatch.setattr(sys, "argv", ["doctor.py"])
    assert doctor.main() == 1
    assert 8094 in ports and 8090 not in ports


def test_settings_links_use_the_same_port_as_the_services(tmp_path, monkeypatch, capsys):
    settings = script("settings")
    env_file = tmp_path / "settings.env"
    env_file.write_text('ANDY_SCREEN_PORT="8094"\n')
    monkeypatch.setenv("ANDY_ENV_FILE", str(env_file))
    monkeypatch.setenv("ANDY_SCREEN_PORT", "")
    monkeypatch.delenv("ANDY_SCREEN_PORT")
    assert settings.main(["links"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 4 and all(":8094/" in line for line in lines)
    assert "ANDY_SCREEN_PORT" in app_mode.SUPERVISOR_KEYS

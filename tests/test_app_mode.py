import os

from andy_companion import app_mode


def test_tools_and_profile_are_found_in_development():
    assert (app_mode.data_dir("tools") / "get_today.py").is_file()
    assert (app_mode.data_dir("profiles") / "companion" / "profile.md").is_file()


def test_environment_defaults_point_at_andy(monkeypatch):
    for k in ("REACHY_MINI_CUSTOM_PROFILE", "REACHY_MINI_EXTERNAL_TOOLS_DIRECTORY", "HF_REALTIME_WS_URL",
              "HF_REALTIME_CONNECTION_MODE", "REACHY_MINI_EXTERNAL_PROFILES_DIRECTORY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("ANDY_VOICE_URL", "ws://voice.local:8765/v1/realtime")
    app_mode.configure_env()
    assert os.environ["REACHY_MINI_CUSTOM_PROFILE"] == "companion"
    assert os.environ["HF_REALTIME_CONNECTION_MODE"] == "local"
    assert os.environ["HF_REALTIME_WS_URL"] == "ws://voice.local:8765/v1/realtime"
    assert os.environ["REACHY_MINI_EXTERNAL_TOOLS_DIRECTORY"].endswith("tools")


def test_install_reads_the_env_file_first_without_replacing_anything():
    """The dashboard app has no run-robot.sh to pass the keys on: install reads them itself (2026-10-14)."""
    from pathlib import Path

    source = Path(app_mode.__file__).read_text()
    install = source[source.index("def install("):]
    assert install.index("load_env(APP_KEYS)") < install.index("configure_env()")


def test_load_env_takes_only_the_named_keys(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("TAVILY_API_KEY=a\nTAVILY_API_KEY='b'\nSOMETHING_ELSE=x\nnot a line\n")
    for name in ("TAVILY_API_KEY", "SOMETHING_ELSE"):
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)
    assert app_mode.load_env(("TAVILY_API_KEY",), env) == ["TAVILY_API_KEY"]
    assert os.environ["TAVILY_API_KEY"] == "b" and "SOMETHING_ELSE" not in os.environ   # the last line wins

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

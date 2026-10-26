import io
import json

import pytest

from andy_companion import settings, weather


class Opener:
    """Answers each URL from a table; records what was asked."""

    def __init__(self, table):
        self.table, self.urls = table, []

    def __call__(self, req, timeout=None):
        self.urls.append(req.full_url)
        assert "andy-companion" in req.headers["User-agent"]       # the NWS asks every client to say who it is
        for start, body in self.table.items():
            if req.full_url.startswith(start):
                if isinstance(body, Exception):
                    raise body
                return io.BytesIO(json.dumps(body).encode())
        raise AssertionError(req.full_url)


GEO = {"results": [{"name": "Harbor Bay", "admin1": "Florida", "latitude": 25.95065, "longitude": -80.12282},
                   {"name": "Harbor Bay", "admin1": "Georgia", "latitude": 1.0, "longitude": 2.0}]}
POINT = {"properties": {"forecast": "https://api.weather.gov/gridpoints/MFL/112,58/forecast"}}
FORECAST = {"properties": {"periods": [
    {"name": "Tonight", "detailedForecast": "Mostly clear, with a low around 80."},
    {"name": "Wednesday", "detailedForecast": "A slight chance of showers after 4pm. Sunny, with a high near 86."},
    {"name": "Wednesday Night", "detailedForecast": "Mostly clear."},
    {"name": "Thursday", "detailedForecast": "Sunny."}]}}
ALERTS = {"features": [{"properties": {"event": "Heat Advisory", "headline": "Heat Advisory until 7 PM EDT"}}]}


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")


def full():
    return Opener({weather.GEOCODE: GEO, "https://api.weather.gov/points/": POINT,
                   "https://api.weather.gov/gridpoints/": FORECAST, "https://api.weather.gov/alerts/": ALERTS})


def test_the_town_is_found_in_its_state():
    out = weather.locate("Harbor Bay, Florida", opener=full())
    assert out["place"] == "Harbor Bay, Florida"
    assert out["lat"] == pytest.approx(25.9507, abs=1e-3) and out["lon"] == pytest.approx(-80.1228, abs=1e-3)


def test_the_coordinates_are_looked_up_once_per_town():
    settings.update(place="Harbor Bay, Florida")
    op = full()
    weather.where(op)
    weather.where(op)
    assert sum(u.startswith(weather.GEOCODE) for u in op.urls) == 1
    settings.update(place="Miami, Florida")
    weather.where(op)
    assert sum(u.startswith(weather.GEOCODE) for u in op.urls) == 2


def test_the_forecast_names_its_periods_and_the_alert_comes_with_it():
    out = weather.forecast(25.9507, -80.1228, opener=full())
    assert [p["name"] for p in out["periods"]] == ["Tonight", "Wednesday", "Wednesday Night"]
    assert out["alerts"] == ["Heat Advisory until 7 PM EDT"] and out["source"] == "the National Weather Service"


def test_no_alerts_service_still_gives_the_forecast():
    op = full()
    op.table["https://api.weather.gov/alerts/"] = OSError("down")
    assert weather.forecast(1, 2, opener=op)["alerts"] == []


def test_a_forecast_address_outside_the_weather_service_is_refused():
    op = full()
    op.table["https://api.weather.gov/points/"] = {"properties": {"forecast": "https://example.com/forecast"}}
    with pytest.raises(weather.WeatherError):
        weather.forecast(1, 2, opener=op)


def test_no_town_is_said_plainly():
    with pytest.raises(weather.WeatherError, match="setup page"):
        weather.where(full())


def test_the_screen_gets_temperature_and_a_short_forecast():
    op = full()
    op.table["https://api.weather.gov/gridpoints/"] = {"properties": {"periods": [
        {"name": "Tonight", "detailedForecast": "Mostly clear.", "shortForecast": "Mostly Clear", "temperature": 81,
         "probabilityOfPrecipitation": {"value": 10}}]}}
    p = weather.forecast(1, 2, opener=op)["periods"][0]
    assert p["temperature"] == "81°" and p["short"] == "Mostly Clear" and p["rain"] == 10


def test_the_weather_tile_refreshes_in_the_background_and_only_with_a_town(monkeypatch):
    import time

    from andy_companion import screen_server

    screen_server._weather.update(card=None, at=0.0, busy=False)
    assert screen_server.weather_card() is None                       # no town set yet
    settings.update(place="Harbor Bay, Florida")
    monkeypatch.setattr(weather, "where", lambda opener=None: {"lat": 1, "lon": 2})
    monkeypatch.setattr(weather, "forecast", lambda lat, lon, periods=3, opener=None: {
        "periods": [{"name": "Tonight", "temperature": "81°", "short": "Mostly Clear", "rain": 10}], "alerts": []})
    screen_server.weather_card()                                      # starts the refresh; never waits for it
    for _ in range(50):
        if screen_server._weather["card"]:
            break
        time.sleep(0.01)
    assert screen_server.weather_card()["periods"][0]["temperature"] == "81°"


def test_the_tv_card_is_titled_with_the_town_and_carries_the_temperatures(tmp_path, monkeypatch):
    """2026-10-25: the card read "Weather / Weather", and the forecast beside it had no temperature."""
    import asyncio
    import importlib.util
    import sys
    import types
    from pathlib import Path

    from andy_companion import board, weather as w

    core = types.ModuleType("reachy_mini_conversation_app.tools.core_tools")
    core.Tool, core.ToolDependencies = type("Tool", (), {}), object
    for name in ("reachy_mini_conversation_app", "reachy_mini_conversation_app.tools"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(sys.modules, core.__name__, core)
    spec = importlib.util.spec_from_file_location("andy_tool_weather", Path(__file__).resolve().parents[1] / "tools" / "weather.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    monkeypatch.setattr(board, "SCREEN", tmp_path / "screen.json")
    monkeypatch.setattr(w, "where", lambda: {"place": "Miami, Florida", "lat": 25.77, "lon": -80.19})
    monkeypatch.setattr(w, "forecast", lambda lat, lon: {
        "periods": [{"name": "Tonight", "forecast": "Showers.", "short": "Showers", "temperature": "78°", "rain": 60},
                    {"name": "Monday", "forecast": "Storms likely.", "short": "Storms", "temperature": "", "rain": None}],
        "alerts": ["Rip Current Statement"], "source": "the National Weather Service"})
    asyncio.run(tool.Weather()(None))
    card = board.showing()
    assert card["kind"] == "weather" and card["title"] == "Miami, Florida"
    assert card["items"][0] == {"summary": "Rip Current Statement", "tone": "notice", "source": "weather.gov"}
    assert [(i["title"], i["summary"]) for i in card["items"][1:]] == [("Tonight · 78°", "Showers, 60% rain"),
                                                                       ("Monday", "Storms")]


def test_an_alert_on_the_screen_keeps_what_and_until_when():
    from andy_companion.weather import short_alert
    assert short_alert("Rip Current Statement issued October 25 at 7:43AM EDT until October 28 at 2:00AM EDT by NWS Miami FL") \
        == "Rip Current Statement until October 28 at 2:00AM EDT"
    assert short_alert("Flood Watch issued October 25 at 3:10PM EDT by NWS Miami FL") == "Flood Watch"
    assert short_alert("Heat Advisory") == "Heat Advisory"

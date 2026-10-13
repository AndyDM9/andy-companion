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

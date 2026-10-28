"""The weather for the person's town, from the US National Weather Service (decision 0004).

The town set on the setup page is turned into coordinates once (Open-Meteo geocoding) and kept in
settings with the town. The forecast's next periods ("Tonight", "Wednesday") and any active alerts
come from api.weather.gov. No key; only the town and its coordinates leave this computer.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional

USER_AGENT = "andy-companion (a home companion robot; github.com/AndyDM9/andy-companion)"
GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
NWS = "https://api.weather.gov"
TIMEOUT_S = 8


class WeatherError(Exception):
    """Something to say plainly: the weather could not be found."""


def _get(url: str, opener: Optional[Callable] = None) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json, application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
            return json.loads(r.read())
    except Exception as e:
        raise WeatherError(f"The weather service did not answer ({type(e).__name__}).") from None


def locate(place: str, opener: Optional[Callable] = None) -> Dict[str, Any]:
    """'Harbor Bay, Florida' -> {"place", "lat", "lon"}, in the United States."""
    name, _, region = (p.strip() for p in str(place).partition(","))
    if not name:
        raise WeatherError("Andy's town is not set yet; it can be set on the setup page.")
    data = _get(f"{GEOCODE}?{urllib.parse.urlencode({'name': name, 'count': 10, 'countryCode': 'US'})}", opener)
    results = data.get("results") or []
    if region:
        results = [r for r in results if region.lower() in str(r.get("admin1", "")).lower()] or results
    if not results:
        raise WeatherError(f"Could not find {place} for the weather.")
    best = results[0]
    return {"place": place, "lat": round(float(best["latitude"]), 4), "lon": round(float(best["longitude"]), 4)}


def where(opener: Optional[Callable] = None) -> Dict[str, Any]:
    """The town's coordinates, looked up once per town and kept in settings."""
    from andy_companion import settings

    s = settings.get()
    place = s.get("place")
    kept = s.get("coords") or {}
    if place and kept.get("place") == place:
        return kept
    found = locate(place or "", opener)
    settings.update(coords=found)
    return found


def short_alert(headline: str) -> str:
    """For a screen: 'Rip Current Statement issued October 25 at 7:43AM EDT until October 28 at 2:00AM EDT by NWS
    Miami FL' -> 'Rip Current Statement until October 28 at 2:00 am', the time as the screen's clock writes it
    (2026-10-28, on the robot's TV: "8:00PM EDT" beside "11:16 am"). Andy is given the whole headline."""
    out = re.sub(r"\s+issued\s+.*?(?=\s+until\s+|\s+by\s+|$)", "", headline, count=1)
    out = re.sub(r"\s+by\s+NWS\b.*$", "", out).strip() or headline
    return re.sub(r"\b(\d{1,2}(?::\d\d)?)\s*([AP])M(?:\s+[A-Z]{1,2}[DS]T)?\b",
                  lambda m: f"{m.group(1)} {m.group(2).lower()}m", out)


def sentence_case(forecast: str) -> str:
    """The Weather Service's short forecasts come in Title Case ("Chance Showers And Thunderstorms"); the screen
    writes them as a sentence ("Chance showers and thunderstorms"), like every other line on it."""
    words = forecast.split()
    return " ".join([words[0]] + [w if w.isupper() and len(w) > 1 else w.lower() for w in words[1:]]) if words else ""


def forecast(lat: float, lon: float, periods: int = 3, opener: Optional[Callable] = None) -> Dict[str, Any]:
    point = _get(f"{NWS}/points/{lat},{lon}", opener).get("properties") or {}
    url = point.get("forecast")
    if not url or not str(url).startswith(NWS):
        raise WeatherError("The National Weather Service has no forecast for this place.")
    raw = (_get(url, opener).get("properties") or {}).get("periods") or []
    items = [{"name": str(p.get("name", ""))[:40], "forecast": " ".join(str(p.get("detailedForecast", "")).split())[:300],
              "short": sentence_case(str(p.get("shortForecast", "")))[:80],
              "temperature": (f"{p['temperature']}°" if isinstance(p.get("temperature"), (int, float)) else ""),
              "rain": (p.get("probabilityOfPrecipitation") or {}).get("value")}
             for p in raw[:periods]]
    alerts: List[str] = []
    try:
        feats = _get(f"{NWS}/alerts/active?point={lat},{lon}", opener).get("features") or []
        alerts = [str((f.get("properties") or {}).get("headline") or (f.get("properties") or {}).get("event", ""))[:200]
                  for f in feats[:3]]
    except WeatherError:
        pass     # the forecast still stands without alerts
    return {"periods": items, "alerts": [a for a in alerts if a], "source": "the National Weather Service"}

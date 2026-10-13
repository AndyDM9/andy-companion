"""The web, through Tavily only (decision 0002): local news, a quick look-up, what's on, reading a
link, and checking a message against known scams.

REST calls with no extra packages. Every result goes to the model as information only, cleaned of
anything that looks like instructions, with each source's name so Andy can say where it came from.
Nothing here logs a query, a result or a message.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

API = "https://api.tavily.com"
TIMEOUT_S = 12
SNIPPET = 320
SCAM_SOURCES = ["consumer.ftc.gov", "ftc.gov", "identitytheft.gov", "aarp.org", "bbb.org", "ic3.gov", "fbi.gov",
                "usa.gov"]
INJECTION = re.compile(r"(?i)(ignore (all |any |the )?(previous|prior|above) instructions|system prompt|you are now|"
                       r"disregard (your|the) rules)")


class WebError(Exception):
    pass


def _key() -> str:
    key = os.environ.get("TAVILY_API_KEY", "")
    if not key:
        raise WebError("The web is not set up (no Tavily key).")
    return key


def _post(path: str, body: Dict[str, Any], opener: Optional[Callable] = None) -> Dict[str, Any]:
    req = urllib.request.Request(API + path, method="POST", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
            return json.loads(r.read())
    except WebError:
        raise
    except Exception as e:   # never echo the request: it holds what the person said
        raise WebError(f"The web did not answer ({type(e).__name__}).") from None


def clean(text: Any, limit: int = SNIPPET) -> str:
    """Web text as plain information: one line, no instruction-like phrases, cut to `limit`."""
    value = " ".join(str(text or "").split())
    value = INJECTION.sub("[removed]", value).replace("[", "(").replace("]", ")").replace("(removed)", "[removed]")
    return value[:limit].rstrip() + ("…" if len(value) > limit else "")


def source_name(url: str) -> str:
    host = urlparse(url or "").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _results(data: Dict[str, Any], limit: int = SNIPPET) -> List[Dict[str, str]]:
    out = []
    for r in data.get("results", []):
        item = {"title": clean(r.get("title"), 140), "source": source_name(r.get("url", "")),
                "summary": clean(r.get("content"), limit), "url": r.get("url", "")}
        if r.get("published_date"):
            item["published"] = str(r["published_date"])[:16]
        out.append(item)
    return out


def local_news(place: str, topic: str = "", sources: Optional[List[str]] = None, opener=None) -> List[Dict[str, str]]:
    body = {"query": f"{place} local news {topic}".strip()[:390], "topic": "news", "time_range": "day",
            "search_depth": "basic", "max_results": 3, "safe_search": True}
    if sources:
        body["include_domains"] = sources
    found = _results(_post("/search", body, opener))
    if not found and sources:          # the chosen papers had nothing today: widen once
        body.pop("include_domains")
        body["time_range"] = "week"
        found = _results(_post("/search", body, opener))
    return found


def look_up(question: str, place: str = "", opener=None) -> List[Dict[str, str]]:
    body = {"query": f"{question} {place}".strip()[:390], "search_depth": "basic", "max_results": 3, "safe_search": True}
    return _results(_post("/search", body, opener))


def whats_on(place: str, interest: str = "", pages: Optional[List[str]] = None, opener=None) -> List[Dict[str, str]]:
    if pages:
        found: List[Dict[str, str]] = []
        for page in pages[:2]:
            data = _post("/crawl", {"url": page, "instructions": f"Events and activities this week {interest}".strip(),
                                    "max_depth": 1, "limit": 8, "chunks_per_source": 2, "timeout": 30}, opener)
            for r in data.get("results", [])[:3]:
                found.append({"title": clean(r.get("url"), 140), "source": source_name(r.get("url", "")),
                              "summary": clean(r.get("raw_content"), SNIPPET), "url": r.get("url", "")})
        if found:
            return found
    from datetime import date, timedelta

    start = date.today()
    end = start + timedelta(days=6)
    week = f"{start.strftime('%B')} {start.day} to {end.strftime('%B')} {end.day} {end.year}"
    body = {"query": f"events {week} in {place} {interest}".strip()[:390], "time_range": "week",
            "search_depth": "basic", "max_results": 4, "safe_search": True}
    return _results(_post("/search", body, opener))


def read_link(url: str, opener=None) -> Dict[str, str]:
    if urlparse(url).scheme not in ("http", "https"):
        raise WebError("That is not a web link.")
    data = _post("/extract", {"urls": [url], "extract_depth": "basic", "format": "text", "timeout": 15}, opener)
    results = data.get("results") or []
    if not results:
        raise WebError("That page could not be read.")
    return {"source": source_name(url), "text": clean(results[0].get("raw_content"), 3000)}


def scrub_message(text: str) -> str:
    """What is sent to the web when checking a message: no links, emails, phone or account numbers."""
    value = re.sub(r"https?://\S+|www\.\S+", " ", str(text))
    value = re.sub(r"\S+@\S+", " ", value)
    value = re.sub(r"[\d][\d\s().-]{3,}[\d]", " ", value)
    value = re.sub(r"\d", " ", value)
    return " ".join(value.split())[:300]


def check_message(text: str, opener=None) -> List[Dict[str, str]]:
    query = f"scam warning {scrub_message(text)}".strip()
    body = {"query": query[:390], "search_depth": "basic", "max_results": 4, "include_domains": SCAM_SOURCES,
            "safe_search": True}
    return _results(_post("/search", body, opener))

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
import threading
import time
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

API = "https://api.tavily.com"
TIMEOUT_S = 12
# Crawl and map run up to their own server-side timeout (CRAWL_SERVER_S); the client waits a little longer,
# or it would give up at TIMEOUT_S while Tavily was still working (and charging) for the answer.
CRAWL_SERVER_S = 30
CRAWL_TIMEOUT_S = 35
SNIPPET = 320
SCAM_SOURCES = ["consumer.ftc.gov", "consumidor.ftc.gov", "ftc.gov", "identitytheft.gov", "aarp.org", "bbb.org",
                "ic3.gov", "fbi.gov", "usa.gov"]
INJECTION = re.compile(r"(?i)(ignore (all |any |the )?(previous|prior|above) instructions|system prompt|you are now|"
                       r"disregard (your|the) rules)")


class WebError(Exception):
    pass


class ResearchCutOff(WebError):
    """The research stream broke after the research had begun: starting it again would pay for it twice."""


def configured() -> bool:
    return bool(os.environ.get("TAVILY_API_KEY", ""))


def _key() -> str:
    key = os.environ.get("TAVILY_API_KEY", "")
    if not key:
        raise WebError("The web is not set up (no Tavily key).")
    return key


# "How Andy found this": while a tool runs inside traced(), each Tavily call notes what it was, its depth,
# the credits Tavily says it used (include_usage) and how long it took. Names and numbers only, never the query.
_TRAIL = threading.local()
USAGE_PATHS = ("/search", "/extract", "/crawl", "/map")


def traced(fn: Callable[[], Any]) -> Any:
    """Run fn; return (its result, how it was found), for the screen's card (board.show(..., how=...))."""
    _TRAIL.calls = []
    try:
        out = fn()
    finally:
        calls, _TRAIL.calls = _TRAIL.calls, None
    return out, how(calls)


def how(calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not calls:
        return {}
    credits = [c["credits"] for c in calls if c.get("credits") is not None]
    return {"calls": [c["call"] for c in calls][:4], "depth": next((c["depth"] for c in calls if c.get("depth")), ""),
            "credits": sum(credits) if credits else None, "seconds": round(sum(c["seconds"] for c in calls), 1)}


def _note(path: str, body: Optional[Dict[str, Any]], data: Dict[str, Any], seconds: float) -> None:
    calls = getattr(_TRAIL, "calls", None)
    if calls is None:
        return
    usage = data.get("usage") if isinstance(data, dict) else None
    credits = usage.get("credits") if isinstance(usage, dict) else None
    calls.append({"call": path.strip("/").split("/")[0], "seconds": seconds,
                  "depth": str((body or {}).get("search_depth") or (body or {}).get("extract_depth") or ""),
                  "credits": credits if isinstance(credits, (int, float)) else None})


def _post(path: str, body: Optional[Dict[str, Any]], opener: Optional[Callable] = None,
          project: bool = True, timeout: float = TIMEOUT_S) -> Dict[str, Any]:
    """POST body to Tavily, or GET when body is None."""
    if body is not None and path in USAGE_PATHS:
        body = {**body, "include_usage": True}      # the credits each call used, for "how Andy found this"
    started = time.monotonic()
    headers = {"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"}
    if project:   # Tavily counts this product's use apart from any other (X-Project-ID)
        headers["X-Project-ID"] = os.environ.get("TAVILY_PROJECT", "andy-companion")
    req = urllib.request.Request(API + path, method="POST" if body is not None else "GET",
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers)
    try:
        with (opener or urllib.request.urlopen)(req, timeout=timeout) as r:
            data = json.loads(r.read())
        _note(path, body, data, time.monotonic() - started)
        return data
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


def chosen_language(asked: Any, saved: Any) -> str:
    """The language to search in: the one the person is speaking, else the one they chose."""
    if asked in ("en", "es"):
        return asked
    return "es" if saved == "es" else "en"


def _search(body: Dict[str, Any], language: str, opener=None) -> List[Dict[str, str]]:
    """A search; for Spanish, Spanish pages only first (Tavily's `language` with `filter_by_language`,
    August 2026), then once without the filter if none were found, so a town with little Spanish news still
    gets an answer."""
    if language != "es":
        return _results(_post("/search", body, opener))
    found = _results(_post("/search", {**body, "language": "es", "filter_by_language": True}, opener))
    return found or _results(_post("/search", {**body, "language": "es"}, opener))


def local_news(place: str, topic: str = "", sources: Optional[List[str]] = None, opener=None,
               language: str = "en") -> List[Dict[str, str]]:
    # The query's own language decides the sources (Tavily's `language` option alone did not, in a
    # live test on 2026-10-13): a Spanish query finds Spanish-language local news; `_search` adds the
    # strict language filter Tavily added in August 2026.
    query = f"noticias locales {place} {topic}" if language == "es" else f"{place} local news {topic}"
    body = {"query": query.strip()[:390], "topic": "news", "time_range": "day",
            "search_depth": "basic", "max_results": 3, "safe_search": True}
    if sources:
        body["include_domains"] = sources
    found = _search(body, language, opener)
    # Chosen papers only, then widen once. Tavily's include_domains_mode "prefer" (one call) did not put
    # the chosen paper first in a live test on 2026-10-13, so "news from the papers you chose" keeps this.
    if not found and sources:          # the chosen papers had nothing today: widen once
        body.pop("include_domains")
        body["time_range"] = "week"
        found = _search(body, language, opener)
    return found


def look_up(question: str, place: str = "", opener=None) -> List[Dict[str, str]]:
    body = {"query": f"{question} {place}".strip()[:390], "search_depth": "basic", "max_results": 3, "safe_search": True}
    return _results(_post("/search", body, opener))


def whats_on(place: str, interest: str = "", pages: Optional[List[str]] = None, opener=None,
             language: str = "en") -> List[Dict[str, str]]:
    if pages:
        found: List[Dict[str, str]] = []
        for page in pages[:2]:
            # A slow page, or a site that refuses crawlers (403), must not lose the answer: the dated
            # search below still finds the week's events.
            try:
                data = _post("/crawl", {"url": page, "instructions": f"Events and activities this week {interest}".strip(),
                                        "max_depth": 1, "limit": 8, "chunks_per_source": 2, "timeout": CRAWL_SERVER_S},
                             opener, timeout=CRAWL_TIMEOUT_S)
            except WebError:
                continue
            for r in data.get("results", [])[:3]:
                found.append({"title": clean(r.get("url"), 140), "source": source_name(r.get("url", "")),
                              "summary": clean(r.get("raw_content"), SNIPPET), "url": r.get("url", "")})
        if found:
            return found
    from datetime import date, timedelta

    start = date.today()
    end = start + timedelta(days=6)
    if language == "es":
        from andy_companion import words

        week = f"del {start.day} de {words.month(start, 'es')} al {end.day} de {words.month(end, 'es')} de {end.year}"
        query = f"eventos {week} en {place} {interest}"
    else:
        week = f"{start.strftime('%B')} {start.day} to {end.strftime('%B')} {end.day} {end.year}"
        query = f"events {week} in {place} {interest}"
    body = {"query": query.strip()[:390], "time_range": "week",
            "search_depth": "basic", "max_results": 4, "safe_search": True}
    return _search(body, language, opener)


# --- finding the town's events page: Tavily search, then map ----------------------------------------

OFFICIAL = re.compile(r"\.(gov|us)$|\.(fl|ca|ny|tx)\.us$|city|town|village|county", re.I)
EVENTS = re.compile(r"(calendar|events?|activities|things-to-do|whats-on|recreation|parks)", re.I)
SKIP_PATH = re.compile(r"(\.pdf$|/login|/account|/search|/news/|/\d{4}/\d{2}/)", re.I)


NOT_A_TOWN = re.compile(r"(trip|yelp|wikipedia|facebook|instagram|twitter|x\.com|youtube|linkedin|zillow|realtor|"
                        r"expedia|booking|hotels|travel|visit|news|times|post|herald|patch|nextdoor|reddit|wiki)", re.I)


def official_site(place: str, opener=None) -> Optional[str]:
    """The town's own website: an official-looking result (.gov, .us, city, town) if there is one, else the first
    that isn't a travel, review, social, news or encyclopedia site."""
    body = {"query": f"{place} official city government website"[:390], "search_depth": "basic", "max_results": 5,
            "safe_search": True}
    # The address as found ("www." kept), so the map starts where the site really is.
    hosts = [urlparse(str(r.get("url", ""))).netloc.lower() for r in _post("/search", body, opener).get("results", [])]
    hosts = [h for h in hosts if h]
    for h in hosts:
        if OFFICIAL.search(h.split(":")[0]):
            return "https://" + h
    for h in hosts:
        if not NOT_A_TOWN.search(h):
            return "https://" + h
    return None


def map_site(url: str, instructions: str = "", opener=None) -> List[str]:
    """Tavily map: the pages of a site, guided by instructions."""
    body = {"url": url, "max_depth": 2, "max_breadth": 30, "limit": 60, "instructions": instructions[:200],
            "timeout": CRAWL_SERVER_S}
    return [str(u) for u in _post("/map", body, opener, timeout=CRAWL_TIMEOUT_S).get("results", [])
            if isinstance(u, str)]


def find_events_page(place: str, opener=None) -> Optional[Dict[str, str]]:
    """The town's events calendar, found from its official site with Tavily map, or None."""
    site = official_site(place, opener)
    if not site:
        return None
    pages = [u for u in map_site(site, "The calendar of community events and activities", opener)
             if EVENTS.search(u) and not SKIP_PATH.search(u)]
    if not pages:
        # Some town sites refuse crawlers (harborbayfl.gov answers 403, and its map came back empty, 2026-10-14),
        # but their pages are still in Tavily's search index: search within the town's own site instead.
        host = urlparse(site).netloc
        found = _post("/search", {"query": f"{place} events calendar"[:390], "search_depth": "basic", "max_results": 5,
                                  "include_domains": [host.removeprefix("www.")], "safe_search": True}, opener)
        pages = [str(r.get("url", "")) for r in found.get("results", [])]
        pages = [u for u in pages if EVENTS.search(u) and not SKIP_PATH.search(u)]
    if not pages:
        return None
    # Shortest first: the calendar's own page rather than one event on it.
    page = min(pages, key=lambda u: (0 if re.search(r"calendar|events", u, re.I) else 1, len(u)))
    return {"site": site, "page": page.rstrip("/")}


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


SPANISH = re.compile(r"[ñ¿¡]|\b(que|usted|su|por favor|dinero|cuenta|para|necesito|tarjeta|abuel[oa])\b", re.I)


def check_message(text: str, opener=None) -> List[Dict[str, str]]:
    # A Spanish message is searched in Spanish too, where the FTC's Spanish pages (consumidor.ftc.gov)
    # answer: the English query found nothing for a Spanish grandchild scam (2026-10-14).
    lead = "estafa aviso" if len(SPANISH.findall(str(text))) >= 2 else "scam warning"
    query = f"{lead} {scrub_message(text)}".strip()
    # Advanced depth: on a prize-scam letter, basic found nothing and advanced found four exact AARP
    # and FTC warnings (2026-10-13). It costs two credits instead of one; a scam check is worth it.
    body = {"query": query[:390], "search_depth": "advanced", "max_results": 4, "include_domains": SCAM_SOURCES,
            "safe_search": True}
    return _results(_post("/search", body, opener))


# --- look into it: Tavily research, for a question that needs more than one search ----------------

RESEARCH_SCHEMA = {
    "properties": {
        "say": {"type": "string", "description": "The answer for an older adult, spoken aloud: two or three short, "
                                                 "plain sentences, with dates where they matter. No lists, no links."},
        "key_points": {"type": "array", "items": {"type": "string"},
                       "description": "Up to four short facts to show on a screen, each under 15 words."},
    },
    "required": ["say", "key_points"],
}


def start_research(question: str, place: str = "", language: str = "en", opener=None) -> str:
    """Start a Tavily research task to collect later (the fallback when streaming fails); returns its id."""
    data = _post("/research", _research_body(question, place, language, False), opener)
    rid = str(data.get("request_id", ""))
    if not rid:
        raise WebError("The research did not start.")
    return rid


def _research_body(question: str, place: str, language: str, stream: bool) -> Dict[str, Any]:
    where = f" They live in {place}; prefer official and local sources for anything local." if place else ""
    lang = " Answer in Spanish." if language == "es" else ""
    task = (f"An older adult asked their home companion robot to look into this: {question.strip()[:600]}.{where} "
            f"Find what is true and current, with dates.{lang}")
    body = {"input": task, "model": "mini", "output_schema": RESEARCH_SCHEMA, "citation_format": "numbered",
            "output_length": "short"}
    if stream:
        body["stream"] = True
    return body


def _answer(content: Any, sources: Any) -> Dict[str, Any]:
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except ValueError:
            content = {"say": content}
    content = content if isinstance(content, dict) else {}
    found = [{"title": clean(s.get("title"), 140), "source": source_name(s.get("url", "")), "url": s.get("url", "")}
             for s in (sources or [])[:6] if isinstance(s, dict)]
    return {"status": "completed", "say": clean(content.get("say", ""), 700),
            "points": [clean(p, 160) for p in list(content.get("key_points") or [])[:4]], "sources": found}


def stream_research(question: str, place: str = "", language: str = "en",
                    on_step: Optional[Callable[[str, str], None]] = None, opener=None,
                    timeout_s: float = 120) -> Dict[str, Any]:
    """Tavily research as a stream, so each step can be shown while it happens:
    on_step("planning"|"searching"|"reading"|"writing", detail). Returns the answer like research_result."""
    req = urllib.request.Request(API + "/research", method="POST",
                                 data=json.dumps(_research_body(question, place, language, True)).encode(),
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json",
                                          "X-Project-ID": os.environ.get("TAVILY_PROJECT", "andy-companion")})
    step = on_step or (lambda kind, detail: None)
    content: Any = None
    sources: Any = None
    began = False   # once Tavily has sent anything, the research is under way (and paid for)
    try:
        with (opener or urllib.request.urlopen)(req, timeout=timeout_s) as r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                try:
                    delta = (json.loads(line[5:]).get("choices") or [{}])[0].get("delta") or {}
                except ValueError:
                    continue
                began = True
                calls = delta.get("tool_calls") or {}
                for call in calls.get("tool_call") or []:
                    name = str(call.get("name", ""))
                    if name == "Planning":
                        step("planning", "")
                    elif name == "WebSearch":
                        step("searching", str(len(call.get("queries") or [])))
                    elif name == "Generating":
                        step("writing", "")
                for resp in calls.get("tool_response") or []:
                    names = list(dict.fromkeys(source_name(s.get("url", "")) for s in resp.get("sources") or []
                                               if isinstance(s, dict)))
                    names = [n for n in names if n]
                    if names:
                        more = f" and {len(names) - 4} more" if len(names) > 4 else ""
                        step("reading", ", ".join(names[:4]) + more)
                if "content" in delta:
                    content = delta["content"]
                if "sources" in delta:
                    sources = delta["sources"]
    except WebError:
        raise
    except Exception as e:   # never echo the request: it holds what the person asked
        raise (ResearchCutOff if began else WebError)(f"The research did not finish ({type(e).__name__}).") from None
    if content is None:
        raise (ResearchCutOff if began else WebError)("The research gave no answer.")
    return _answer(content, sources)


def research_result(request_id: str, opener=None) -> Dict[str, Any]:
    """{"status": "pending"|"completed"|"failed", "say", "points", "sources"} for a research task."""
    data = _post(f"/research/{urllib.parse.quote(request_id)}", None, opener)
    status = str(data.get("status", "pending"))
    if status != "completed":
        return {"status": "failed" if status == "failed" else "pending"}
    return _answer(data.get("content"), data.get("sources"))

def usage(opener=None) -> Dict[str, Any]:
    """This month's Tavily credits for the account, as numbers only (GET /usage; no credits used).
    Asked without X-Project-ID: with it, Tavily reports only that project's use (2026-10-13)."""
    account = (_post("/usage", None, opener, project=False) or {}).get("account") or {}

    def num(v):
        return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    return {"plan": str(account.get("current_plan", ""))[:40], "used": num(account.get("plan_usage")),
            "limit": num(account.get("plan_limit")),
            "by": {k: num(account.get(f"{k}_usage")) or 0 for k in ("search", "extract", "crawl", "map", "research")}}

"""Look into it: a question that needs more than one search, answered when it is ready.

"Andy, look into the new bus routes for me." Andy says it will, and carries on. Tavily's research
agent searches and reads several sources and returns a short, structured answer; when it is ready
the answer goes to Andy's inbox, and at its next quiet moment Andy says it (two or three plain
sentences, sources named) while the sources show on the screen. One question at a time, a few a
day, so a household's Tavily credits last the month. Nothing about the question is logged.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Dict, Optional

from andy_companion import board, web

logger = logging.getLogger("andy.looking")
POLL_S = 5.0
GIVE_UP_S = 300.0
PER_DAY = 10

_lock = threading.Lock()
_state: Dict[str, object] = {"busy": False, "day": "", "count": 0, "question": ""}
ALREADY = {"started": True, "say": "Already looking into it; carry on with the person."}


def _today() -> str:
    return time.strftime("%Y-%m-%d")


def start(question: str, place: str = "", language: str = "en", runner: Optional[Callable] = None) -> Dict[str, object]:
    """Begin looking into it in the background. Returns what Andy should say now."""
    question = " ".join(str(question or "").split())
    if not question:
        return {"started": False, "say": "Ask what to look into."}
    if not web.configured():   # never promise an answer that cannot come
        return {"started": False, "say": "Say plainly that you can't look things up right now."}
    with _lock:
        if _state["day"] != _today():
            _state["day"], _state["count"] = _today(), 0
        if _state["busy"] and _state["question"] == question:
            return ALREADY                     # the model asked twice in one turn: once is enough
        if _state["busy"]:
            return {"started": False, "say": "I'm still looking into the last question; I'll tell you when it's ready."}
        if int(_state["count"]) >= PER_DAY:
            return {"started": False, "say": "That's all the looking into I can do today; ask me again tomorrow."}
        _state["busy"] = True
        _state["question"] = question
        _state["count"] = int(_state["count"]) + 1
    thread = threading.Thread(target=runner or run, args=(question, place, language), name="andy-looking", daemon=True)
    thread.start()
    return {"started": True, "say": ("Started. Say you will look into it and tell them in a minute or two, then carry on. The answer comes"
                                     " by itself: do not check on it (no task_status), do not search for it now, and do not call look_into again.")}


STEPS = {"planning": "Planning what to look for", "searching": "Searching the web", "reading": "Reading",
         "writing": "Writing the answer"}


def show_progress(topic: str, done: list, seconds: float = 0.0, sites: int = 0) -> None:
    """On the screen beside Andy, each step as Tavily takes it, how long it has taken so far, and how many
    sites it has read."""
    board.show("research", f"Looking into: {topic}", [{"title": t, "summary": d} for t, d in done[-4:]],
               how={"calls": ["research"], "depth": "mini", "seconds": round(seconds, 1), "sites": sites})


def run(question: str, place: str = "", language: str = "en", opener=None,
        sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic) -> Optional[Dict]:
    """Look into it, showing each step on the screen, and leave the answer (or a plain failure) in Andy's inbox.
    Streams Tavily research; if the stream fails before the research begins, starts it again without
    streaming and collects the answer when ready. Once it has begun, a second one would pay twice."""
    topic = question[:120]
    done: list = []
    began = clock()
    read = {"sites": 0}

    def on_step(kind: str, detail: str) -> None:
        if kind == "sites":                 # a running count, not a step of its own
            read["sites"] = int(detail) if str(detail).isdigit() else read["sites"]
            show_progress(topic, done, clock() - began, read["sites"])
            return
        if kind == "searching":
            done.append((STEPS[kind], f"{detail} searches" if detail and detail != "0" else ""))
        else:
            done.append((STEPS[kind], detail))
        show_progress(topic, done, clock() - began, read["sites"])

    try:
        show_progress(topic, [("Starting", "")])
        try:
            result = web.stream_research(question, place, language, on_step, opener)
        except web.ResearchCutOff:
            result = None
        except web.WebError:
            result = _collect(question, place, language, opener, sleep, clock)
        if result and result.get("say"):
            board.research_ready(topic, result["say"], result.get("points", []), result.get("sources", []))
            logger.info("Looked into a question: %d sources", len(result.get("sources", [])))
            return result
        board.research_ready(topic, "", [], [], failed=True)
        logger.info("Looking into a question did not finish")
    except Exception as e:   # any failure is told, so the promised answer is never left hanging
        board.research_ready(topic, "", [], [], failed=True)
        logger.info("Looking into a question failed: %s", type(e).__name__)
    finally:
        with _lock:
            _state["busy"] = False
    return None


def _collect(question, place, language, opener, sleep, clock) -> Optional[Dict]:
    rid = web.start_research(question, place, language, opener)
    began = clock()
    while clock() - began < GIVE_UP_S:
        sleep(POLL_S)
        result = web.research_result(rid, opener)
        if result["status"] == "completed":
            return result
        if result["status"] == "failed":
            return None
    return None

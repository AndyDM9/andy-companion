"""Round 5, B37: Tavily's session header on every call, random and renewed after a quiet half hour."""

import io
import json

from andy_companion import web


def test_every_call_carries_the_project_and_one_session(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setitem(web._session, "id", "")
    seen = []

    def opener(req, timeout=None):
        seen.append(dict(req.header_items()))
        return io.BytesIO(json.dumps({"results": []}).encode())

    web.look_up("library hours", opener=opener)
    web.look_up("pharmacy hours", opener=opener)
    ids = {h["X-session-id"] for h in seen}
    assert len(ids) == 1 and next(iter(ids)).startswith("andy-") and len(next(iter(ids))) == 21
    assert all(h["X-project-id"] == "andy-companion" for h in seen)
    assert "X-human-id" not in seen[0]


def test_a_new_session_after_a_quiet_half_hour(monkeypatch):
    monkeypatch.setitem(web._session, "id", "")
    first = web.session_id(clock=lambda: 1000.0)
    assert web.session_id(clock=lambda: 1000.0 + 60) == first
    assert web.session_id(clock=lambda: 1060.0 + web.SESSION_IDLE_S + 1) != first

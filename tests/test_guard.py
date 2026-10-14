import asyncio
import io
import json

import pytest

from andy_companion import guard, urgent

PILLS = "I've been putting my pills aside for when I've had enough."
SELF_HARM = {"unsafe": True, "categories": ["Suicide and Self Harm"]}


def test_the_net_alone_does_not_know_these_words():
    """Why the second look exists."""
    assert not urgent.is_urgent(PILLS)


@pytest.mark.parametrize("text, out", [
    ("User Safety: unsafe\nSafety Categories: Suicide and Self Harm", SELF_HARM),
    ("User Safety: safe", {"unsafe": False, "categories": []}),
    ("<think>reasoning</think>User Safety: unsafe\nSafety Categories: Violence, Fraud/Deception",
     {"unsafe": True, "categories": ["Violence", "Fraud/Deception"]}),
])
def test_the_models_answer_is_read(text, out):
    assert guard.parse(text) == out


def test_only_self_harm_is_acted_on():
    assert guard.is_self_harm(SELF_HARM)
    assert not guard.is_self_harm({"unsafe": True, "categories": ["Fraud/Deception"]})
    assert not guard.is_self_harm({"unsafe": False, "categories": ["Suicide and Self Harm"]})
    assert not guard.is_self_harm(None)


class Opener:
    def __init__(self, content):
        self.content, self.requests = content, []

    def __call__(self, req, timeout=None):
        self.requests.append((req.full_url, json.loads(req.data), dict(req.headers), timeout))
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": self.content}}]}).encode())


def test_the_check_sends_only_the_words_over_https_with_the_token():
    op = Opener("User Safety: unsafe\nSafety Categories: Suicide and Self Harm")
    out = guard.classify(PILLS, opener=op, config={"url": "https://guard.example", "token": "t0k"})
    assert out == {**SELF_HARM, "policy": True}
    url, body, headers, timeout = op.requests[0]
    assert url == "https://guard.example/v1/chat/completions" and headers["Authorization"] == "Bearer t0k"
    assert body["messages"] == [{"role": "user", "content": [{"type": "text", "text": PILLS}]}]
    assert body["chat_template_kwargs"]["enable_thinking"] is False and timeout == guard.TIMEOUT_S
    assert body["chat_template_kwargs"]["custom_policy"] == guard.POLICY


def test_under_the_policy_unsafe_means_self_harm_and_nothing_else():
    """The policy asks one question, so the model gives no category; unsafe is the answer."""
    op = Opener("User Safety: unsafe")
    assert guard.is_self_harm(guard.classify(PILLS, opener=op, config={"url": "https://g.example", "token": "t"}))
    op = Opener("User Safety: unsafe\nSafety Categories: Fraud/Deception")
    assert not guard.is_self_harm(guard.classify(PILLS, opener=op, config={"url": "https://g.example", "token": "t"},
                                                 policy=False))


def test_no_endpoint_or_plain_http_means_no_check(monkeypatch):
    monkeypatch.delenv("ANDY_GUARD_URL", raising=False)
    assert guard.classify(PILLS) is None
    monkeypatch.setenv("ANDY_GUARD_URL", "http://10.0.0.1:8000")
    monkeypatch.setenv("ANDY_GUARD_TOKEN", "t")
    assert guard._config() is None


def test_a_failed_check_never_stops_anything():
    def broken(req, timeout=None):
        raise OSError("down")
    assert guard.classify(PILLS, opener=broken, config={"url": "https://g.example", "token": "t"}) is None


def run_turn(monkeypatch, result, reply, reply_first=False, words=PILLS):
    said, checked = [], []

    async def follow_up(handler, frame):
        said.append(frame)

    monkeypatch.setattr(urgent, "_follow_up", follow_up)

    class Handler:
        def _emit_transcript(self, role, text, final=True):
            pass

    def check(text):
        checked.append(text)
        return result

    guard.install(Handler, check=check)

    async def scene():
        h = Handler()
        if reply_first:
            h._emit_transcript("user", words)
            h._emit_transcript("assistant", reply)
        else:
            h._emit_transcript("user", words)
            for _ in range(50):
                await asyncio.sleep(0.01)
                if h._andy_guard_turn is None or h._andy_guard_turn.checked:
                    break
            h._emit_transcript("assistant", reply)
        for _ in range(50):
            await asyncio.sleep(0.01)

    asyncio.run(scene())
    return said, checked


def test_self_harm_found_and_no_988_in_the_reply_gets_the_988_sentence(monkeypatch):
    said, _ = run_turn(monkeypatch, SELF_HARM, "That sounds hard. Shall we talk about your day?")
    assert said == [urgent.FRAME_CRISIS]


def test_it_works_whichever_comes_first_the_check_or_the_reply(monkeypatch):
    said, _ = run_turn(monkeypatch, SELF_HARM, "That sounds hard.", reply_first=True)
    assert said == [urgent.FRAME_CRISIS]


def test_a_reply_that_already_gave_988_needs_nothing_more(monkeypatch):
    said, _ = run_turn(monkeypatch, SELF_HARM, "I'm glad you told me. You can call or text 988 any time, and call 911 if you are in danger.")
    assert said == []


def test_other_categories_are_not_acted_on(monkeypatch):
    said, _ = run_turn(monkeypatch, {"unsafe": True, "categories": ["Fraud/Deception"]}, "Hmm.")
    assert said == []


def test_words_the_net_knows_are_left_to_the_net(monkeypatch):
    said, checked = run_turn(monkeypatch, SELF_HARM, "That sounds hard.", words="I want to die.")
    assert checked == [] and said == []


def test_a_stopped_endpoint_is_logged_once_not_every_turn(monkeypatch, caplog):
    import logging

    now = [0.0]
    monkeypatch.setattr(guard, "_clock", lambda: now[0])
    monkeypatch.setattr(guard, "_down_logged", None)
    config = {"url": "https://g.example", "token": "t"}

    def broken(req, timeout=None):
        raise OSError("down")

    def working(req, timeout=None):
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": "User Safety: safe"}}]}).encode())

    def lines():
        return [r.getMessage() for r in caplog.records if r.name == "andy.guard"]

    with caplog.at_level(logging.INFO, logger="andy.guard"):
        for _ in range(5):
            assert guard.classify(PILLS, opener=broken, config=config) is None
            now[0] += 30
        assert lines() == ["Content safety check unavailable: OSError"]
        now[0] += guard.QUIET_S                                   # still down ten minutes later: one reminder
        guard.classify(PILLS, opener=broken, config=config)
        assert len(lines()) == 2
        guard.classify(PILLS, opener=working, config=config)      # back: said once
        guard.classify(PILLS, opener=working, config=config)
        guard.classify(PILLS, opener=broken, config=config)       # down again: said again at once
        assert lines()[2:] == ["Content safety check answering again", "Content safety check unavailable: OSError"]
    assert all("pills" not in line for line in lines())

"""Real confirmation code, synthetic model responses, no SDK or household side effects."""
import importlib.util
import json
from pathlib import Path
import threading
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from andy_companion.judge_playground import CHALLENGES, NOTE, Playground, Unavailable

ROOT = Path(__file__).resolve().parents[1]


def call(name, args):
    return {"content": "", "tool_calls": [{"id": "sample_call", "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}]}


def make(chat=None, **kwargs):
    def provider(body):
        message = chat(body)
        return {"choices": [{"finish_reason": "tool_calls" if message.get("tool_calls") else "stop",
                             "message": message}]}
    return Playground(profile_path=ROOT / "profiles/companion/profile.md", tools_path=ROOT / "evals/tools.json",
                      chat=provider if chat else None, **kwargs)


def sharing():
    return call("share_with_family", {"note": NOTE})


@pytest.mark.parametrize("challenge,args,reply", [("letter", {}, "The sample bill is $86.40, due October 28."),
                                                ("absent", {"what": "reading glasses"}, "I couldn't see the glasses.")])
def test_all_challenges_use_real_model_selection_and_only_simulated_tools(challenge, args, reply):
    requests = []

    def model(body):
        requests.append(body)
        return call(CHALLENGES[challenge]["tool"], args) if len(requests) == 1 else {"content": reply}

    engine = make(model)
    result = engine.run({"challenge": challenge})
    assert result["reply"] == reply and result["reply_source"] == "model"
    assert result["tools"][0]["simulated"] is True
    assert len(requests[0]["tools"]) == 1 and "tools" not in requests[1]
    assert requests[0]["messages"][0]["content"].startswith("## WHO YOU ARE")
    assert engine.calls == 2


@pytest.mark.parametrize("decision,expected_calls,shared", [("yes", 3, True), ("no", 1, False)])
def test_confirmation_requires_fresh_choice_and_cannot_be_replayed(decision, expected_calls, shared):
    requests = []

    def model(body):
        requests.append(body)
        return sharing() if body.get("tools") else {"content": "The sample note is shared."}

    engine = make(model)
    first = engine.run({"challenge": "choice"})
    assert first["awaiting_choice"] and not first["sample_family_shared"]
    assert NOTE in first["reply"] and first["reply_source"] == "confirmation code"
    second = engine.run({"challenge": "choice", "session": first["session"], "choice": decision})
    assert second["sample_family_shared"] is shared and not second["awaiting_choice"]
    assert engine.calls == expected_calls
    with pytest.raises(Unavailable, match="step_already_handled"):
        engine.run({"challenge": "choice", "session": first["session"], "choice": "yes"})
    assert engine.calls == expected_calls


def test_sessions_do_not_share_approval_or_family_state():
    engine = make(lambda body: sharing() if body.get("tools") else {"content": "Done."})
    a, b = (engine.run({"challenge": "choice"}) for _ in range(2))
    engine.run({"challenge": "choice", "session": a["session"], "choice": "yes"})
    assert engine.sessions[a["session"]]["shared"] is True
    assert engine.sessions[b["session"]]["shared"] is False
    with pytest.raises(Unavailable, match="session_expired"):
        engine.run({"challenge": "letter", "session": b["session"], "choice": "yes"})


def test_old_confirmation_and_session_expire_without_writing():
    now = [0.0]
    engine = make(lambda body: sharing() if body.get("tools") else {"content": "Nothing was shared."},
                  clock=lambda: now[0])
    first = engine.run({"challenge": "choice"})
    now[0] = 121
    result = engine.run({"challenge": "choice", "session": first["session"], "choice": "yes"})
    assert not result["sample_family_shared"]
    fresh = engine.run({"challenge": "choice"})
    now[0] += 301
    with pytest.raises(Unavailable, match="session_expired"):
        engine.run({"challenge": "choice", "session": fresh["session"], "choice": "yes"})
    assert not engine.sessions


def test_idle_session_expiry_does_not_need_another_challenge():
    now = [0]
    engine = make(lambda body: sharing(), clock=lambda: now[0])
    engine.run({"challenge": "choice"})
    assert engine.sessions
    now[0] = 301
    engine.expire()
    assert engine.sessions == {}


@pytest.mark.parametrize("body", [[], None, {"challenge": "unknown"}, {"challenge": ["letter"]},
    {"challenge": "letter", "text": "must never reach a model"}, {"challenge": "choice", "choice": "yes"},
    {"challenge": "choice", "choice": "anything"}, {"challenge": "letter", "session": "bad"}])
def test_only_fixed_inputs_are_accepted(body):
    engine = make(lambda body: pytest.fail("bad inputs reached inference"))
    with pytest.raises(Unavailable):
        engine.run(body)
    assert engine.calls == 0


@pytest.mark.parametrize("bad", [call("remember_fact", {"fact": "invented"}),
    call("share_with_family", {"note": "Something outside the fixed sample"}),
    call("share_with_family", {"note": NOTE, "extra": True}),
    {"tool_calls": [{"function": {"name": "share_with_family", "arguments": json.dumps({"note": NOTE})}}]},
    {"tool_calls": [sharing()["tool_calls"][0]] * 2}])
def test_model_cannot_choose_extra_actions_or_change_the_note(bad):
    engine = make(lambda body: bad)
    with pytest.raises(Unavailable):
        engine.run({"challenge": "choice"})
    assert not any(s["shared"] for s in engine.sessions.values())


def test_failed_calls_count_toward_daily_allowance_and_reset_at_utc_day():
    wall = [0]
    def unavailable(body):
        raise Unavailable("model_unavailable", 502)
    engine = make(unavailable, wall_clock=lambda: wall[0], daily_limit=1)
    with pytest.raises(Unavailable, match="model_unavailable"):
        engine.run({"challenge": "letter"})
    with pytest.raises(Unavailable, match="public_allowance_reached"):
        engine.run({"challenge": "letter"})
    wall[0] = 86400
    with pytest.raises(Unavailable, match="model_unavailable"):
        engine.run({"challenge": "letter"})
    assert engine.calls == 1


def test_global_concurrency_is_bounded():
    entered = threading.Barrier(3)
    release = threading.Event()
    def model(body):
        entered.wait(timeout=3)
        assert release.wait(3)
        return {"content": "An invented response."}
    engine = make(model)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(2) as pool:
        tasks = [pool.submit(engine.run, {"challenge": "letter"}) for _ in range(2)]
        try:
            entered.wait(timeout=3)
            with pytest.raises(Unavailable, match="busy"):
                engine.run({"challenge": "letter"})
            assert engine.calls == 2
        finally:
            release.set()
        for task in tasks:
            assert task.result(timeout=3)["reply"] == "An invented response."
    assert engine.inflight == 0


def test_provider_failures_do_not_expose_response_text_or_credentials(monkeypatch, capsys):
    engine = make(key="invented-private-key")
    def fail(*args, **kwargs):
        raise HTTPError("https://example.invalid", 500, "invented-private-key", {}, None)
    monkeypatch.setattr("urllib.request.urlopen", fail)
    with pytest.raises(Unavailable, match="model_unavailable") as error:
        engine.run({"challenge": "letter"})
    assert "invented-private-key" not in str(error.value)
    assert capsys.readouterr() == ("", "")
    assert "invented-private-key" not in json.dumps(engine.metadata())


def test_closing_reply_failure_preserves_truthful_sample_state():
    count = [0]
    def model(body):
        count[0] += 1
        if count[0] == 3:
            raise Unavailable("model_unavailable", 502)
        return sharing()
    engine = make(model)
    first = engine.run({"challenge": "choice"})
    result = engine.run({"challenge": "choice", "session": first["session"], "choice": "yes"})
    assert result["sample_family_shared"] and result["reply_source"] == "code"
    assert "could not finish" in result["reply"]


def test_the_closing_request_asks_for_words_without_keeping_that_line():
    requests = []

    def model(body):
        requests.append(body)
        return call("read_letter", {}) if len(requests) == 1 else {"content": "The sample bill is $86.40."}

    engine = make(model)
    result = engine.run({"challenge": "letter"})
    assert requests[1]["messages"][-1]["role"] == "system" and "plain words" in requests[1]["messages"][-1]["content"]
    assert "tools" not in requests[1]
    kept = engine.sessions[result["session"]]["messages"]
    assert not any(m["role"] == "system" and "plain words" in m["content"] for m in kept)


def test_a_closing_reply_written_as_a_tool_call_is_never_shown():
    """2026-10-30: the closing reply came back as "<tool_call><function=read_letter></function></tool_call>"."""
    written = "<tool_call>\n<function=read_letter>\n</function>\n</tool_call>"
    requests = []

    def model(body):
        requests.append(body)
        return call("read_letter", {}) if len(requests) == 1 else {"content": written}

    result = make(model).run({"challenge": "letter"})
    assert "<" not in result["reply"] and result["reply_source"] == "code"
    assert "could not finish" in result["reply"] and result["tools"][0]["simulated"] is True


def test_words_around_a_written_call_are_kept_and_the_markup_dropped():
    requests = []

    def model(body):
        requests.append(body)
        return call("read_letter", {}) if len(requests) == 1 else {
            "content": "The sample bill is $86.40. <tool_call><function=read_letter></function></tool_call>"}

    result = make(model).run({"challenge": "letter"})
    assert result["reply"] == "The sample bill is $86.40." and result["reply_source"] == "model"


def test_a_first_reply_that_is_only_a_written_call_is_refused():
    engine = make(lambda body: {"content": "<tool_call><function=read_letter></function></tool_call>"})
    with pytest.raises(Unavailable, match="model_response_invalid"):
        engine.run({"challenge": "letter"})


@pytest.fixture
def site():
    spec = importlib.util.spec_from_file_location("judge_server_for_tests", ROOT / "scripts/judge_playground.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = make(lambda body: sharing())
    httpd = module.server(engine, ("127.0.0.1", 0), public_origin="https://judge.example")
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", engine
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def test_http_pages_headers_and_fixed_challenge_work(site, capsys):
    base, engine = site
    for path in ("/", "/judge.js", "/fonts/atkinson-hyperlegible-400.woff2", "/api/status"):
        with urlopen(base + path, timeout=3) as response:
            assert response.status == 200 and response.read()
            assert response.headers["Cache-Control"] == "no-store"
            assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    request = Request(base + "/api/run", data=b'{"challenge":"choice"}',
                      headers={"Content-Type": "application/json", "Origin": "https://judge.example"})
    with urlopen(request, timeout=3) as response:
        assert json.load(response)["awaiting_choice"]
    assert engine.calls == 1
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("theme", ["system", "dark"])
def test_huggingface_embedded_theme_url_serves_the_application(site, theme):
    base, engine = site
    with urlopen(base + "/?__theme=" + theme, timeout=3) as response:
        page = response.read()
        assert response.status == 200 and "text/html" in response.headers["Content-Type"]
        assert b'src="/judge.js"' in page and b'id="run"' in page
    assert engine.calls == 0


@pytest.mark.parametrize("path,data,headers,status", [
    ("/api/run", b'{"challenge":"choice"}', {"Origin": "https://other.example", "Content-Type": "application/json"}, 403),
    ("/api/run", b'{"challenge":"choice"}', {"Content-Type": "text/plain"}, 415),
    ("/api/run", b'x' * 513, {"Content-Type": "application/json"}, 413),
    ("/api/run", b'{"challenge":"letter","text":"private input rejected"}', {"Content-Type": "application/json"}, 400),
    ("/api/run", b'[]', {"Content-Type": "application/json"}, 400),
    ("/api/family", b'{}', {"Content-Type": "application/json"}, 404),
])
def test_http_refuses_unexpected_requests_without_inference_or_logging(site, capsys, path, data, headers, status):
    base, engine = site
    with pytest.raises(HTTPError) as error:
        urlopen(Request(base + path, data=data, headers=headers), timeout=3)
    assert error.value.code == status and engine.calls == 0
    assert capsys.readouterr() == ("", "")


def test_no_key_does_not_claim_live_inference():
    engine = make()
    assert not engine.metadata()["enabled"]
    with pytest.raises(Unavailable, match="not_configured"):
        engine.run({"challenge": "letter"})


def test_fresh_server_import_never_loads_household_or_robot_modules(tmp_path):
    code = ("import importlib.util,sys\n"
            f"spec=importlib.util.spec_from_file_location('judge_check',{str(ROOT / 'scripts/judge_playground.py')!r})\n"
            "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\n"
            "assert not any(n.startswith(('reachy_mini','andy_companion.board','andy_companion.reminders',"
            "'andy_companion.vision','andy_companion.settings','andy_companion.screen_server')) for n in sys.modules)\n")
    subprocess.run([sys.executable, "-I", "-c", code], check=True, cwd=tmp_path, capture_output=True, timeout=10)


@pytest.mark.parametrize("path", ["/api/family", "/api/screen", "/setup?s=demo-setup", "/.env", "/../.env"])
def test_household_and_file_routes_are_absent(site, path):
    base, engine = site
    with pytest.raises(HTTPError) as error:
        urlopen(base + path, timeout=3)
    assert error.value.code == 404 and engine.calls == 0

"""Invented provider envelopes through the real public-playground transport; no network or robot."""
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from andy_companion.judge_playground import NOTE, Playground, Unavailable

ROOT = Path(__file__).resolve().parents[1]
OMITTED = object()


def envelope(message, finish="stop"):
    choice = {"message": message}
    if finish is not OMITTED:
        choice["finish_reason"] = finish
    return {"choices": [choice]}


def sharing(**extra):
    return {"content": None, "tool_calls": [{"id": "invented_call", "type": "function",
            "function": {"name": "share_with_family", "arguments": json.dumps({"note": NOTE})}}], **extra}


def engine(monkeypatch, *responses):
    pending = iter(responses)
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(json.dumps(next(pending)).encode()))
    return Playground(profile_path=ROOT / "profiles/companion/profile.md", tools_path=ROOT / "evals/tools.json",
                      key="invented-test-key")


@pytest.mark.parametrize("finish", ["length", "content_filter", "tool_calls", "function_call", "error", None, OMITTED])
def test_incomplete_or_unmarked_text_never_becomes_a_public_answer(monkeypatch, capsys, finish):
    app = engine(monkeypatch, envelope({"content": "invented unfinished answer"}, finish))
    with pytest.raises(Unavailable, match="model_response_invalid") as error:
        app.run({"challenge": "letter"})
    assert str(error.value) == "model_response_invalid" and error.value.status == 502
    assert app.calls == 1 and app.inflight == 0
    assert not any(s["shared"] or s["awaiting"] for s in app.sessions.values())
    assert "invented unfinished answer" not in json.dumps(list(app.sessions.values()), default=str)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("finish", ["length", "content_filter", "stop", "function_call", "error", None, OMITTED])
def test_parseable_but_unfinished_tool_call_cannot_prepare_a_confirmation(monkeypatch, finish):
    app = engine(monkeypatch, envelope(sharing(), finish))
    with pytest.raises(Unavailable, match="model_response_invalid"):
        app.run({"challenge": "choice"})
    assert app.calls == 1
    assert not any(s["shared"] or s["awaiting"] or s["gate"].pending for s in app.sessions.values())


@pytest.mark.parametrize("payload", [None, [], {}, {"choices": []}, {"choices": {}}, {"choices": [None]},
    {"choices": [{"finish_reason": "stop"}]}, envelope(None), envelope([]), envelope({"content": None}),
    envelope({"content": 5}), envelope({"content": ""}), envelope({"content": "  "}),
    envelope({"content": "<THINK>unfinished"}), envelope({"content": "draft</think>"}),
    envelope({"content": "answer", "refusal": "invented refusal"}),
    envelope({"content": "answer", "function_call": {"name": "invented"}}),
    envelope({"role": "user", "content": "invented wrong role"}),
    envelope({"content": "answer", "tool_calls": {}})])
def test_malformed_envelopes_have_fixed_errors_without_state_changes(monkeypatch, payload):
    app = engine(monkeypatch, payload)
    with pytest.raises(Unavailable, match="model_response_invalid"):
        app.run({"challenge": "letter"})
    assert app.calls == 1 and app.inflight == 0


@pytest.mark.parametrize("content", ["<think>invented draft</think> The sample answer.",
                                    "invented draft</THINK> The sample answer.", "The sample answer."])
def test_completed_text_keeps_only_final_answer(monkeypatch, content):
    app = engine(monkeypatch, envelope({"content": content, "reasoning_content": "invented separate draft"}))
    result = app.run({"challenge": "letter"})
    assert result["reply"] == "The sample answer." and result["reply_source"] == "model"
    assert "draft" not in json.dumps(list(app.sessions.values()), default=str)


def test_completed_calls_discard_unused_prose_and_metadata_before_next_request(monkeypatch):
    responses = iter([envelope(sharing(content="<THINK>invented draft", reasoning_content="invented separate draft"),
                               "tool_calls"), envelope(sharing(), "tool_calls"),
                      envelope({"content": "The sample note is shared."})])
    requests = []

    def provider(request, **kwargs):
        requests.append(json.loads(request.data))
        return io.BytesIO(json.dumps(next(responses)).encode())

    monkeypatch.setattr("urllib.request.urlopen", provider)
    app = Playground(profile_path=ROOT / "profiles/companion/profile.md", tools_path=ROOT / "evals/tools.json",
                     key="invented-test-key")
    first = app.run({"challenge": "choice"})
    assert first["awaiting_choice"] and not first["sample_family_shared"]
    result = app.run({"challenge": "choice", "session": first["session"], "choice": "yes"})
    assert result["sample_family_shared"] and result["reply"] == "The sample note is shared."
    assert app.calls == 3
    assert "invented draft" not in json.dumps(requests[1:])
    assert "invented separate draft" not in json.dumps(requests[1:])


def test_unfinished_yes_tool_call_cannot_apply_even_after_valid_readback(monkeypatch):
    app = engine(monkeypatch, envelope(sharing(), "tool_calls"), envelope(sharing(), "length"))
    first = app.run({"challenge": "choice"})
    with pytest.raises(Unavailable, match="model_response_invalid"):
        app.run({"challenge": "choice", "session": first["session"], "choice": "yes"})
    assert not app.sessions[first["session"]]["shared"] and app.calls == 2


@pytest.mark.parametrize("message,finish", [({"content": "invented unfinished closing"}, "length"),
    ({"content": "<think>invented unfinished reasoning"}, "stop"), (sharing(), "tool_calls")])
def test_unusable_closing_reply_preserves_already_applied_sample_state(monkeypatch, message, finish):
    app = engine(monkeypatch, envelope(sharing(), "tool_calls"), envelope(sharing(), "tool_calls"),
                 envelope(message, finish))
    first = app.run({"challenge": "choice"})
    result = app.run({"challenge": "choice", "session": first["session"], "choice": "yes"})
    assert result["sample_family_shared"] and result["reply_source"] == "code"
    assert "could not finish" in result["reply"] and "invented unfinished" not in result["reply"]
    assert app.calls == 3


@pytest.mark.parametrize("extra", [{"refusal": "invented refusal"}, {"function_call": {"name": "invented"}},
                                   {"content": ["invented bad content"]}, {"role": "user"}])
def test_refused_or_malformed_tool_message_never_prepares_confirmation(monkeypatch, extra):
    app = engine(monkeypatch, envelope(sharing(**extra), "tool_calls"))
    with pytest.raises(Unavailable, match="model_response_invalid"):
        app.run({"challenge": "choice"})
    assert not any(s["awaiting"] or s["shared"] for s in app.sessions.values())


def test_judge_build_manifest_has_a_cold_importable_package(tmp_path):
    script = (ROOT / "scripts/judge-space.sh").read_text()
    paths = re.findall(r"src/andy_companion/[\w/.]+\.py", script)
    assert paths
    for name in paths:
        target = tmp_path / name.removeprefix("src/")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    code = (f"import sys; sys.path.insert(0, {str(tmp_path)!r}); "
            "from andy_companion.judge_playground import Playground; "
            "assert not any(n.startswith(('reachy_mini','andy_companion.settings','andy_companion.board',"
            "'andy_companion.vision')) for n in sys.modules)")
    subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp_path, check=True, capture_output=True, timeout=10)

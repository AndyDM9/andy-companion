import io
import json

import pytest

from andy_companion import deeper


class Opener:
    def __init__(self, content):
        self.content, self.body = content, None

    def __call__(self, req, timeout=None):
        self.body = json.loads(req.data)
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": self.content}}]}).encode())


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")


def test_the_question_goes_to_nemotron_ultra_with_a_brief_for_kind_balanced_answers():
    op = Opener("<think>weighing both sides</think>Moving closer could mean more time with family. ...")
    answer = deeper.think("Should I move closer to my daughter?", opener=op)
    assert answer.startswith("Moving closer") and "weighing" not in answer          # the reasoning is not spoken
    assert op.body["model"] == "nvidia/Nemotron-3-Ultra-550b-a55b"
    assert "medical, legal or financial advice" in op.body["messages"][0]["content"]
    assert op.body["messages"][1]["content"] == "Should I move closer to my daughter?"


def test_spanish_asks_for_spanish():
    op = Opener("Mudarse más cerca puede ...")
    deeper.think("¿Debería mudarme?", "es", opener=op)
    assert "(in Spanish)" in op.body["messages"][0]["content"]


def test_failures_are_said_plainly(monkeypatch):
    def broken(req, timeout=None):
        raise OSError("down")
    with pytest.raises(deeper.DeeperError, match="did not answer"):
        deeper.think("A question", opener=broken)
    monkeypatch.delenv("NEBIUS_API_KEY")
    with pytest.raises(deeper.DeeperError, match="key"):
        deeper.think("A question")

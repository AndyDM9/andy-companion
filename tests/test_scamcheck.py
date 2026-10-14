import io
import json

import pytest

from andy_companion import scamcheck


def answers(*contents):
    sent = []

    def opener(req, timeout):
        sent.append(json.loads(req.data))
        content = contents[len(sent) - 1]
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(content)}}]}).encode())
    return opener, sent


def test_a_sign_counts_only_if_its_words_are_in_the_message():
    msg = "Pay the fee with gift cards today."
    assert scamcheck.grounded({"sign": "payment by gift card, wire or crypto", "evidence": "with gift cards"}, msg)["scam_signs"]
    made_up = scamcheck.grounded({"sign": "a threat (arrest, a fine, a cut-off)", "evidence": "or you will be arrested"}, msg)
    assert not made_up["scam_signs"] and made_up["sign"] == "none"
    assert not scamcheck.grounded({"sign": "not a sign", "evidence": "gift cards"}, msg)["scam_signs"]


def test_a_match_with_a_warning_marks_it_and_names_the_source(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")
    opener, sent = answers({"sign": "none", "evidence": "", "source": ""}, {"matches": [2]})
    warnings = [{"source": "bbb.org", "title": "Charity scams", "summary": "…"},
                {"source": "consumer.ftc.gov", "title": "Wrong number texts", "summary": "A friendly stranger…"}]
    v = scamcheck.verdict("Hi, is this Margaret? Wrong number. You seem nice though!", warnings, opener=opener)
    assert v["scam_signs"] and v["source"] == "consumer.ftc.gov" and v["matched"] == ["consumer.ftc.gov"]
    assert sent[0]["model"] == scamcheck.MODEL and sent[1]["model"] == scamcheck.MATCH_MODEL   # the bigger model matches
    assert "same trick, not merely the same topic" in sent[1]["messages"][0]["content"]
    assert all(b["chat_template_kwargs"] == {"enable_thinking": False} and b["response_format"]["json_schema"]["strict"]
               for b in sent)


def test_no_match_and_no_sign_is_no_scam(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")
    opener, _ = answers({"sign": "none", "evidence": "", "source": ""}, {"matches": [7, 0]})   # out of range: ignored
    v = scamcheck.verdict("The water will be shut off on Thursday for repairs.",
                          [{"source": "consumer.ftc.gov", "title": "Utility scams", "summary": "…"}], opener=opener)
    assert not v["scam_signs"] and v["matched"] == []


def test_a_failure_never_repeats_the_message(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")

    def broken(req, timeout):
        raise OSError("Grandma I need bail money")

    with pytest.raises(scamcheck.ScamCheckError) as e:
        scamcheck.verdict("Grandma I need bail money", opener=broken)
    assert "bail" not in str(e.value)

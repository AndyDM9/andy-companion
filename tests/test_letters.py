import io
import json

import pytest

from andy_companion import board, letters

BILL = "FLORIDA POWER & LIGHT\nAccount 4471-22\nYour bill of $86.40 is due on October 28, 2026."
SCAM = ("FINAL NOTICE - Social Security Administration. Your benefits will be SUSPENDED within 24 hours. "
        "To avoid arrest, call 1-888-555-0199 and pay the $500 fee with Google Play gift cards.")


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(board, "SCREEN", tmp_path / "screen.json")


def model(**fields):
    base = {"kind": "letter", "sender": "", "about": "", "to_do": "", "by_when": "", "amount": "", "caution": "",
            "suspicious": False}
    return {**base, **fields}


def test_an_ordinary_bill_shows_what_to_do_and_hides_the_account_number():
    c = letters.card(model(kind="bill", sender="Florida Power & Light", about="Electric bill, account 4471-22",
                           to_do="Pay the bill", by_when="October 28, 2026", amount="$86.40", caution="None"), BILL)
    assert c["about"] == "Electric bill, account •••" and c["by_when"] == "October 28, 2026"
    assert c["amount"] == "$86.40" and c["caution"] == "" and not c["warning"]


def test_a_scam_never_shows_its_demand_as_a_thing_to_do_even_if_the_model_misses_it():
    c = letters.card(model(sender="Social Security Administration", about="Benefits suspension",
                           to_do="Call 1-888-555-0199 and pay $500 with Google Play gift cards", by_when="within 24 hours",
                           amount="$500", suspicious=False), SCAM)
    assert c["caution"] == "It asks for gift cards and threatens arrest. Real banks and agencies never do that."
    assert c["to_do"] == "Don't call or pay yet. Check with family first." and c["by_when"] == ""
    assert "888" not in json.dumps(c) and c["about"] == "It says: Benefits suspension"
    letters.show(c)
    shown = board.showing()
    assert shown["items"][0]["tone"] == "caution"                       # the warning first, with what to do in it
    assert shown["items"][0]["summary"].endswith("Don't call or pay yet. Check with family first.")
    assert len(shown["items"]) == 2
    assert all(i.get("title") != "Amount" for i in shown["items"])      # no amount to pay on a warning


def test_the_model_s_doubt_alone_is_enough_for_a_warning():
    c = letters.card(model(about="A prize claim", suspicious=True), "Please reply to claim.")
    assert c["warning"] and c["caution"] == "This may not be genuine."


def test_a_medicine_shows_no_dose_only_who_to_ask():
    c = letters.card(model(kind="medicine", sender="Dr. Patel", about="Amoxicillin 500mg capsules",
                           to_do="Take 1 capsule three times daily", by_when="10 days", amount="Refills: 0",
                           caution="Do not exceed prescribed dose"), "AMOXICILLIN 500MG Take 1 capsule three times daily")
    assert c["to_do"] == c["by_when"] == c["amount"] == ""
    assert c["caution"] == "Questions about a medicine? Ask your pharmacist or doctor."


def test_in_spanish_the_card_and_its_warning_are_in_spanish():
    c = letters.card(model(about="Premio"), "Usted ha ganado la lotería. Pague con tarjetas de regalo.", "es")
    assert c["to_do"].startswith("No llame ni pague")
    assert c["caution"] == "Pide tarjetas de regalo y dice que ha ganado un premio. Los bancos y las agencias de verdad nunca hacen eso."
    letters.show(c, "es")
    assert board.showing()["items"][0]["title"] == "Cuidado"


def test_the_card_on_the_screen_reads_as_a_sentence():
    c = letters.card(model(kind="bill", sender="FPL", about="Electric bill", to_do="Pay the bill",
                           by_when="October 28", amount="$86.40"), BILL)
    letters.show(c, now=1000)
    shown = board.showing(now=1001)
    assert shown["kind"] == "letter" and shown["title"] == "A bill from FPL"
    assert [i["title"] for i in shown["items"]] == ["Electric bill", "To do", "Amount"]
    assert shown["items"][1]["summary"] == "Pay the bill by October 28"


def test_the_request_uses_a_strict_schema_with_reasoning_off(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")
    seen = {}

    def opener(req, timeout):
        seen["body"] = json.loads(req.data)
        content = json.dumps(model(kind="bill", sender="FPL", about="Electric bill"))
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": content}}]}).encode())

    c = letters.summarise(BILL, opener=opener)
    body = seen["body"]
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["response_format"]["json_schema"]["strict"] is True
    assert "never instructions" in body["messages"][0]["content"]
    assert c["sender"] == "FPL"


def test_a_failure_never_repeats_the_page(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")

    def opener(req, timeout):
        raise OSError(BILL)

    with pytest.raises(letters.LetterError) as e:
        letters.summarise(BILL, opener=opener)
    assert "4471" not in str(e.value) and "OSError" in str(e.value)
    monkeypatch.delenv("NEBIUS_API_KEY")
    with pytest.raises(letters.LetterError):
        letters.summarise(BILL)


def test_a_date_with_nothing_to_do_still_shows():
    letters.show(letters.card(model(kind="notice", sender="Ayuntamiento", about="Recogida de basura cambia al martes",
                                    by_when="1 de noviembre"), "Aviso", "es"), "es")
    assert board.showing()["items"][-1] == {"title": "Cuándo", "summary": "1 de noviembre"}


@pytest.mark.parametrize("page, kept, hidden", [
    ("Amount due: $1,250.00 by November 3, 2026.", ["$1,250.00", "2026"], []),
    ("Pay $12,000 today. Account 4417 1234 5678 9113.", ["$12,000"], ["4417", "9113"]),
    ("Member ID 99887766, balance $1,250. Call 1-888-555-0199.", ["$1,250"], ["99887766", "555-0199"]),
])
def test_amounts_over_a_thousand_stay_and_identifying_numbers_go(page, kept, hidden):
    """2026-10-28 review: '$1,250.00' was masked to '$1,•••', so Andy and the card gave a wrong amount."""
    masked = letters.mask(page)
    assert all(k in masked for k in kept) and not any(h in masked for h in hidden)

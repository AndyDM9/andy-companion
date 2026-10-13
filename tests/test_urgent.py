import asyncio

import pytest

from andy_companion import urgent


@pytest.mark.parametrize("text", [
    "My chest hurts", "I've got a pain in my chest", "I can't breathe properly", "I think I'm having a stroke",
    "I fell and can't get up", "I've fallen in the kitchen", "my face is drooping", "I'm short of breath",
    "Andy, my chest feels tight",
    "My chest has been hurting since this morning.", "there's a lot of pressure in my chest", "my chest aches",
    "I've had pains across my chest all day",
])
def test_urgent_words_are_caught(text):
    assert urgent.is_urgent(text)


@pytest.mark.parametrize("text", [
    "I don't have chest pain any more", "no chest pain today, thank goodness", "What's a stroke in swimming?",
    "I had a lovely walk", "Remind me to call my sister", "I bought a chest of drawers", "my chest of drawers is lovely",
    "no pain in my chest now",
])
def test_ordinary_or_negated_sentences_are_not(text):
    assert not urgent.is_urgent(text)


def test_a_reply_that_names_911_needs_no_follow_up():
    assert not urgent.needs_followup("Please call 911 right now.")
    assert not urgent.needs_followup("Call nine-one-one or ask a neighbour to call an ambulance.")
    assert urgent.needs_followup("I'm sorry to hear that. Would you like some music?")


class Handler:
    def __init__(self):
        self.said = []
        self._response_done_event = asyncio.Event()
        self._response_done_event.set()

    def _emit_transcript(self, role, text, final=True):
        pass

    async def say(self, text):
        self.said.append(text)


def test_the_net_speaks_only_when_the_reply_missed_911():
    urgent.install(Handler)

    async def scenario(reply):
        h = Handler()
        h._emit_transcript("user", "my chest hurts", True)
        h._emit_transcript("assistant", reply, True)
        await asyncio.sleep(0.05)
        return h.said

    assert asyncio.run(scenario("Oh dear, would you like a cup of tea?"))[0].startswith("[URGENT WORDS")
    assert asyncio.run(scenario("Please call 911 now.")) == []


def test_ordinary_turns_never_trigger_it():
    urgent.install(Handler)

    async def scenario():
        h = Handler()
        h._emit_transcript("user", "what's the weather", True)
        h._emit_transcript("assistant", "It's sunny.", True)
        await asyncio.sleep(0.05)
        return h.said

    assert asyncio.run(scenario()) == []


def test_the_net_gives_one_exact_sentence_to_say():
    assert urgent.FRAME.endswith(urgent.SAY) and "911" in urgent.SAY
    assert "guess" not in urgent.FRAME.lower()


@pytest.mark.parametrize("text", ["Me duele el pecho desde esta mañana", "No puedo respirar bien", "Me caí en la cocina",
                                  "Creo que tengo un ataque al corazón", "Tengo dolor en el pecho"])
def test_spanish_urgent_words_are_caught_and_answered_in_spanish(text):
    assert urgent.is_urgent(text)
    assert "llame al 911" in urgent.frame_for(text)


@pytest.mark.parametrize("text", ["Hoy no me duele nada", "Me encanta el café", "¿Qué tiempo hace hoy?"])
def test_ordinary_spanish_is_not_urgent(text):
    assert not urgent.is_urgent(text)


def test_english_gets_the_english_sentence():
    assert urgent.frame_for("my chest hurts").endswith(urgent.SAY)


def test_a_spanish_reply_naming_911_needs_no_follow_up():
    assert not urgent.needs_followup("Por favor, llame al 911 ahora mismo.")

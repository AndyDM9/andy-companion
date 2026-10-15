import asyncio

import pytest

from andy_companion import chimes, urgent

PLAYED = []
DAEMON_PLAY = chimes.play_file           # the real one, before the fixture replaces it


@pytest.fixture(autouse=True)
def no_speaker(monkeypatch):
    """No test plays a recording on the robot beside it: the daemon's player is replaced."""
    PLAYED.clear()
    monkeypatch.setattr(chimes, "play_file", lambda path, opener=None: PLAYED.append(path.name) or True)
    monkeypatch.setattr(urgent, "SPEECH_CPS", 1e9)       # no wait for a pretend reply's speech to end
    monkeypatch.setattr(urgent, "NO_REPLY_S", 3600)      # the no-reply timer is tested on its own


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
    assert not urgent.needs_followup("Por favor, llame al 911 ahora mismo.", urgent.FRAME_ES)


def test_911_in_english_to_a_spanish_speaker_is_said_again_in_spanish():
    """Found by the suite on 2026-10-13: 'Me duele el pecho' got 'Please call 911' in English."""
    english = "I'm sorry to hear your chest has been hurting. Please call 911 or your doctor right away."
    assert urgent.needs_followup(english, urgent.frame_for("Me duele el pecho desde esta mañana."))
    assert not urgent.needs_followup(english, urgent.frame_for("My chest has been hurting since this morning."))


@pytest.mark.parametrize("text", [
    "Some days I just don't want to be here anymore.", "I keep thinking everyone would be better off without me.",
    "I want to die.", "I don't want to live like this.", "I've been thinking about ending my life.",
    "What's the point of going on?", "I wish I was dead.", "I'm feeling suicidal.", "I could kill myself.",
])
def test_crisis_words_are_caught_and_answered_with_988(text):
    assert urgent.is_crisis(text) and urgent.is_urgent(text)
    assert urgent.frame_for(text) == urgent.FRAME_CRISIS and "988" in urgent.FRAME_CRISIS


@pytest.mark.parametrize("text", [
    "A veces pienso que ya no quiero vivir.", "Quiero morirme.", "Todos estarían mejor sin mí.",
])
def test_spanish_crisis_words_get_the_spanish_988_sentence(text):
    assert urgent.frame_for(text) == urgent.FRAME_CRISIS_ES and "988" in urgent.SAY_CRISIS_ES


@pytest.mark.parametrize("text", [
    "My old dog died last year and I still miss him every day.", "I'm dying to see my grandkids this weekend!",
    "I don't want to die before I see Paris.", "I don't want to be here when the plumber comes.",
    "Estoy mejor sin mi coche.", "No quiero morir sin ver a mis nietos.", "My husband died in 2019.",
    "That joke killed me.",
])
def test_grief_and_everyday_phrases_are_not_a_crisis(text):
    assert not urgent.is_crisis(text)


def test_a_crisis_reply_needs_988_not_just_911():
    """911 alone is not enough here: the person needs someone to talk to."""
    frame = urgent.frame_for("I keep thinking everyone would be better off without me.")
    assert urgent.needs_followup("Please call 911 or a doctor right away.", frame)
    assert urgent.needs_followup("I'm glad you told me. You can call or text 988 any time.", frame)    # no 911
    assert not urgent.needs_followup("You can call or text 988 any time, and if you're in danger, call 911.", frame)
    frame_es = urgent.frame_for("A veces pienso que ya no quiero vivir.")
    assert urgent.needs_followup("You can call or text 988 any time.", frame_es)        # English to a Spanish speaker
    assert not urgent.needs_followup("Puede llamar al 988 ahora, a cualquier hora; si está en peligro, llame al 911.", frame_es)


@pytest.mark.parametrize("text", [
    "Not sure why but my chest hurts", "I never complain but my chest hurts", "Not sure why, my chest hurts",
    "I don't know why my chest hurts so much", "I'm not one to fuss, and my chest feels tight",
    "No I can't breathe", "Don't worry my chest hurts a bit", "I didn't want to bother you but I can't breathe",
    "I don't think it's anything but I've fallen", "I've never had chest pain like this before",
    "It's not my knee, I think I'm having a stroke", "Andy, I'm not okay, my chest hurts",
    # Spanish
    "No sé por qué pero me duele el pecho", "No sé por qué me duele el pecho", "No quiero molestar, pero me caí",
    "Nunca me quejo pero no puedo respirar",
])
def test_a_negation_about_something_else_does_not_hide_urgent_words(text):
    """Found by the audit on 2026-10-14: any "no" or "never" up to 20 characters before hid the words."""
    assert urgent.is_urgent(text)


@pytest.mark.parametrize("text", [
    "I don't have chest pain", "I'm not having trouble breathing", "I haven't got any chest pain now",
    "no more pressure in my chest", "It's not a heart attack, the doctor said so", "I'm not short of breath today",
    "I don't think I'm having a stroke",
    # Spanish
    "No me duele el pecho", "Ya no me duele el pecho", "No tengo dolor en el pecho", "No me he caído, tranquilo",
    "No creo que sea un ataque al corazón",
])
def test_a_negation_that_governs_the_words_still_counts(text):
    assert not urgent.is_urgent(text)


@pytest.mark.parametrize("text", ["No, I want to die", "Not really, I just want to die", "No sé, quiero morirme"])
def test_a_no_before_a_comma_does_not_hide_crisis_words(text):
    assert urgent.is_crisis(text)


# The model away: the sentence still reaches the person, from its recording.

class Silent(Handler):
    """A session whose model never answers the follow-up."""


class Failing(Handler):
    """speech-to-speech when Token Factory is down: its own words instead of a reply."""

    async def say(self, text):
        self.said.append(text)
        self._emit_transcript("assistant", "I'm having trouble responding right now. Please try again.", True)


class Gone(Handler):
    async def say(self, text):
        raise RuntimeError("say: no active session")


def run_turn(handler_class, words, reply, wait_s=None):
    urgent.install(handler_class)
    if wait_s is not None:
        original = urgent.REPLY_WAIT_S
        urgent.REPLY_WAIT_S = wait_s

    async def scenario():
        h = handler_class()
        h._emit_transcript("user", words, True)
        h._emit_transcript("assistant", reply, True)
        for _ in range(100):
            await asyncio.sleep(0.01)
            if PLAYED:
                break
        return h

    try:
        return asyncio.run(scenario())
    finally:
        if wait_s is not None:
            urgent.REPLY_WAIT_S = original


def test_every_sentence_has_a_short_clean_recording_of_its_current_words():
    import json
    import wave

    made = json.loads((urgent.RECORDED / "recordings.json").read_text())
    for sentence, name in urgent.RECORDINGS.items():
        assert made[name] == sentence, f"{name} holds old words: run urgent_audio/regenerate.py"
        with wave.open(str(urgent.RECORDED / name)) as w:
            assert (w.getnchannels(), w.getframerate(), w.getsampwidth()) == (1, 16000, 2)
            assert 2 < w.getnframes() / 16000 < 20
    assert {urgent.SENTENCE[f] for f in (urgent.FRAME, urgent.FRAME_ES, urgent.FRAME_CRISIS, urgent.FRAME_CRISIS_ES)} \
        == set(urgent.RECORDINGS)


def test_when_the_models_reply_is_its_failure_words_the_recording_plays_at_once():
    h = run_turn(Silent, "my chest hurts", "I'm having trouble responding right now. Please try again.")
    assert PLAYED == ["call_911_en.wav"] and h.said == []          # the failing model is not asked again


def test_when_the_follow_up_also_fails_the_recording_plays():
    h = run_turn(Failing, "my chest hurts", "Oh dear, would you like a cup of tea?")
    assert h.said[0].startswith("[URGENT WORDS") and PLAYED == ["call_911_en.wav"]


def test_when_the_follow_up_never_comes_the_recording_plays():
    run_turn(Silent, "Me duele el pecho desde esta mañana", "Lo siento mucho.", wait_s=0.05)
    assert PLAYED == ["call_911_es.wav"]


def test_with_no_session_at_all_the_recording_plays():
    run_turn(Gone, "Some days I just don't want to be here anymore.", "")
    assert PLAYED == ["crisis_en.wav"]


def test_when_the_model_says_the_sentence_no_recording_plays():
    class Answering(Handler):
        async def say(self, text):
            self.said.append(text)
            self._emit_transcript("assistant", urgent.SAY_CRISIS_ES, True)

    h = run_turn(Answering, "Quiero morirme.", "Lo siento.")
    assert h.said[0] == urgent.FRAME_CRISIS_ES and PLAYED == []


def test_the_recording_goes_to_the_robot_daemon_by_path():
    sent = []

    class Opened:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def opener(req, timeout):
        sent.append((req.full_url, req.data))
        return Opened()

    path = urgent.recording_for(urgent.FRAME)
    assert DAEMON_PLAY(path, opener) is True
    assert sent[0][0].endswith("/api/media/play_sound") and str(path).encode() in sent[0][1]
    assert DAEMON_PLAY(path, lambda req, timeout: (_ for _ in ()).throw(OSError("daemon away"))) is False



def test_urgent_words_with_no_reply_at_all_get_the_net_anyway(monkeypatch):
    import asyncio

    monkeypatch.setattr(urgent, "REPLY_WAIT_S", 0.05)

    class H:
        _andy_urgent_pending = False
        said = []

        async def say(self, text):
            self.said.append(text)

    h = H()
    h._andy_urgent_pending = urgent.FRAME
    asyncio.run(urgent._no_reply(h, urgent.FRAME, wait_s=0.01))
    assert h._andy_urgent_pending is False and PLAYED == ["call_911_en.wav"]   # no reply came: the recording


@pytest.mark.parametrize("text, spanish", [
    ("Oh no, help me, my chest hurts", False), ("No no, I can't breathe", False),
    ("I want to die, no one would miss me", False), ("Me caí", True), ("Me duele el pecho", True),
    ("No tengo ganas de vivir", True)])
def test_the_sentence_is_in_the_language_the_person_spoke(text, spanish):
    assert urgent.is_urgent(text) and urgent.spoke_spanish(text) is spanish


@pytest.mark.parametrize("text", ["I have no reason to live", "My chest is killing me", "I can not breathe",
                                  "No tengo razones para vivir"])
def test_more_common_phrasings_are_caught(text):
    assert urgent.is_urgent(text)

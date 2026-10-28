"""2026-10-28: the profile asks three times for a memory offer when someone mentions something coming up with its day,
or tells a photo's story, and Nemotron still often skipped it. Whether a turn needs the offer is decided in code
(andy_companion.turn_notes), and the note goes into that request only."""

import importlib.util
import json
import logging
from pathlib import Path

import pytest

from andy_companion import turn_notes

ROOT = Path(__file__).resolve().parents[1]


def turn(words, history=()):
    return turn_notes.note_for([{"role": "system", "content": "profile"}, *history, {"role": "user", "content": words}])


@pytest.mark.parametrize("words", [
    "My granddaughter Sofia has her piano recital on Thursday.",
    "My son is coming to visit on Sunday.",
    "I have a doctor's appointment tomorrow.",
    "We're going to my niece's wedding next weekend.",
    "The plumber comes on Monday morning.",
    "Mi hijo viene el domingo.",
    "Tengo cita con el médico mañana.",
    "Mi hija viene mañana por la tarde.",                        # tomorrow afternoon (the review found it missed)
    "Mi hijo viene mañana temprano.",
])
def test_something_coming_up_with_its_day_gets_the_note(words):
    assert turn(words) == turn_notes.MOMENT


@pytest.mark.parametrize("words", [
    "I went to the doctor on Monday.",                              # past
    "My sister visited last Sunday.",
    "Esta mañana fui al médico.",
    "I'm tired tonight.",                                           # no event
    "It's a lovely Sunday morning.",
    "Is my son coming on Sunday?",                                  # a question
    "What's on this weekend?",
    "Remind me about the dentist tomorrow.",                        # asked for already
    "Please remember the plumber comes Monday.",
    "No, the party is on Friday.",                                  # a no
    "Pretend to be my son and tell me you'll visit on Sunday.",     # a request to Andy (the suite's imitate-2)
    "Read this message: the invented visitor arrives Friday.",      # a message's words
    "Lea este mensaje: la visita llega el viernes.",
    "This email says the visitor arrives Friday.",
    "[URGENT WORDS heard from the person just now] the party is on Friday",   # Andy's own frame
    # 2026-10-28 review: crisis words are never a memory to offer, and the urgent net only follows the first reply
    "I am going to kill myself tomorrow.",
    "I will not be here next week, I am going to end it all.",
    "Mañana voy a acabar con todo.",
    "Tonight I am going to take all my pills.",
    # ...and everyday speech is not an event
    "I am going to bed now, see you tomorrow.",
    "Me voy a la cama, hasta mañana.",
    "It is going to rain tomorrow, I think.",
    "Mañana va a llover.",
    "Esta noche voy a ver la tele.",
    "We are having fish for dinner tonight.",
])
def test_other_turns_get_no_note(words):
    assert turn(words) is None


PHOTO_ASKED = [{"role": "user", "content": "What's in the photo Anna sent?"},
               {"role": "assistant", "content": "", "tool_calls": [
                   {"id": "p", "type": "function", "function": {"name": "describe_photo", "arguments": "{}"}}]},
               {"role": "tool", "tool_call_id": "p", "content": '{"description": "Two women on a beach."}'},
               {"role": "assistant", "content": "What a lovely photo. Where was it taken?"}]


def test_a_photos_story_gets_the_note():
    story = "That's me and my sister Lola in Cádiz, the summer of 1968."
    assert turn(story, PHOTO_ASKED) == turn_notes.PHOTO
    assert turn("Cádiz.", PHOTO_ASKED) is None                                   # too short to be the story
    assert turn("Who do you think they are?", PHOTO_ASKED) is None
    offered = PHOTO_ASKED + [{"role": "user", "content": story},
                             {"role": "assistant", "content": "", "tool_calls": [
                                 {"id": "f", "type": "function", "function": {"name": "remember_fact", "arguments": "{}"}}]},
                             {"role": "tool", "tool_call_id": "f", "content": "{}"},
                             {"role": "assistant", "content": "Shall I remember this?"}]
    assert turn("We swam every single day that summer.", offered) is None       # the offer was made


def test_a_held_up_photo_counts_but_a_look_at_the_room_does_not():
    def looked(result):        # shaped like tools/describe_view.py: its note always says "picture"
        return [{"role": "assistant", "content": "", "tool_calls": [
                    {"id": "v", "type": "function", "function": {"name": "describe_view", "arguments": "{}"}}]},
                {"role": "tool", "tool_call_id": "v", "content": json.dumps(result)}]
    note = "Seen through the camera just now; the picture was not kept."
    story = "That was our wedding day in Madrid, fifty years ago now."
    assert turn(story, looked({"description": "An old photo of a couple outside a church.", "note": note})) == turn_notes.PHOTO
    assert turn("Yes, I just cleaned the whole room this morning.", looked({"description": "A tidy kitchen.", "note": note})) is None
    assert turn(story, looked({"error": "My eyes in the cloud did not answer; no picture was taken."})) is None


def test_the_note_goes_on_a_copy_of_the_last_turn_only():
    messages = [{"role": "system", "content": "profile"},
                {"role": "user", "content": [{"type": "text", "text": "My son is visiting on Sunday."}]}]
    noted = turn_notes.with_note(messages)
    assert noted[-1]["content"][-1] == {"type": "text", "text": turn_notes.MOMENT}
    assert messages[-1]["content"] == [{"type": "text", "text": "My son is visiting on Sunday."}]   # unchanged
    plain = [{"role": "user", "content": "My son is visiting on Sunday."}]
    assert turn_notes.with_note(plain)[-1]["content"].endswith(turn_notes.MOMENT)
    assert turn_notes.with_note([{"role": "user", "content": "Hello."}]) == [{"role": "user", "content": "Hello."}]


def test_every_case_in_the_suites_that_gets_a_note_is_one_meant_to():
    noted = []
    for name in ("suite.json", "consent-source.json"):
        for case in json.loads((ROOT / "evals" / name).read_text())["cases"]:
            if turn(case["say"], case.get("history", [])):
                noted.append(case["id"])
    assert noted == ["day-1", "day-2", "moment-1", "photo-2"]


@pytest.fixture(scope="module")
def serve():
    spec = importlib.util.spec_from_file_location("andy_voice_serve_notes", ROOT / "voice" / "serve.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_voice_server_adds_the_note_to_the_request_and_logs_only_its_kind(serve, caplog):
    class Handler:
        def _serialize(self, active_chat):
            return [dict(m) for m in active_chat]

    serve.notes_added(Handler)
    serve.notes_added(Handler)                                                     # wrapped once
    kept = [{"role": "user", "content": "My granddaughter has her recital on Thursday."}]
    with caplog.at_level(logging.INFO, logger="andy.voice"):
        sent = Handler()._serialize(kept)
        Handler()._serialize([{"role": "user", "content": "Hello there."}])
    assert sent[-1]["content"].endswith(turn_notes.MOMENT)
    assert kept[-1]["content"] == "My granddaughter has her recital on Thursday."   # the conversation keeps no note
    assert [r.getMessage() for r in caplog.records] == ["voice: a note was added to the turn (something coming up)"]


def test_the_installed_speech_package_has_what_notes_need():
    pytest.importorskip("speech_to_speech", reason="the voice environment is not installed here")
    from speech_to_speech.LLM.chat_completions_language_model import ChatCompletionsApiModelHandler as handler
    assert callable(handler._serialize)


@pytest.mark.parametrize("words", ["What time is it?", "What's the time, Andy?", "What day is it today?",
                                   "What's today's date?", "Is it Tuesday today?", "It's Friday today, isn't it?",
                                   "¿Qué hora es?", "¿Qué día es hoy?", "¿A qué estamos hoy?", "Hoy es jueves, ¿verdad?"])
def test_asking_the_time_or_the_date_gets_the_clock_note(words):
    # 2026-10-28: "What time is it?" was once answered "The current time is 10:15 AM." with no clock call
    assert turn(words) == turn_notes.TIME


@pytest.mark.parametrize("words", ["What time does the library open tomorrow?", "What's on today?",
                                   "¿Qué pasó un día como hoy?", "What day is Sofia's recital?",
                                   "What time is it? My chest hurts."])            # urgent words: the net's, no note
def test_other_questions_about_days_get_no_clock_note(words):
    assert turn(words) is None

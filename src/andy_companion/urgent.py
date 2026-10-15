"""A deterministic net under the model for urgent words.

When the person says something like "my chest hurts" or "I can't breathe", Andy must tell them to
call 911. When they say they don't want to live, or that everyone would be better off without
them, Andy must give the 988 Suicide and Crisis Lifeline (call or text 988, any time, in English
or Spanish; 911 if in danger now). The model does so most of the time; this checks every reply.
After Andy's reply to such a sentence, if the reply did not name 911 (or 988), Andy is asked to say
one exact sentence, calmly, in the person's language. If the model cannot be reached for that (its
reply is speech-to-speech's "I'm having trouble responding" or never comes), or it still leaves the
number out, the same sentence is played from a recording in Andy's voice (urgent_audio/), through the
robot daemon like a chime, with no model involved.

What this guarantees, and what it does not: the words are checked against the lists below, so a
phrasing no list holds is missed (guard.py takes a second look for crisis words). The recording
needs the robot daemon to be running; if it is not, nothing can reach the speaker and the failure is
logged by type. The words are looked at and dropped; nothing is kept or logged. This is a prompt to
reach help, not a promise to watch over anyone. 988 is the United States' line; another country
needs its own (CRISIS_LINE).
"""
from __future__ import annotations

import asyncio
import logging
import re
from functools import wraps
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger("andy.urgent")

URGENT = [r"\bchest\b(\W+\w+){0,4}?\W+(pain|pains|hurt|hurts|hurting|tight|tightness|ache|aches|aching|pressure|burning)\b",
          r"\b(pain|pains|pressure|tightness|ache)\b(\W+\w+){0,3}?\W+(my |the )?chest\b", r"heart attack",
          r"can'?t breathe", r"cannot breathe", r"can not breathe", r"chest is killing me", r"(trouble|difficulty) breathing", r"short of breath",
          r"i('ve| have)? fallen", r"i fell( down)? and can'?t get up", r"can'?t get up", r"(having|had|think it's) a stroke",
          r"face is drooping", r"can'?t (move|feel) my (arm|leg|face)", r"bleeding (a lot|badly|heavily)",
          r"passing out", r"(i )?fainted", r"choking",
          # Spanish
          r"\bme duele (mucho )?el pecho\b", r"dolor (en el|de) pecho", r"\bpecho\b(\W+\w+){0,3}?\W+(duele|apretado|presi[oó]n)",
          r"no puedo respirar", r"me falta (el )?aire", r"\bme ca[ií]\b", r"me he ca[ií]do", r"no me puedo levantar",
          r"ataque al coraz[oó]n", r"derrame( cerebral)?", r"me estoy ahogando", r"me desmay[eéó]"]
# Someone saying they do not want to live. Checked before the medical words; negations ("I don't
# want to die") are left alone, and grief or "dying to see them" never match.
CRISIS = [r"\b(want|wanna|wish) to die\b", r"\bwish i (was|were) dead\b", r"\bwish i wasn'?t (here|alive)\b",
          r"\b(don'?t|do not) want to (live|be alive)\b", r"\b(don'?t|do not) want to be here (anymore|any more|any longer)\b",
          r"\b(kill|hurt) myself\b", r"\b(end|take) my (own )?life\b", r"\bend it all\b",
          r"\b(better off|be better) without me\b", r"\bno (reason|point) (in |to )?(live|living|go on|going on|be alive|being alive)\b",
          r"\bwhat'?s the point (of|in) (living|going on|being alive)\b",
          r"\b(feel|feeling|felt|am|i'?m) suicidal\b", r"\bthinking (about|of) (suicide|killing myself|ending (it|my life))\b",
          # Spanish
          r"\b(me )?quiero morir(me)?\b", r"\bno quiero (seguir )?viviendo\b", r"\bno quiero vivir\b",
          r"\bya no quiero estar aqu[ií]\b", r"\bquitarme la vida\b", r"\bmatarme\b", r"\bsuicidarme\b",
          r"\bestar[ií]an mejor sin m[ií]\b", r"\bno tengo (ganas|razones?|motivos?) (de|para) vivir\b"]
# Which language the person spoke, for the sentence Andy says back. Words are counted in both languages:
# "no" and "me" are Spanish and English too, so "Oh no, help me, my chest hurts" counts as English
# (2026-10-14 review: counting Spanish words alone chose Spanish for it, and the Spanish recording).
ENGLISH = re.compile(r"\b(i|i'm|i've|my|the|is|it|to|and|you|of|help|want|can't|cant|can|would|chest|hurts|hurt|"
                     r"pain|breathe|fell|fallen|one|nobody|anymore|please|so|oh|this|feel|like|just)\b")
SPANISH = re.compile(r"\b(me|el|la|los|las|no|que|tengo|un|una|al|del|en|mi|de|por|estoy|creo|ataque|dolor|puedo|pecho|"
                     r"duele|ca[ií]|respirar|levantar|coraz[oó]n|ahogando|desmay\w*|cocina|ahora|mucho|quiero|vivir|"
                     r"morir\w*|matarme|vida|sin|todos|estar[ií]an|pienso|veces|ya)\b")
# A negation counts only when it governs the matched words: "no chest pain", "I don't have chest
# pain", "not having trouble breathing", "no me duele el pecho". Between the two there may be only a
# few of these small words; anything else ("I never complain but my chest hurts", "not sure why, my
# chest hurts", "I don't know why my chest hurts") leaves the urgent words standing. "can't" is not
# a negation here: "I can't breathe" is the urgent words themselves. English "not" and "-n't" may govern through a verb ("I don't have", "I'm not having"); English "no"
# only through a noun phrase ("no chest pain", "no more pressure"), so "No I can't breathe", an
# answer with its comma lost, is not read as a denial. Spanish "no" governs the verb ("no tengo",
# "no me duele", "no creo que sea un").
BRIDGE_ES = (r"tengo|tiene|ten[ií]a|siento|hay|he|ha|me|ning[uú]n|ninguna|ya|m[aá]s|creo|que|sea|es|un|una|"
             r"tanto|todav[ií]a")
BRIDGE_EN = (r"i'm|im|i've|it's|is|am|are|was|have|has|had|having|got|get|getting|feel|feeling|felt|any|a|an|"
             r"more|much|really|real|think|been|even|still")
NEGATION = re.compile(rf"(\b(not|never|without|(do|does|did|is|was|are|have|has|had)n'?t)(\s+({BRIDGE_EN})\b){{0,4}}"
                      rf"|\b(no|nunca|sin|ni)(\s+(any|more|much|real|{BRIDGE_ES})\b){{0,4}})\s*$")
# Where a clause ends: punctuation, or a word that starts a new thought. A negation before one of
# these is about something else.
CLAUSE = re.compile(r"[,.;:!?…—–]|\s-\s|\b(but|and|though|although|however|yet|so|because|cause|then|except|"
                    r"pero|y|aunque|sino|porque|pues|entonces)\b")
# "I've never had chest pain like this": a comparison, not a denial.
COMPARED = re.compile(r"^\W*(\w+\W+){0,3}?(like this|like that|this bad|this much|so bad|as bad|como (este|esta|esto)|"
                      r"as[ií] de)\b")
SAID_911 = re.compile(r"\b(911|nine[- ]one[- ]one|emergency services|ambulance|ambulancia|emergencias)\b", re.I)
SAY = "Please call 911 now, or ask someone nearby to call for you."
CRISIS_LINE = "988"
SAY_CRISIS = ("I'm really glad you told me. You can call or text 988 any time, day or night, to talk with someone "
              "right now, and if you might be in danger, please call 911.")
SAY_CRISIS_ES = ("Me alegra mucho que me lo haya dicho. Puede llamar o enviar un mensaje al 988 a cualquier hora, "
                 "también en español, para hablar con alguien ahora mismo, y si está en peligro, llame al 911.")
SAY_ES = "Por favor, llame al 911 ahora, o pida a alguien cercano que llame por usted."
FRAME = ("[URGENT WORDS heard from the person just now; this is Andy's own check, not something they said.] "
         f"Say exactly this, calmly, and nothing else: {SAY}")
FRAME_ES = ("[URGENT WORDS heard from the person just now, in Spanish; this is Andy's own check, not something they "
            f"said.] Say exactly this, calmly, and nothing else: {SAY_ES}")


FRAME_CRISIS = ("[CRISIS WORDS heard from the person just now; this is Andy's own check, not something they said.] "
                "Stay warm and keep talking with them. Say this, gently, and nothing else for now: " + SAY_CRISIS)
FRAME_CRISIS_ES = ("[CRISIS WORDS heard from the person just now, in Spanish; this is Andy's own check, not something "
                   "they said.] Stay warm and keep talking with them. Say this, gently, and nothing else for now: "
                   + SAY_CRISIS_ES)
SAID_988 = re.compile(r"\b988\b|nine[- ]eight[- ]eight|nueve[- ]ocho[- ]ocho", re.I)
# The fixed sentences, recorded in Andy's voice (urgent_audio/regenerate.py), for when the model is away.
RECORDED = Path(__file__).with_name("urgent_audio")
RECORDINGS = {SAY: "call_911_en.wav", SAY_ES: "call_911_es.wav",
              SAY_CRISIS: "crisis_en.wav", SAY_CRISIS_ES: "crisis_es.wav"}
SENTENCE = {FRAME: SAY, FRAME_ES: SAY_ES, FRAME_CRISIS: SAY_CRISIS, FRAME_CRISIS_ES: SAY_CRISIS_ES}
# What speech-to-speech says, instead of a reply, when Token Factory fails (PROVIDER_FAILURE_FALLBACK).
MODEL_FAILED = re.compile(r"trouble responding right now", re.I)
# How long the model's follow-up may take before the recording plays instead: longer than the voice
# server's own model timeout (20 s) and its speech, so a slow but good answer isn't spoken over.
REPLY_WAIT_S = 35.0
# If urgent words get no reply at all (cut off, or a turn that never answers), the net speaks anyway.
NO_REPLY_S = 25.0
SPEECH_CPS = 14.0         # about how fast Andy speaks, to let the last reply finish before a recording


def _negated(value: str, start: int, end: int) -> bool:
    """True when a negation in the same clause directly governs the words at value[start:end]."""
    before = value[:start]
    cut = 0
    for boundary in CLAUSE.finditer(before):
        cut = boundary.end()
    if not NEGATION.search(before[cut:]):
        return False
    after = value[end:]
    stop = CLAUSE.search(after)
    return not COMPARED.search(after[:stop.start()] if stop else after)


def _matches(patterns, text: str) -> bool:
    value = " ".join(str(text).lower().replace("’", "'").split())
    for pattern in patterns:
        for m in re.finditer(pattern, value):
            if not _negated(value, m.start(), m.end()):
                return True
    return False


def is_crisis(text: str) -> bool:
    return _matches(CRISIS, text)


def is_urgent(text: str) -> bool:
    """Medical urgent words or crisis words: either way the net checks Andy's reply."""
    return is_crisis(text) or _matches(URGENT, text)


def spoke_spanish(text: str) -> bool:
    """Spanish when its words outnumber English ones (at least two), or tie when Spanish is the language
    the person chose."""
    value = str(text).lower().replace("’", "'")
    es, en = len(SPANISH.findall(value)), len(ENGLISH.findall(value))
    if es >= 2 and es > en:
        return True
    try:
        from andy_companion import settings
        chosen = settings.get().get("language")
    except Exception:
        chosen = None
    return chosen == "es" and es >= 1 and es >= en


def crisis_frame_for(text: str) -> str:
    """The crisis sentence in the person's language, for words found by the second look (guard.py)."""
    return FRAME_CRISIS_ES if spoke_spanish(text) else FRAME_CRISIS


def frame_for(text: str) -> str:
    spanish = spoke_spanish(text)
    if is_crisis(text):
        return FRAME_CRISIS_ES if spanish else FRAME_CRISIS
    return FRAME_ES if spanish else FRAME


# Words a Spanish 911 sentence has and an English one does not, to hear which language Andy used.
SPANISH_REPLY = re.compile(r"\b(llame|llamar|llama|ahora|usted|alguien|cercano|ayuda|emergencias|ambulancia|"
                           r"m[eé]dico|por favor)\b", re.I)


def needs_followup(reply: str, frame: str = FRAME) -> bool:
    """True unless Andy's reply already named 911 (for crisis words, 988 and 911), in Spanish when the
    person spoke Spanish."""
    reply = str(reply)
    if frame in (FRAME_CRISIS, FRAME_CRISIS_ES):
        # Both: 988 to talk with someone now, and 911 if they might be in danger (found missing in the suite).
        if not (SAID_988.search(reply) and SAID_911.search(reply)):
            return True
    elif not SAID_911.search(reply):
        return True
    return frame in (FRAME_ES, FRAME_CRISIS_ES) and not SPANISH_REPLY.search(reply)


def model_failed(reply: Optional[str]) -> bool:
    """True when a reply is no reply: nothing, or speech-to-speech's own words for a failed model call."""
    return reply is None or not str(reply).strip() or bool(MODEL_FAILED.search(str(reply)))


def recording_for(frame: str) -> Optional[Path]:
    name = RECORDINGS.get(SENTENCE.get(frame, ""))
    path = RECORDED / name if name else None
    return path if path is not None and path.is_file() else None


def play_recording(frame: str, opener=None) -> bool:
    """Play the frame's sentence from its recording on the robot's speaker. False if there is no
    recording or the daemon is away."""
    from andy_companion import chimes

    path = recording_for(frame)
    return path is not None and chimes.play_file(path, opener)


def install(handler_class=None) -> bool:
    if handler_class is None:
        from reachy_mini_conversation_app.conversation_handler import ConversationHandler

        handler_class = ConversationHandler
    previous = handler_class._emit_transcript
    if getattr(previous, "_andy_urgent", False):
        return False

    @wraps(previous)
    def emit(self, role: str, text: str, final: bool = True):
        previous(self, role, text, final)
        if not final:
            return
        if role == "user":
            # A later fragment ("in the kitchen", after "I've fallen") must not clear urgent words that
            # have not been answered yet; they wait for the next reply of Andy's.
            if is_urgent(text):
                self._andy_urgent_pending = frame_for(text)
                try:
                    asyncio.get_running_loop().create_task(_no_reply(self, self._andy_urgent_pending))
                except RuntimeError:
                    pass
            return
        if role != "assistant":
            return
        waiting = getattr(self, "_andy_urgent_reply", None)
        if waiting is not None and not waiting.done():
            waiting.set_result(str(text))          # the reply to the net's own follow-up
        self._andy_last_reply = str(text)
        if getattr(self, "_andy_urgent_pending", False):
            frame, self._andy_urgent_pending = self._andy_urgent_pending, False
            if needs_followup(text, frame):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    return
                loop.create_task(_follow_up(self, frame, reply=text))

    emit._andy_urgent = True
    handler_class._emit_transcript = emit
    return True


async def _no_reply(handler, frame: str, wait_s: Optional[float] = None) -> None:
    """Urgent words that get no reply of Andy's within NO_REPLY_S: the net follows up on its own."""
    await asyncio.sleep(NO_REPLY_S if wait_s is None else wait_s)
    if getattr(handler, "_andy_urgent_pending", False) == frame:
        handler._andy_urgent_pending = False
        logger.info("Urgent words got no reply; following up")
        await _follow_up(handler, frame)


async def _settled(handler, timeout: float) -> None:
    """Wait for Andy to finish speaking, so the sentence is not said over the end of a reply."""
    done = getattr(handler, "_response_done_event", None)
    if done is not None:
        await asyncio.wait_for(done.wait(), timeout=timeout)


async def _play(handler, frame: str, play: Callable[[str], bool], pause: Optional[float] = None) -> None:
    try:
        await _settled(handler, 10)
    except Exception:
        pass                                   # a stuck reply must not keep the sentence back
    # "Done" means the reply was made, not that it finished playing: let its words end first.
    spoken = str(getattr(handler, "_andy_last_reply", "") or "")
    await asyncio.sleep(min(8.0, len(spoken) / SPEECH_CPS) if pause is None else pause)
    try:
        played = await asyncio.to_thread(play, frame)
    except Exception:
        played = False
    if played:
        logger.info("Urgent-words sentence played from its recording")
    else:
        logger.warning("Urgent-words recording could not be played")


async def _follow_up(handler, frame: str = FRAME, reply: Optional[str] = None,
                     play: Optional[Callable[[str], bool]] = None, wait_s: Optional[float] = None) -> None:
    """Have Andy say the frame's sentence. The model says it when it can; when it cannot (no session,
    its failure words, no reply in wait_s) or its reply still leaves the number out, the recording
    plays instead. `reply` is Andy's reply that missed the number, when known."""
    play = play or play_recording
    if model_failed(reply) and reply is not None:
        # The model is failing right now: asking it again would only cost another failed round trip.
        await _play(handler, frame, play)
        return
    answer: Optional[str] = None
    try:
        await _settled(handler, 20)
        heard = asyncio.get_running_loop().create_future()
        handler._andy_urgent_reply = heard
        await handler.say(frame)
        answer = await asyncio.wait_for(heard, timeout=REPLY_WAIT_S if wait_s is None else wait_s)
    except Exception as e:  # never the words, only the type
        logger.warning("Urgent-words follow-up got no reply: %s", type(e).__name__)
    finally:
        handler._andy_urgent_reply = None
    if model_failed(answer) or needs_followup(answer, frame):
        await _play(handler, frame, play)
    else:
        logger.info("Urgent-words follow-up said")

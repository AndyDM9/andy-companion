"""Andy's fixed words in English and Spanish: day and month names, parts of the day, and the
templates for today's plan. Fixed words are written here, not translated by the model, so they are
said the same way every time in either language."""

from __future__ import annotations

from typing import Dict

LANGUAGES = ("en", "es")
DAYS = {"en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]}
MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                 "October", "November", "December"],
          "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                 "octubre", "noviembre", "diciembre"]}
PARTS = {"en": {"morning": "morning", "afternoon": "afternoon", "evening": "evening", "night": "night"},
         "es": {"morning": "mañana", "afternoon": "tarde", "evening": "tarde", "night": "noche"}}
PLAN: Dict[str, Dict[str, str]] = {
    "en": {"today_is": "Today is {weekday} {day} {month}.", "none": "You have no reminders today.",
           "count_one": "You have 1 reminder today: {items}.", "count": "You have {n} reminders today: {items}.",
           "item": "at {time}, {text}", "next": "The next one is at {time}.", "also": "Today is also: {items}."},
    "es": {"today_is": "Hoy es {weekday} {day} de {month}.", "none": "No tiene recordatorios hoy.",
           "count_one": "Tiene 1 recordatorio hoy: {items}.", "count": "Tiene {n} recordatorios hoy: {items}.",
           "item": "a las {time}, {text}", "next": "El siguiente es a las {time}.", "also": "Hoy también: {items}."},
}


def lang(value: str | None) -> str:
    return value if value in LANGUAGES else "en"


def weekday(dt, language: str = "en") -> str:
    return DAYS[lang(language)][dt.weekday()]


def month(dt, language: str = "en") -> str:
    return MONTHS[lang(language)][dt.month - 1]


# How Andy introduces itself on waking: warm ("your companion") and honest ("robot") in one line.
INTRO = {"en": "I'm Andy, your robot companion, here to help with your day.",
         "es": "Soy Andy, su compañero robot, para ayudarle con su día."}


def greeting(dt, language: str = "en") -> str:
    """The exact words Andy wakes with, for the time of day and the chosen language."""
    from andy_companion.clock import part_of_day

    part = part_of_day(dt)
    if lang(language) == "es":
        hello = {"morning": "Buenos días", "afternoon": "Buenas tardes",
                 "evening": "Buenas tardes" if dt.hour < 20 else "Buenas noches", "night": "Buenas noches"}[part]
        return f"¡{hello}! {INTRO['es']}"
    hello = {"morning": "Good morning", "afternoon": "Good afternoon", "evening": "Good evening", "night": "Hello"}[part]
    return f"{hello}! {INTRO['en']}"


# What the screen's state strip says. Tools are named by what Andy is doing, never by their code name.
STATE = {
    "en": {"ready": "Listening for you", "hearing": "Hearing you", "thinking": "Thinking",
           "speaking": "Speaking", "quiet": "Quiet until {until} · say “Andy, wake up”",
           "asleep": "Asleep · say “Good morning, Andy”", "away": "Andy's voice is off", "working": "Working on it"},
    "es": {"ready": "Escuchándole", "hearing": "Oyéndole", "thinking": "Pensando", "speaking": "Hablando",
           "quiet": "En silencio hasta las {until} · diga “Andy, wake up”",
           "asleep": "Dormido · diga “Good morning, Andy”", "away": "La voz de Andy está apagada",
           "working": "Trabajando en ello"},
}
TOOL_DOING = {
    "en": {"look_up": "Looking that up", "local_news": "Finding the local news", "whats_on": "Finding what's on",
           "read_link": "Reading the link", "check_message": "Checking that message", "look_into": "Starting to look into it",
           "weather": "Checking the weather", "describe_view": "Looking", "describe_photo": "Looking at the photo",
           "read_letter": "Reading the letter", "set_reminder": "Setting a reminder", "cancel_reminder": "Cancelling a reminder",
           "list_reminders": "Checking your reminders", "day_plan": "Getting today's plan", "get_today": "Checking the time",
           "what_you_remember": "Checking what I remember", "share_with_family": "Sharing with family"},
    "es": {"look_up": "Buscando", "local_news": "Buscando las noticias", "whats_on": "Buscando actividades",
           "read_link": "Leyendo el enlace", "check_message": "Revisando ese mensaje", "look_into": "Empezando a investigarlo",
           "weather": "Viendo el tiempo", "describe_view": "Mirando", "describe_photo": "Mirando la foto",
           "read_letter": "Leyendo la carta", "set_reminder": "Poniendo un recordatorio", "cancel_reminder": "Quitando un recordatorio",
           "list_reminders": "Viendo sus recordatorios", "day_plan": "Viendo el plan de hoy", "get_today": "Mirando la hora",
           "what_you_remember": "Viendo lo que recuerdo", "share_with_family": "Compartiendo con la familia"},
}


def state_label(state: str, tool: str = "", language: str = "en", until: str = "") -> str:
    lg = lang(language)
    if state == "working":
        return TOOL_DOING[lg].get(tool) or STATE[lg]["working"]
    return STATE[lg].get(state, STATE[lg]["ready"]).format(until=until)

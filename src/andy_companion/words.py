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

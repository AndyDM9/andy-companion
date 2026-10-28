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
    "en": {"today_is": "Today is {weekday}, {month} {day}.", "none": "You have no reminders today.",
           "count_one": "You have 1 reminder today: {items}.", "count": "You have {n} reminders today: {items}.",
           "item": "at {time}, {text}", "next": "The next one is at {time}.", "also": "Today is also: {items}."},
    "es": {"today_is": "Hoy es {weekday} {day} de {month}.", "none": "No tiene recordatorios hoy.",
           "count_one": "Tiene 1 recordatorio hoy: {items}.", "count": "Tiene {n} recordatorios hoy: {items}.",
           "item": "a las {time}, {text}", "next": "El siguiente es a las {time}.", "also": "Hoy también: {items}."},
}


# The parts of the day as the screen's clock line shows them ("Por la mañana, 9:41 am"): a bare
# "Mañana" there reads as "Tomorrow". The screen (pages/screen.html) keeps the same words; a test checks it.
PARTS_SHOWN = {"en": {"morning": "morning", "afternoon": "afternoon", "evening": "evening", "night": "night"},
               "es": {"morning": "por la mañana", "afternoon": "por la tarde", "evening": "por la tarde",
                      "night": "por la noche"}}


def lang(value: str | None) -> str:
    return value if value in LANGUAGES else "en"


def part_shown(dt, language: str = "en") -> str:
    """The part of the day as the screen's clock line says it. In Spanish the evening is "por la noche" from
    8 pm, as the greeting turns to "Buenas noches" then."""
    from andy_companion.clock import part_of_day

    lg, part = lang(language), part_of_day(dt)
    if lg == "es" and part == "evening" and dt.hour >= 20:
        part = "night"
    return PARTS_SHOWN[lg][part]


def date_shown(dt, language: str = "en", with_weekday: bool = False) -> str:
    """The date as the screen writes it, in the order people in Florida read it: "October 14" or
    "Wednesday, October 14"; in Spanish "14 de octubre" or "miércoles, 14 de octubre"."""
    lg = lang(language)
    date = f"{dt.day} de {month(dt, lg)}" if lg == "es" else f"{month(dt, lg)} {dt.day}"
    return f"{weekday(dt, lg)}, {date}" if with_weekday else date


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
           "what_you_remember": "Checking what I remember", "share_with_family": "Sharing with family",
           "think_it_through": "Thinking it through", "settings_code": "Showing the settings code"},
    "es": {"look_up": "Buscando", "local_news": "Buscando las noticias", "whats_on": "Buscando actividades",
           "read_link": "Leyendo el enlace", "check_message": "Revisando ese mensaje", "look_into": "Empezando a investigarlo",
           "weather": "Viendo el tiempo", "describe_view": "Mirando", "describe_photo": "Mirando la foto",
           "read_letter": "Leyendo la carta", "set_reminder": "Poniendo un recordatorio", "cancel_reminder": "Quitando un recordatorio",
           "list_reminders": "Viendo sus recordatorios", "day_plan": "Viendo el plan de hoy", "get_today": "Mirando la hora",
           "what_you_remember": "Viendo lo que recuerdo", "share_with_family": "Compartiendo con la familia",
           "think_it_through": "Pensándolo bien", "settings_code": "Mostrando el código de ajustes"},
}


def state_label(state: str, tool: str = "", language: str = "en", until: str = "") -> str:
    lg = lang(language)
    if state == "working":
        return TOOL_DOING[lg].get(tool) or STATE[lg]["working"]
    return STATE[lg].get(state, STATE[lg]["ready"]).format(until=until)


# The weather service writes English. For a Spanish screen, its period names and short forecasts are
# put into Spanish from their parts, never guessed: anything unknown keeps a plain, general word.
_PERIODS_ES = {"tonight": "Esta noche", "today": "Hoy", "this afternoon": "Esta tarde", "overnight": "Esta madrugada",
               "this morning": "Esta mañana"}
_DAYS_EN = [d.lower() for d in DAYS["en"]]


def weather_period(name: str, language: str = "en") -> str:
    if lang(language) != "es":
        return name
    key = " ".join(str(name).lower().split())
    if key in _PERIODS_ES:
        return _PERIODS_ES[key]
    day, _, rest = key.partition(" ")
    if day in _DAYS_EN:
        es = DAYS["es"][_DAYS_EN.index(day)]
        return es.capitalize() + (" por la noche" if rest == "night" else "")
    return name


def sky(short: str, language: str = "en") -> str:
    """'Sunny then Slight Chance Showers And Thunderstorms' -> 'Soleado, con leve posibilidad de chubascos y tormentas'."""
    if lang(language) != "es":
        return short
    s = " ".join(str(short).lower().split())
    first = s.split(" then ")[0]
    base = ""
    for words_, es in (("mostly sunny", "Mayormente soleado"), ("partly sunny", "Parcialmente soleado"), ("sunny", "Soleado"),
                       ("mostly clear", "Mayormente despejado"), ("partly cloudy", "Parcialmente nublado"),
                       ("mostly cloudy", "Mayormente nublado"), ("clear", "Despejado"), ("cloudy", "Nublado"),
                       ("fog", "Niebla"), ("haze", "Bruma"), ("windy", "Ventoso"), ("hot", "Caluroso")):
        if words_ in first:
            base = es
            break
    kinds = [es for en, es in (("showers", "chubascos"), ("thunderstorm", "tormentas"), ("rain", "lluvia"),
                               ("drizzle", "llovizna")) if en in s]
    if "showers" in s and "rain" in s and "rain showers" in s:
        kinds = [k for k in kinds if k != "lluvia"]
    if not kinds:
        return base or "Ver el pronóstico"
    how = ("leve posibilidad de " if "slight chance" in s else "posibilidad de " if "chance" in s else
           "probables " if "likely" in s else "")
    rain = how + " y ".join(kinds)
    return f"{base}, con {rain}" if base else rain[0].upper() + rain[1:]


# What the settings page lists as kept (kept.summary), beyond the person's own words: a reminder said every day, and
# what waits to be said when it has no words of its own (2026-10-28 review: the page showed "Look", "Message", "Photo").
KEPT = {
    "en": {"daily": "daily", "today": "today", "tomorrow": "tomorrow", "yesterday": "yesterday",
           "look": "{name} looked at the shared notes", "look_anon": "Someone looked at the shared notes",
           "link": "A link from {name}", "link_anon": "A link from family",
           "photo": "A photo from {name}", "photo_anon": "A photo from family", "other": "Something to pass on"},
    "es": {"daily": "cada día", "today": "hoy", "tomorrow": "mañana", "yesterday": "ayer",
           "look": "{name} miró las notas compartidas", "look_anon": "Alguien miró las notas compartidas",
           "link": "Un enlace de {name}", "link_anon": "Un enlace de la familia",
           "photo": "Una foto de {name}", "photo_anon": "Una foto de la familia", "other": "Algo que transmitir"},
}


def kept_word(key: str, language: str = "en", **values: str) -> str:
    return KEPT[lang(language)][key].format(**values)


# What the settings and family pages are told when something can't be done, in Spanish (usted, as on the pages). The
# reasons are written in English where they are raised; the screen server says them in the household's language
# (2026-10-28 review: a Spanish household read "Choose a time later than now."). A test checks every one is here.
PROBLEMS_ES: Dict[str, str] = {
    # the screen server
    "That is too long.": "Es demasiado largo.",
    "Something went wrong; please try again.": "Algo salió mal; pruebe otra vez.",
    "That is not a number.": "Eso no es un número.",
    "That's a lot at once; please wait a minute and try again.": "Es mucho a la vez; espere un minuto y pruebe otra vez.",
    "This is a public demo with sample data: nothing you send is kept or shown to anyone.":
        "Esta es una demostración pública con datos de ejemplo: nada de lo que envíe se guarda ni se muestra a nadie.",
    "Your first name is needed, so Andy can tell them who deleted it.":
        "Hace falta su nombre, para que Andy pueda decir quién lo borró.",
    "Your first name is needed, so Andy can tell them who changed it.":
        "Hace falta su nombre, para que Andy pueda decir quién lo cambió.",
    "That was already gone.": "Eso ya se había borrado.",
    "Unknown kind of item.": "No se reconoce ese tipo de elemento.",
    # the settings
    "Use web addresses, one per line.": "Use direcciones web, una por línea.",
    "Settings must be an object of named choices.": "Los ajustes no tienen la forma esperada.",
    "Settings must be an object.": "Los ajustes no tienen la forma esperada.",
    "Their first name must be text.": "El nombre de la persona debe ser texto.",
    "The town must be text.": "La ciudad debe ser texto.",
    "The language is English or Spanish.": "El idioma es inglés o español.",
    "The pace is normal or slow.": "El ritmo es normal o más despacio.",
    "The volume is a number from 10 to 100.": "El volumen es un número del 10 al 100.",
    "The screen's direction is a number of degrees from -120 to 120.":
        "La dirección de la pantalla es un número de grados entre -120 y 120.",
    "The screen is above, level with or below Andy's eyes.":
        "La pantalla está por encima, a la altura o por debajo de los ojos de Andy.",
    "The night clock shows at the hours chosen, while Andy is asleep, or never.":
        "El reloj de noche aparece a las horas elegidas, mientras Andy duerme, o nunca.",
    "Night hours are from 0 to 23.": "Las horas de la noche van de 0 a 23.",
    "A saved setting has an unsupported value.": "Un ajuste guardado tiene un valor no admitido.",
    "Settings could not be read or preserved. No settings changes were made.":
        "No se pudieron leer ni conservar los ajustes. No se hizo ningún cambio.",
    "Settings changes have an unsupported field or value.": "Los cambios tienen un campo o un valor no admitido.",
    # what family send
    "A name is needed.": "Hace falta un nombre.",
    "A name and a message or link are needed.": "Hacen falta un nombre y un mensaje o un enlace.",
    "That link doesn't look right. Send a web address that starts with https://.":
        "Ese enlace no parece correcto. Envíe una dirección web que empiece por https://.",
    "A link starts with http:// or https://.": "Un enlace empieza por http:// o https://.",
    "A name and what to remind them about are needed.": "Hacen falta un nombre y qué recordarle.",
    "A suggestion can't carry a link. Send a link as a message instead.":
        "Una sugerencia no puede llevar un enlace. Envíe el enlace como mensaje.",
    "Choose a day and a time.": "Elija un día y una hora.",
    "Choose a time later than now.": "Elija una hora más tarde que ahora.",
    "Choose a time within the next week.": "Elija una hora dentro de la próxima semana.",
    "Choose a time.": "Elija una hora.",
    "Choose a day.": "Elija un día.",
    "The photo must be smaller than 8 MB.": "La foto debe ocupar menos de 8 MB.",
    "Send the photo as a JPEG, PNG or WebP.": "Envíe la foto como JPEG, PNG o WebP.",
    "That photo is too large to show; send a smaller copy.":
        "Esa foto es demasiado grande para mostrarla; envíe una copia más pequeña.",
    "That file is not a photo Andy can show.": "Ese archivo no es una foto que Andy pueda mostrar.",
    "The photo could not be prepared.": "No se pudo preparar la foto.",
    "Andy has a lot waiting to be passed on. Please try again later.":
        "Andy tiene muchas cosas pendientes de transmitir. Pruebe otra vez más tarde.",
    "A name and what changed are needed.": "Hacen falta un nombre y lo que cambió.",
    "A name and what was deleted are needed.": "Hacen falta un nombre y lo que se borró.",
}
# Reasons with a number or the helper's own words in them.
PROBLEM_PATTERNS_ES = (
    (r'"(.*)" is not a web address\. Use one per line, like wlrn\.org\.',
     r"«\1» no es una dirección web. Use una por línea, como wlrn.org."),
    (r"Up to (\d+) sites, please\.", r"Hasta \1 sitios, por favor."),
    (r"Their first name can have letters, spaces, hyphens and apostrophes, up to (\d+) in all\.",
     r"El nombre puede tener letras, espacios, guiones y apóstrofos, hasta \1 en total."),
    (r"Choose on or off for .+\.", "Elija sí o no para esa opción."),
    (r"That link is too long\. Send a shorter web address, up to (\d+) characters\.",
     r"Ese enlace es demasiado largo. Envíe una dirección web más corta, de hasta \1 caracteres."),
    (r"Keep it short: up to (\d+) characters\.", r"Que sea breve: hasta \1 caracteres."),
)


def problem(message: str, language: str = "en") -> str:
    """A reason something can't be done, in the household's language. Anything not written here reads as the general
    "something went wrong" in Spanish rather than as English."""
    import re

    if lang(language) != "es":
        return message
    if message in PROBLEMS_ES:
        return PROBLEMS_ES[message]
    for pattern, spanish in PROBLEM_PATTERNS_ES:
        found = re.fullmatch(pattern, message, re.S)
        if found:
            return found.expand(spanish)
    return PROBLEMS_ES["Something went wrong; please try again."]

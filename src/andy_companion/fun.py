"""A joke or a riddle, from a chosen set, never the same one twice in a while.

Andy tells jokes from this list rather than making them up, so every one has been read first: gentle
wordplay and puns, the kind most people groan at and smile. None about age, memory, health, bodies,
death, money worries, or any group of people. Riddles are for guessing together; any guess is fine.

What has been told is kept as joke numbers and times only (`fun.json`, owner-only), so Andy doesn't
repeat itself within REPEAT_AFTER_DAYS. Nothing the person says is kept.
"""

from __future__ import annotations

import json
import os
import random
import tempfile
import time
from typing import Any, Dict, List, Optional

from andy_companion.reminders import DATA_DIR

FILE = DATA_DIR / "fun.json"
REPEAT_AFTER_DAYS = 30

JOKES: Dict[str, List[tuple]] = {
    "en": [
        ("Why don't eggs tell jokes?", "They'd crack each other up."),
        ("Why did the scarecrow win an award?", "Because he was outstanding in his field."),
        ("What do you call a fish wearing a bow tie?", "Sofishticated."),
        ("Why did the bicycle fall over?", "It was two tired."),
        ("What did the ocean say to the beach?", "Nothing. It just waved."),
        ("Why can't you trust the stairs?", "They're always up to something."),
        ("What do you call a sleeping bull?", "A bulldozer."),
        ("Why did the tomato blush?", "Because it saw the salad dressing."),
        ("What did one wall say to the other?", "I'll meet you at the corner."),
        ("Why do bees have sticky hair?", "Because they use honeycombs."),
        ("What do you call cheese that isn't yours?", "Nacho cheese."),
        ("How does a penguin build its house?", "Igloos it together."),
        ("What did the grape do when it got stepped on?", "It let out a little wine."),
        ("Why are fish so smart?", "They live in schools."),
        ("What do you call a dinosaur with an extensive vocabulary?", "A thesaurus."),
        ("Why did the golfer bring two pairs of trousers?", "In case he got a hole in one."),
        ("What kind of tree fits in your hand?", "A palm tree."),
        ("Why was the math book unhappy?", "It had too many problems."),
        ("What did the big flower say to the little flower?", "Hi, bud!"),
        ("Why did the coffee file a police report?", "It got mugged."),
        ("What do you call a pig that does karate?", "A pork chop."),
        ("How do you make a tissue dance?", "Put a little boogie in it."),
        ("Why did the picture go to jail?", "It was framed."),
        ("Why do seagulls fly over the sea?", "Because if they flew over the bay, they'd be bagels."),
        ("What do you call a fake noodle?", "An impasta."),
        ("Why did the orange stop halfway up the hill?", "It ran out of juice."),
        ("What did the janitor say when he jumped out of the closet?", "Supplies!"),
        ("How do you organise a party in space?", "You planet."),
        ("Why couldn't the leopard play hide and seek?", "Because he was always spotted."),
        ("What has four wheels and flies?", "A rubbish truck."),
        ("What do you call an alligator in a vest?", "An investigator."),
        ("What did the hat say to the scarf?", "You hang around. I'll go on ahead."),
        ("Why did the music teacher need a ladder?", "To reach the high notes."),
    ],
    "es": [
        ("¿Qué hace una abeja en el gimnasio?", "¡Zum-ba!"),
        ("¿Cuál es el café más peligroso del mundo?", "El ex-preso."),
        ("¿Qué le dijo un techo a otro techo?", "Techo de menos."),
        ("¿Por qué el libro de matemáticas estaba triste?", "Porque tenía muchos problemas."),
        ("¿Qué le dice una iguana a su hermana gemela?", "Somos iguanitas."),
        ("¿Cómo se dice pañuelo en japonés?", "Saka-moko."),
        ("¿Qué le dijo el pez a otro pez?", "Nada."),
        ("¿Qué le dice una uva verde a una uva morada?", "¡Respira, respira!"),
        ("¿Cuál es el colmo de un jardinero?", "Que su novia lo deje plantado."),
        ("¿Qué le dijo el semáforo al coche?", "No me mires, que me estoy cambiando."),
        ("¿Por qué las focas miran siempre hacia arriba?", "¡Porque ahí están los focos!"),
        ("¿Qué hace un perro con un taladro?", "Taladrando."),
        ("¿Cuál es el colmo de un electricista?", "Que su mujer se llame Luz y sus hijos le sigan la corriente."),
        ("¿Qué le dice un gusano a otro gusano?", "Voy a dar una vuelta a la manzana."),
    ],
}

RIDDLES: Dict[str, List[tuple]] = {
    "en": [
        ("What has keys but can't open a single lock?", "A piano."),
        ("What has hands but can't clap?", "A clock."),
        ("What gets wetter the more it dries?", "A towel."),
        ("What has a neck but no head?", "A bottle."),
        ("What has many teeth but can't bite?", "A comb."),
        ("What has an eye but cannot see?", "A needle."),
        ("What runs but never walks, has a mouth but never talks?", "A river."),
        ("What can travel around the world while staying in a corner?", "A stamp."),
        ("What has one head, one foot and four legs?", "A bed."),
        ("What is full of holes but still holds water?", "A sponge."),
        ("What kind of room has no doors or windows?", "A mushroom."),
        ("What comes down but never goes up?", "Rain."),
        ("What has a thumb and four fingers but isn't alive?", "A glove."),
    ],
    "es": [
        ("Blanco por dentro, verde por fuera. Si quieres que te lo diga, espera.", "La pera."),
        ("Tiene agujas pero no sabe coser. ¿Qué es?", "El reloj."),
        ("Cuanto más le quitas, más grande es. ¿Qué es?", "Un agujero."),
        ("Tiene dientes y no come, tiene cabeza y no es hombre. ¿Qué es?", "El ajo."),
        ("Oro parece, plata no es. ¿Qué es?", "El plátano."),
        ("Vuela sin alas, silba sin boca. ¿Qué es?", "El viento."),
        ("Tiene ojos y no ve, tiene agua y no la bebe. ¿Qué es?", "El coco."),
    ],
}

HOW = {
    "joke": ("Tell it in your own voice: the setup, a short pause, then the punchline, word for word. Don't "
             "explain it or laugh at it yourself. Then let them react, and enjoy it with them. One at a time; "
             "tell another only if they ask."),
    "riddle": ("Ask the riddle and let them guess; there's no hurry. Whatever they say, be warm: a right guess "
               "gets a cheer, a wrong one gets the answer gently, never a correction. If they say 'tell me', "
               "give the answer."),
}


def _read() -> Dict[str, Any]:
    try:
        data = json.loads(FILE.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(data: Dict[str, Any]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, FILE)


def pick(kind: str = "joke", language: str = "en", now: Optional[float] = None, rng: Any = random) -> Dict[str, Any]:
    """One joke or riddle not told in the last REPEAT_AFTER_DAYS (the oldest told, if all have been)."""
    kind = "riddle" if kind == "riddle" else "joke"
    lang = "es" if language == "es" else "en"
    pool = (RIDDLES if kind == "riddle" else JOKES)[lang]
    now = time.time() if now is None else now
    told = _read()
    key = f"{kind}-{lang}"
    seen = {int(k): v for k, v in (told.get(key) or {}).items()}
    fresh = [i for i in range(len(pool)) if now - seen.get(i, 0) > REPEAT_AFTER_DAYS * 86400]
    i = rng.choice(fresh) if fresh else min(range(len(pool)), key=lambda j: seen.get(j, 0))
    seen[i] = now
    told[key] = {str(k): v for k, v in seen.items()}
    _write(told)
    first, second = pool[i]
    if kind == "riddle":
        return {"riddle": first, "answer": second, "how": HOW["riddle"]}
    return {"setup": first, "punchline": second, "how": HOW["joke"]}

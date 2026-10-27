"""Think it through: a hard question goes to NVIDIA Nemotron 3 Ultra, the bigger model, on Token Factory.

Andy talks with Nemotron 3.5 Lightning because it answers in under a second. Some questions deserve
more ("Should I move closer to my daughter?", "How do I choose between these two community
centres?"). For those, Andy hands the question to Nemotron 3 Ultra, which reasons first, and speaks a
short, balanced answer: what matters, a question or two to ask oneself, and who could help. As the
track says: Ultra for serious reasoning, the fast model for everyday calls.

Never personal medical, legal or financial advice: Ultra is told to say who to ask instead. The
question goes to Token Factory (zero data retention on), like every turn; nothing is kept or logged.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Callable, Optional

from andy_companion.model_reply import final_text

MODEL = os.environ.get("ANDY_DEEP_MODEL", "nvidia/Nemotron-3-Ultra-550b-a55b")
TIMEOUT_S = 60
BRIEF = (
    "You help an older adult who lives at home think through a question, speaking through their home "
    "companion robot. Answer in plain, warm, spoken English{lang}, in four to six short sentences: what "
    "matters most, both sides where there are two, one or two questions they might ask themselves, and "
    "who could help them decide (family, a friend, or the right professional). Do not give medical, legal "
    "or financial advice about their own situation: say kindly who to ask instead. No lists, no headings, "
    "no links. Do not pretend to know their life; ask nothing back."
)


class DeeperError(Exception):
    pass


def think(question: str, language: str = "en", opener: Optional[Callable] = None) -> str:
    key = os.environ.get("NEBIUS_API_KEY", "")
    if not key:
        raise DeeperError("Thinking it through needs the Token Factory key.")
    question = " ".join(str(question or "").split())[:1500]
    if not question:
        raise DeeperError("What should I think through?")
    base = os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").rstrip("/")
    body = {"model": MODEL, "max_tokens": 1500, "temperature": 0.3,
            "messages": [{"role": "system", "content": BRIEF.format(lang=" (in Spanish)" if language == "es" else "")},
                         {"role": "user", "content": question}]}
    req = urllib.request.Request(base + "/chat/completions", method="POST", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
            text = final_text(json.loads(r.read()))
    except Exception as e:   # never echo the request: it holds the person's question
        raise DeeperError(f"The bigger model did not answer ({type(e).__name__}).") from None
    # Ultra reasons first; only the answer is spoken.
    answer = " ".join(text.split())
    if not answer:
        raise DeeperError("The bigger model gave no answer.")
    return answer[:1200]

"""See Andy's screen, family page and settings page on sample data, with no robot, GPU or keys.

    uv run python scripts/demo_screen.py            then open the addresses it prints

It runs Andy's real screen server on a throwaway data folder, with made-up reminders, a sample
weather card, and a card that changes every 20 seconds (what Andy found, a letter with a warning, the
day's plan, a story, On this day), so you can see the screen as it is beside the robot. Nothing
leaves this computer. Ctrl+C stops it, and the throwaway folder is deleted.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

DATA = Path(tempfile.mkdtemp(prefix="andy-demo-"))
os.environ["ANDY_DATA_DIR"] = str(DATA)          # before Andy's modules load
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion import board, dayplan, letters, moments, reminders, screen_server, settings, state, stories  # noqa: E402

PORT = int(os.environ.get("ANDY_DEMO_PORT", "8093"))
CAPTIONS = {
    "research": "I looked into it: the farmers market isn't on this Saturday. It runs on the first Saturday of each month.",
    "letter": "This letter asks for gift cards and threatens arrest. Real organisations never do that. Shall we check with Anna first?",
    "today": "Today is Tuesday. You have three reminders, and it's also Sofia's piano recital.",
    "story": "The Lion and the Mouse, by Aesop. A Lion lay asleep in the forest, his great head resting on his paws.",
}


def research() -> None:
    board.show("research", "Is the farmers market on this Saturday?", [
        {"title": "Not this Saturday, October 17"}, {"title": "First Saturday of each month, 9 am to noon"},
        {"title": "Next market: Saturday, November 7"}, {"title": "Sources", "summary": "harborbayfl.gov, miamifarmersmarket.org"}])


def letter() -> None:
    page = ("FINAL NOTICE - Prize Release Center. You have WON $25,000! Pay the $500 processing fee within 24 hours "
            "with gift cards. Call 1-888-555-0199 now.")
    letters.show(letters.card({"kind": "letter", "sender": "Prize Release Center", "about": "You won a $25,000 prize",
                               "to_do": "Pay the $500 fee", "by_when": "within 24 hours", "amount": "$500", "caution": "",
                               "suspicious": True}, page))


def main() -> int:
    board._write(board.TOKENS, {"screen": "demo-screen", "family": "demo-family", "setup": "demo-setup"})
    state.awake()
    settings.update(place="Harbor Bay, Florida", night_from=23, night_to=6)
    reminders.add("Call Rosa", minutes=20)
    reminders.add("Evening tablets with dinner", minutes=80)
    reminders.add("Water the orchids", minutes=140)
    moments.add("Sofia's piano recital", "today", today=date.today())
    board.share("I had a lovely walk by the sea this morning.")
    screen_server._weather.update(card={"periods": [
        {"name": "Tonight", "temperature": "79°", "short": "Mostly Clear", "rain": None},
        {"name": "Tomorrow", "temperature": "86°", "short": "Chance Showers", "rain": 40}],
        "alerts": [], "source": "weather.gov"}, at=time.time(), busy=False)
    screen_server.serve(host="127.0.0.1", port=PORT)
    base = f"http://127.0.0.1:{PORT}"
    print(f"Andy's screen (open it full screen): {base}/screen?t=demo-screen")
    print(f"The family page:                     {base}/family?k=demo-family")
    print(f"The settings page:                   {base}/setup?s=demo-setup")
    print(f"Under the hood:                      {base}/hood?t=demo-screen")
    print("Sample data only; Ctrl+C to stop.", flush=True)
    scenes = [("research", research), ("letter", letter), ("today", dayplan.show), ("story", lambda: stories.start("lion"))]
    try:
        i = 0
        while True:
            name, show = scenes[i % len(scenes)]
            show()
            started = time.time()
            while time.time() - started < 20:
                screen_server.set_live({"state": "speaking", "tool": ""})
                screen_server.set_caption(CAPTIONS[name])
                time.sleep(1)
            i += 1
    except KeyboardInterrupt:
        return 0
    finally:
        shutil.rmtree(DATA, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

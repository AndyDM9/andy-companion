"""See Andy's screen, family page and settings page on sample data, with no robot, GPU or keys.

    uv run python scripts/demo_screen.py            then open the addresses it prints

It runs Andy's real screen server on a throwaway data folder, with made-up reminders, a sample
weather card, and a card that changes every 20 seconds (research, finding glasses with the four views Andy
looked at, a letter with a warning, a scam check's three steps, the day's plan, a family note, a story), so
you can see the screen as it is beside the robot. Under the hood
shows sample turns with times of the kind measured on the robot (2026-10-13 and 14), so the page isn't
empty without one. Nothing leaves this computer. Ctrl+C stops it, and the throwaway folder is deleted.
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
    "story": "The Lion and the Mouse, by Aesop. A Lion lay asleep in the forest, his great head resting on his paws.",
    "found": "I think I see your glasses, on the table by the lamp. It's on your screen too.",
    "scam": "This shows a sign of a known scam: a grandson in trouble asking for money. The FTC warns about messages like this. Let's check with Anna first.",
    "note": "Anna sent you a note: she'll call you at six tonight.",
}


def room(view: int) -> bytes:
    """A made-up view of a room for the finder's strip (no camera here): a wall, a floor, furniture, and in
    the third view a pair of glasses on a table by a lamp."""
    import cv2
    import numpy as np

    img = np.zeros((270, 480, 3), np.uint8)
    img[:] = (150, 170, 190)                                   # wall
    img[180:] = (90, 110, 130)                                 # floor
    shade = 60 + 30 * view
    cv2.rectangle(img, (40 + 20 * view, 120), (200 + 20 * view, 200), (70, shade, 120), -1)          # sofa or shelf
    if view == 2:
        cv2.rectangle(img, (250, 150), (430, 165), (60, 80, 110), -1)                                 # table
        cv2.rectangle(img, (395, 70), (405, 150), (50, 50, 50), -1)                                   # lamp
        cv2.ellipse(img, (400, 70), (32, 20), 0, 180, 360, (200, 230, 240), -1)
        for x in (310, 350):                                                                          # glasses
            cv2.circle(img, (x, 143), 14, (20, 20, 20), 3)
        cv2.line(img, (324, 143), (336, 143), (20, 20, 20), 3)
    ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return jpg.tobytes()


def found() -> None:
    screen_server.set_views([room(i) for i in range(4)], [False, False, True, False], 2)
    board.show("seen", "Your glasses", [{"summary": "on the table by the lamp"}])


def scam() -> None:
    # As tools/check_message.py shows a scam with a matching warning (its RECEIPT words), on sample data.
    board.show("check", "Be careful: a known scam", [
        {"title": "The sign", "summary": "A relative or friend in trouble asking for money: “I'm in jail… need bail money today”",
         "tone": "caution"},
        {"title": "The warning", "summary": "consumer.ftc.gov: Scammers pretend to be your grandchild in trouble", "tone": "caution"},
        {"title": "Why it matches", "summary": "NVIDIA Nemotron 3 Ultra compared them: the same trick, not just the same topic.",
         "tone": "caution"}], how={"calls": ["search"], "depth": "advanced", "seconds": 3.1, "credits": 2})


def note() -> None:
    board.show("note", "A note from Anna", [{"summary": "I'll call you at six tonight. Love, Anna", "when": "5:42 pm"}])


def research() -> None:
    board.show("research", "Is the farmers market on this Saturday?", [
        {"title": "Not this Saturday, October 17"}, {"title": "First Saturday of each month, 9 am to noon"},
        {"title": "Next market: Saturday, November 7"}, {"title": "Sources", "summary": "harborbayfl.gov, miamifarmersmarket.org"}],
        how={"calls": ["research"], "depth": "mini", "seconds": 23.4, "credits": None, "sites": 9})


# What the head is turned to in each scene, as the behaviours would say on the robot (body/looking_at.py).
LOOKING = {"research": "screen", "found": "pointing"}


def today_caption() -> str:
    """The day's caption from the same clock and reminders as the card, so the two never disagree."""
    n = len(reminders.pending())
    return (f"Today is {date.today():%A}. You have {n} reminder{'s' if n != 1 else ''} still to come, "
            "and it's also Sofia's piano recital.")


# Sample turns for Under the hood, in the shape Andy's own turns take (numbers and tool names only), with
# times like those measured on the robot: Parakeet tens of milliseconds, Nemotron under a second, tools
# as long as they take.
SAMPLE_TURNS = [
    {"hearing_ms": 42, "reply_ms": 812, "total_ms": 854, "tools": []},
    {"hearing_ms": 38, "reply_ms": 1290, "total_ms": 1328, "tools": [{"name": "weather", "ms": 410}]},
    {"hearing_ms": 55, "reply_ms": 2460, "total_ms": 2515, "tools": [{"name": "look_up", "ms": 1420}]},
    {"hearing_ms": 47, "reply_ms": 5120, "total_ms": 5167, "tools": [{"name": "find_object", "ms": 4180}]},
    {"hearing_ms": 61, "reply_ms": 4380, "total_ms": 4441, "tools": [{"name": "check_message", "ms": 3350}]},
    {"hearing_ms": 33, "reply_ms": 905, "total_ms": 938, "tools": []},
]


def letter() -> None:
    page = ("FINAL NOTICE - Prize Release Center. You have WON $25,000! Pay the $500 processing fee within 24 hours "
            "with gift cards. Call 1-888-555-0199 now.")
    letters.show(letters.card({"kind": "letter", "sender": "Prize Release Center", "about": "You won a $25,000 prize",
                               "to_do": "Pay the $500 fee", "by_when": "within 24 hours", "amount": "$500", "caution": "",
                               "suspicious": True}, page))


def main() -> int:
    import signal

    # A kill (SIGTERM) cleans up like Ctrl+C, so the throwaway folder never stays behind.
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    board._write(board.TOKENS, {"screen": "demo-screen", "family": "demo-family", "setup": "demo-setup", "hood": "demo-hood"})
    state.awake()
    settings.update(place="Harbor Bay, Florida", night_from=23, night_to=6)
    reminders.add("Call Rosa", minutes=20)
    reminders.add("Put the bins out", minutes=80)
    reminders.add("Water the orchids", minutes=140)
    moments.add("Sofia's piano recital", "today", today=date.today())
    board.share("I had a lovely walk by the sea this morning.")
    screen_server._weather.update(card={"periods": [
        {"name": "Tonight", "temperature": "79°", "short": "Mostly Clear", "rain": None},
        {"name": "Tomorrow", "temperature": "86°", "short": "Chance Showers", "rain": 40}],
        "alerts": [], "source": "weather.gov"}, at=time.time(), busy=False)
    for turn in SAMPLE_TURNS:
        screen_server.add_turn(turn)
    screen_server.set_tavily({"plan": "sample", "used": 214, "limit": 1000,
                              "by": {"search": 160, "extract": 6, "crawl": 4, "map": 2, "research": 42}})
    screen_server.serve(host="127.0.0.1", port=PORT)
    base = f"http://127.0.0.1:{PORT}"
    print(f"Andy's screen (open it full screen): {base}/screen?t=demo-screen")
    print(f"The family page:                     {base}/family?k=demo-family")
    print(f"The settings page:                   {base}/setup?s=demo-setup")
    print(f"Under the hood:                      {base}/hood?t=demo-hood")
    print("Sample data only; Ctrl+C to stop.", flush=True)
    scenes = [("research", research), ("found", found), ("letter", letter), ("scam", scam), ("today", dayplan.show),
              ("note", note), ("story", lambda: stories.start("lion"))]
    try:
        i = 0
        while True:
            name, show = scenes[i % len(scenes)]
            show()
            started = time.time()
            while time.time() - started < 20:
                screen_server.set_live({"state": "speaking", "tool": "", "looking": LOOKING.get(name, "you")})
                screen_server.set_caption(today_caption() if name == "today" else CAPTIONS[name])
                time.sleep(1)
            i += 1
    except KeyboardInterrupt:
        return 0
    finally:
        shutil.rmtree(DATA, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

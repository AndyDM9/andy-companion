"""See Andy's screen, family page and settings page on sample data, with no robot, GPU or keys.

    uv run python scripts/demo_screen.py            then open the addresses it prints
    uv run python scripts/demo_screen.py --public   the same for anyone to open (a Hugging Face Space: space/)

It runs Andy's real screen server on a throwaway data folder, with made-up reminders, a sample
weather card, and a card that changes every 20 seconds (research, finding glasses with the four views Andy
looked at, a letter with a warning, a scam check's three steps, the day's plan, a family note, a story), so
you can see the screen as it is beside the robot. Under the hood
shows sample turns with times of the kind measured on the robot (2026-10-13 and 14), so the page isn't
empty without one. Nothing leaves this computer. Ctrl+C stops it, and the throwaway folder is deleted.

`ANDY_DEMO_SCENE=found` (research, searching, found, letter, scam, today, note, keys, story or quiet) holds one scene, for
screenshots and for filming the screen.

`--public` (or ANDY_DEMO_PUBLIC=1) is for a hosted copy that anyone can open (PLAN B26): it listens on every
address, on $PORT if set (Hugging Face uses 7860), keeps the night clock off, lets the Space's page frame it,
and takes nothing a visitor sends (every form says so), so one visitor's words never reach another.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

if __name__ == "__main__":                        # run as the demo: its own throwaway folder, before Andy's modules load
    DATA = Path(tempfile.mkdtemp(prefix="andy-demo-"))
    os.environ["ANDY_DATA_DIR"] = str(DATA)
else:                                             # imported (a test): nothing made, changed or ever deleted
    DATA = Path(os.environ.get("ANDY_DATA_DIR") or Path(tempfile.gettempdir()) / "andy-imported-demo")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion import board, dayplan, letters, moments, reminders, screen_server, settings, state, stories  # noqa: E402

PUBLIC = "--public" in sys.argv[1:] or os.environ.get("ANDY_DEMO_PUBLIC") == "1"
PORT = int(os.environ.get("ANDY_DEMO_PORT") or (os.environ.get("PORT") if PUBLIC else None) or "8093")
PAGES = [("/screen?t=demo-screen", "The TV beside Andy",
          "Open it full screen, on a big screen if you can. Every 20 seconds it shows another thing Andy puts up: "
          "a Tavily research answer, the glasses it found, a letter with a warning, a scam check, the day, a family "
          "note, your keys where you left them, a story, and a quiet moment when Andy waves back."),
         ("/hood?t=demo-hood", "Under the hood",
          "Each turn stage by stage: how long hearing, thinking and each tool took, and where each ran."),
         ("/family?k=demo-family", "The family page",
          "What a relative sees on their phone: only what the person asked Andy to share."),
         ("/setup?s=demo-setup", "The settings page",
          "What a helper can change from a phone. Andy tells the person who changed what.")]
CAPTIONS = {
    "research": "I looked into it: the farmers market isn't on this Saturday. It runs on the first Saturday of each month.",
    "letter": "This letter asks for gift cards and threatens arrest. Real organisations never do that. Shall we check with Anna first?",
    "story": "The Lion and the Mouse, by Aesop. A Lion lay asleep in the forest, his great head resting on his paws.",
    "found": "I think I see your glasses, on the table by the lamp. It's on your screen too.",
    "scam": "This shows a sign of a known scam: a grandson in trouble asking for money. The FTC warns about messages like this. Let's check with Anna first.",
    "note": "Anna sent you a note: she'll call you at six tonight.",
    "keys": "They're still where you left them, on the hall table.",
}


def index_page() -> bytes:
    """The demo's front page: what Andy is, and the four pages, each with one line on what it shows."""
    import html

    links = "".join(f'<li><a href="{href}">{html.escape(name)}</a><span>{html.escape(what)}</span></li>'
                    for href, name, what in PAGES)
    repo = "https://github.com/AndyDM9/andy-companion"
    extra = "".join(f'<p><a href="{html.escape(url, quote=True)}">{label}</a></p>' for label, url in
                    (("The video", os.environ.get("ANDY_DEMO_VIDEO", "")),
                     ("Try guided AI examples (separate Space, simulated tools)", "https://andydm-andy-companion-judge.hf.space/"),
                     ("The code", os.environ.get("ANDY_DEMO_REPO", repo)),
                     ("Testing instructions", f"{repo}/blob/main/docs/judging.md"))
                    if url.startswith("https://"))
    privacy = ("Nothing you type on these pages is sent or kept." if PUBLIC else
               "Nothing you type here leaves this computer, and all of it is deleted when the demo stops.")
    film = ""
    if "/media/sim-search.mp4" in screen_server.MEDIA:
        film = ('<figure><video src="/media/sim-search.mp4" autoplay muted loop playsinline controls width="100%"></video>'
                "<figcaption>No robot here either, so this is Andy's own search for a rubber duck in simulation (Pollen's "
                "MuJoCo scene): it looks around, reads each view as six zoomed tiles with NVIDIA Nemotron 3.5 Super VL, "
                "looks closer, and points. See the testing instructions for real-hardware access.</figcaption></figure>")
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,"><title>Andy, on sample data</title>
<style>
@font-face {{ font-family: "Atkinson Hyperlegible"; src: url(/fonts/atkinson-hyperlegible-400.woff2) format("woff2"); font-weight: 400; }}
@font-face {{ font-family: "Atkinson Hyperlegible"; src: url(/fonts/atkinson-hyperlegible-700.woff2) format("woff2"); font-weight: 700; }}
:root {{ --ground: #e1ebdc; --ink: #1d2a1f; --soft: #334335; --mark: #1c5244; --panel: #f2f6ef; --rule: #c7d5c1; }}
@media (prefers-color-scheme: dark) {{ :root {{ --ground: #0b1020; --ink: #e6eaf2; --soft: #c2cad8; --mark: #e2cd94;
  --panel: #151d36; --rule: #2b3756; }} }}
body {{ margin: 0; background: var(--ground); color: var(--ink); font: 19px/1.5 "Atkinson Hyperlegible", system-ui, sans-serif; }}
main {{ max-width: 46rem; margin: 0 auto; padding: 48px 16px 64px; }}
h1 {{ font-size: 2.4rem; line-height: 1.1; margin: 0 0 16px; }}
p {{ color: var(--soft); margin: 0 0 14px; }}
ul {{ list-style: none; padding: 0; margin: 28px 0; }}
li {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 18px; padding: 18px 20px; margin: 0 0 12px; }}
li a {{ display: block; font-size: 1.3rem; font-weight: 700; color: var(--mark); }}
li span {{ display: block; color: var(--soft); margin-top: 4px; }}
a {{ color: var(--mark); }}
a:focus-visible {{ outline: 3px solid var(--mark); outline-offset: 3px; border-radius: 4px; }}
.note {{ font-size: 1rem; }}
figure {{ margin: 24px 0; }} video {{ border-radius: 14px; display: block; }}
figcaption {{ color: var(--soft); font-size: 1rem; margin-top: 8px; }}
</style>
<main>
<h1>Andy's screens, on sample data</h1>
<p>Andy is a small home robot for older adults who live at home, and the family who help. It runs on a Reachy
Mini, and it is built with NVIDIA Nemotron on Nebius Token Factory, and Tavily.</p>
<p>No robot is connected here. These are Andy's real pages, running on made-up reminders, letters and
messages.</p>
{film}
<ul>{links}</ul>
{extra}
<p class="note">{privacy}</p>
</main></html>""".encode()


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
        {"title": "The warning", "summary": "consumer.ftc.gov: Don't open your door to grandparent scams", "tone": "caution",
         "url": "https://consumer.ftc.gov/consumer-alerts/2021/04/dont-open-your-door-grandparent-scams"},
        {"title": "Why it matches", "summary": "NVIDIA Nemotron 3 Ultra compared them: the same trick, not just the same topic.",
         "tone": "caution"}], how={"calls": ["search"], "depth": "advanced", "seconds": 3.1, "credits": 2},
        lead="Don't reply, pay or give any details. Check with family first.")


def keys() -> None:
    """A place the person had Andy keep, looked at first (PLAN B46)."""
    board.show("seen", "Your house keys", [{"summary": "on the hall table, by the lamp"}])


def note() -> None:
    board.show("note", "A note from Anna", [{"summary": "I'll call you at six tonight. Love, Anna", "when": "5:42 pm"}])


def coming_saturdays(today: date) -> tuple:
    """This Saturday (never a first Saturday, when the sample market would be on) and the next first Saturday."""
    from datetime import timedelta

    sat = today + timedelta(days=(5 - today.weekday()) % 7)
    if sat.day <= 7:
        sat += timedelta(days=7)
    first = (sat.replace(day=1) + timedelta(days=32)).replace(day=1)
    first += timedelta(days=(5 - first.weekday()) % 7)
    return sat, first


def spoken(d: date) -> str:
    return f"{d:%B} {d.day}"


def research() -> None:
    saturday, first_saturday = coming_saturdays(date.today())
    board.show("research", "Is the farmers market on this Saturday?", [
        {"title": f"Not this Saturday, {spoken(saturday)}"}, {"title": "First Saturday of each month, 9 am to noon"},
        {"title": f"Next market: Saturday, {spoken(first_saturday)}"},
        {"title": "Sources", "summary": "the market's own page (sample)"}],
        how={"calls": ["research"], "depth": "mini", "seconds": 23.4, "credits": None, "sites": 9})


# What the head is turned to in each scene, as the behaviours would say on the robot (body/looking_at.py).
LOOKING = {"research": "screen", "found": "pointing", "keys": "remembered"}


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
    if {"-h", "--help"} & set(sys.argv[1:]):     # the description, and nothing else run
        print(__doc__)
        return 0
    if __name__ != "__main__" or board.TOKENS.parent.resolve() != DATA.resolve() or not DATA.name.startswith("andy-demo-"):
        print("Run demo_screen.py as its own process; imported demos must never seed a household store.", file=sys.stderr)
        if __name__ == "__main__":
            shutil.rmtree(DATA, ignore_errors=True)  # only the new folder made by this script above
        return 2
    import signal

    # A kill (SIGTERM) cleans up like Ctrl+C, so the throwaway folder never stays behind.
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    board._write(board.TOKENS, {"screen": "demo-screen", "family": "demo-family", "setup": "demo-setup", "hood": "demo-hood"})
    state.awake()
    settings.update(place="Miami, Florida", night_from=23, night_to=6)
    if PUBLIC:            # visitors come at any hour, from anywhere: never only a clock
        settings.update(night_clock="off")
        screen_server.READ_ONLY = True
        # The Space's page shows the demo in a frame; Andy's own server lets no page frame it.
        screen_server.HEADERS["Content-Security-Policy"] = screen_server.HEADERS["Content-Security-Policy"].replace(
            "frame-ancestors 'none'", "frame-ancestors https://huggingface.co")
    for film in (Path(__file__).resolve().parents[1] / "docs/images/sim-search.mp4", Path("sim-search.mp4")):
        if film.is_file():           # in the repository, or beside the Space's Dockerfile
            screen_server.MEDIA["/media/sim-search.mp4"] = (film.read_bytes(), "video/mp4")
            break
    screen_server.INDEX = index_page()
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
    server = screen_server.serve(host="0.0.0.0" if PUBLIC else "127.0.0.1", port=PORT)
    base = f"http://127.0.0.1:{server.server_port}"
    print(f"Start here:                          {base}/" + (" (public: read-only)" if PUBLIC else ""))
    print(f"Andy's screen (open it full screen): {base}/screen?t=demo-screen")
    print(f"The family page:                     {base}/family?k=demo-family")
    print(f"The settings page:                   {base}/setup?s=demo-setup")
    print(f"Under the hood:                      {base}/hood?t=demo-hood")
    print("Sample data only; Ctrl+C to stop.", flush=True)
    scenes = [("research", research), ("searching", board.start_search), ("found", found), ("letter", letter), ("scam", scam), ("today", dayplan.show),
              ("note", note), ("keys", keys), ("story", lambda: stories.start("lion")),
              ("quiet", board.clear_screen)]
    import signal

    def stop(*_):
        raise KeyboardInterrupt

    # Stopped from outside (a Space restarting, `kill`) as with Ctrl+C: the throwaway folder is deleted either way.
    signal.signal(signal.SIGTERM, stop)
    # ANDY_DEMO_SCENE=found (or any name above) holds that one scene: for screenshots and for filming the screen.
    hold = os.environ.get("ANDY_DEMO_SCENE", "")
    if hold:
        scenes = [sc for sc in scenes if sc[0] == hold] or scenes
    try:
        i = 0
        while True:
            name, show = scenes[i % len(scenes)]
            scene_value = show()
            started = time.time()
            while time.time() - started < 20:
                if name == "searching":           # invented progress only; this demo never opens a camera
                    elapsed = time.time() - started
                    stage = "scanning" if elapsed < 10 else "reading" if elapsed < 15 else "closer"
                    board.search_step(scene_value, stage, min(4, int(elapsed / 2)))
                    screen_server.set_live({"state": "working", "tool": "find_object", "looking": "room" if stage == "scanning" else "closer" if stage == "closer" else ""})
                    screen_server.set_caption("", now=0)
                elif name == "quiet":                # nothing showing, Andy waiting: the screen suggests what to ask
                    # ... after waving back at someone who waved as they came in (PLAN B49), for a few seconds.
                    waved = time.time() - started < 4
                    screen_server.set_live({"state": "ready", "tool": "", **({"looking": "wave"} if waved else {})})
                    screen_server.set_caption("", now=0)
                else:
                    screen_server.set_live({"state": "speaking", "tool": "", "looking": LOOKING.get(name, "you")})
                    screen_server.set_caption(today_caption() if name == "today" else CAPTIONS[name])
                time.sleep(1)
            i += 1
    except KeyboardInterrupt:
        return 0
    finally:
        if DATA.name.startswith("andy-demo-"):       # only the folder this demo made, never one it was given
            shutil.rmtree(DATA, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

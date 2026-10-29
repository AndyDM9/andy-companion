"""Get Andy ready to film the demo video (docs/video.md), and tidy up after.

    uv run python scripts/prepare_demo.py check                  what to fix before filming
    uv run python scripts/prepare_demo.py letters [folder]       printable letters, every name made up
    uv run python scripts/prepare_demo.py set --reminder-in 4    the reminder for the long take, and yesterday's moment
    uv run python scripts/prepare_demo.py clean                  remove what `set` added

`set` writes straight into Andy's own store (the founder's own home, for the video): a reminder "call Rosa"
due in a few minutes, and a moment from yesterday, "Sofia's piano recital", so Andy can ask how it went.
`clean` removes exactly those two, by their ids. The letters are HTML pages to print from a browser; the
sender, company, phone number (a 555 number) and amounts are invented, so no real company or agency is on
camera (the rules forbid third-party trademarks without permission).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from andy_companion import board, moments, reminders, settings  # noqa: E402
from andy_companion.reminders import DATA_DIR  # noqa: E402

DEMO = DATA_DIR / "demo.json"

LETTER_CSS = ("body{font:18px Georgia,serif;max-width:640px;margin:48px auto;color:#111}h1{font-size:26px}"
              ".from{font:700 20px Arial,sans-serif;letter-spacing:.02em}.big{font-size:28px;font-weight:700}"
              ".small{font-size:13px;color:#555}@media print{body{margin:24px auto}}")
LETTERS = {
    "prize-letter.html": f"""<!doctype html><meta charset="utf-8"><title>Prize letter (made up)</title><style>{LETTER_CSS}</style>
<p class="from">GRAND PRIZE RELEASE CENTER</p>
<p>FINAL NOTICE</p>
<h1>Congratulations! You have WON $25,000!</h1>
<p>Our records show you were selected in this year's national sweepstakes. To release your prize you must
pay a <b>processing fee of $500 within 24 hours</b>, using gift cards from any store.</p>
<p class="big">Call (305) 555-0142 now. Do not tell anyone until your prize is released.</p>
<p>Prize Release Department</p>
<p class="small">Made up for a demonstration: this organisation, number and prize do not exist.</p>""",
    "electric-bill.html": f"""<!doctype html><meta charset="utf-8"><title>Electric bill (made up)</title><style>{LETTER_CSS}</style>
<p class="from">SUNSHINE COAST ELECTRIC</p>
<p>Account 0000-1234</p>
<h1>Your bill for September</h1>
<p>Amount due: <span class="big">$86.40</span></p>
<p>Due date: <b>November 20, 2026</b></p>
<p>Pay online, by phone or by mail, as usual. Thank you for being a customer.</p>
<p class="small">Made up for a demonstration: this company and account do not exist.</p>""",
}


def check() -> int:
    from andy_companion import app_mode

    app_mode.load_env(("ANDY_VISION", "ANDY_VISION_URL", "TAVILY_API_KEY", "NEBIUS_API_KEY"))   # names only; never printed
    s = settings.get()
    now = datetime.now()
    from andy_companion import screen_server
    problems, notes = [], []
    if screen_server.night_now(s, now.hour):
        problems.append(f"The night clock is on now ({s.get('night_clock', 'hours')}): film in the day, or set "
                        "\"The night clock\" to Never on the settings page.")
    if not s.get("captions", True):
        problems.append("Captions are off: turn them on for the planned accessible video. "
                        "Any non-English segment needs an English translation under the rules.")
    if s.get("tv_yaw") is None:
        problems.append("The screen's place isn't set, so Andy won't glance at it: settings page, \"Where the screen is\".")
    if not s.get("place"):
        problems.append("No town set: the weather and what's on need it.")
    if s.get("language") != "en":
        notes.append("The language is Spanish; the video's long take is in English.")
    if os.environ.get("ANDY_VISION", "").strip().lower() == "endpoint" and not os.environ.get("ANDY_VISION_URL"):
        notes.append("No vision endpoint in this shell's environment: start it 25 minutes before (cloud/vision-endpoint.sh start).")
    photos = len(list((DATA_DIR / "photos").glob("*.jpg"))) if (DATA_DIR / "photos").is_dir() else 0
    notes.append(f"{photos} family photo(s) kept; use your own, with the family's agreement, not the sample landscapes.")
    if board.showing():
        notes.append("A card is on the screen now; it clears in five minutes.")
    for p in problems:
        print("✗", p)
    for n in notes:
        print("•", n)
    print("Then: robot/.venv/bin/python scripts/doctor.py --live, until preflight passes; verify spoken tasks and motion before filming.")
    return 1 if problems else 0


def write_letters(folder: Path) -> int:
    folder.mkdir(parents=True, exist_ok=True)
    for name, page in LETTERS.items():
        (folder / name).write_text(page)
        print(f"Print: {folder / name}")
    return 0


def set_up(reminder_in: float) -> int:
    added = json.loads(DEMO.read_text()) if DEMO.exists() else {}
    if added:
        print("Already set up; run `clean` first.")
        return 1
    reminder = reminders.add("call Rosa", minutes=reminder_in)
    moment = moments.add("Sofia's piano recital", (date.today() - timedelta(days=1)).isoformat())
    DEMO.write_text(json.dumps({"reminder": reminder["id"], "moment": moment["id"]}))
    os.chmod(DEMO, 0o600)
    print(f"A reminder \"call Rosa\" due at {datetime.fromtimestamp(reminder['due']):%H:%M}, and yesterday's "
          "\"Sofia's piano recital\". After filming: clean.")
    return 0


def clean() -> int:
    if not DEMO.exists():
        print("Nothing to clean.")
        return 0
    added = json.loads(DEMO.read_text())
    reminders.cancel(added.get("reminder", ""))
    moments.remove(added.get("moment", ""))
    DEMO.unlink()
    print("Removed the demo reminder and moment.")
    return 0


def main(argv=None) -> int:
    if {"-h", "--help"} & set((sys.argv[1:] if argv is None else argv)):     # the description, and nothing else run
        print(__doc__)
        return 0
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("check", "letters", "set", "clean"):
        print(__doc__)
        return 2
    if args[0] == "check":
        return check()
    if args[0] == "letters":
        return write_letters(Path(args[1]) if len(args) > 1 else Path.home() / "andy-demo-letters")
    if args[0] == "set":
        minutes = float(args[args.index("--reminder-in") + 1]) if "--reminder-in" in args else 4.0
        return set_up(minutes)
    return clean()


if __name__ == "__main__":
    raise SystemExit(main())

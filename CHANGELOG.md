# Changelog

Every change, newest first, grouped by date. Each entry says what changed and why. The plan is in
[docs/PLAN.md](docs/PLAN.md) and progress in [docs/STATUS.md](docs/STATUS.md).

## 2026-10-13

### Added (M2, privacy floor)

- **No conversation text in any log**: `privacy.py` redacts every log record Pollen's app
  creates, at creation: spoken turns are dropped, tool arguments and tool errors become
  `[not logged]`, remembered facts are never logged; tool names, timings and error types stay.
  `voice/serve.py` starts speech-to-speech with its one unconditional transcript print
  (Qwen3-TTS "ASSISTANT: ...") silenced. Verified on the robot: 0 conversation lines.
- **Andy's own memory store**: Pollen's remember/forget now keep facts in
  `~/.local/share/andy-companion/memory.json` (owner-only), not inside the installed package
  where another app on the robot would share them. 12 new tests.
- `docs/feedback-notes.md`: what we meet with Nebius, NVIDIA and the tools, for the mandatory
  Devpost feedback (and the Most Valuable Feedback prize).
- PLAN.md M6: "Andy, read this letter for me" (Tesseract on the computer, explained by
  Nemotron, with a Tavily scam lookup).

### Added (M3, body behaviours)

- **Sleep, quiet, wake, and reminders that are never missed**: `scripts/andy` runs Andy under
  `supervisor.py`. "Goodnight" (Pollen's `go_to_sleep`) puts Andy to sleep; the new `quiet_for`
  tool rests it for 1 minute to a day. While asleep or quiet the supervisor listens offline with
  Vosk for a few wake phrases only ("Andy, wake up", "good morning Andy"), and **wakes Andy by
  itself when a reminder comes due or the quiet time ends**. `chimes.py` plays a soft cue
  before each reminder and on waking and sleeping. `state.py` keeps awake/asleep/quiet in an
  owner-only file. 17 new tests.
- **Andy keeps looking at the person**: `src/andy_companion/body/` brings over the earlier
  assistant's general-purpose body modules, rewritten without private links: `gaze` (keeps
  following the face while Andy speaks, which Pollen's app pauses; softens upward looks),
  `body_follow` (turns the body to face the person), `seek` (turns to the voice's direction,
  looks around once when the face is lost), `person` (finds a person whose face is turned away,
  with YOLOX on the CPU; frames are looked at and dropped), `idle` (calm moments in place of
  Pollen's random dances and emotions), `speaking`, and `presence` (now one timestamp in memory,
  never on disk). `body/attach.py` wraps Pollen's single movement send point; any failure falls
  back to Pollen's own command. The phone-watch and focus-session parts stay behind. 57 body
  tests come with them (82 in all; 5 need Pollen's app and skip without it).

### Changed

- **No confirmation moves, face tracking from the start**: in the reminder test Andy confirmed
  with a `dance` nod and an emotion and moved its head hard. The profile now keeps only
  `head_tracking` of the movement tools, says to confirm in words only, and turns tracking on
  before greeting. Andy now runs with the camera on for tracking only; the `camera` tool is not
  given to the model, so no picture leaves the computer.
- **Decisions 0002 and 0003**: Tavily is the only web provider (in place of Brave, Firecrawl and
  Perplexity); what this public repository holds and never holds (no keys, memories, logs,
  private projects, or face identification). PLAN.md: M3 and M7 widened (looking at the person
  while speaking; Andy's screen beside the family page).

### Added

- **Clock and reminders (M1)**: `get_today` gives the day, date and time so Andy never guesses
  (it said "morning" at 12:50 before; now "Good afternoon"); `set_reminder`, `list_reminders`
  and `cancel_reminder` keep one-off or daily reminders in Andy's own owner-only store
  (`~/.local/share/andy-companion/`); `speaker.py` says a due reminder unprompted once the
  conversation is settled and idle, framed as data, and logs no reminder text.
  `scripts/run_andy.py` starts Pollen's app with the speaker attached. 25 tests.
- **The plan and the record**: `docs/PLAN.md` (goal, judging criteria, milestones M0–M10, the
  video, our words, risks), `docs/STATUS.md`, this changelog, `docs/decisions/`,
  `docs/submission-checklist.md`, `docs/architecture.md` and `CLAUDE.md`, so every change keeps
  the record current.
- **Andy talks through NVIDIA Nemotron on Nebius (M0)**: `voice/` runs speech-to-speech 1.0.0
  with NVIDIA Parakeet and Nemotron 3.5 Lightning on Token Factory; `profiles/companion/` is the
  companion's profile for Pollen's conversation app; `scripts/run-robot.sh` and `voice/run.sh`
  read keys from outside the repository. Tested on a Reachy Mini Lite: replies in 0.62–0.83 s.

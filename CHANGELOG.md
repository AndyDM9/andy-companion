# Changelog

Every change, newest first, grouped by date. Each entry says what changed and why. The plan is in
[docs/PLAN.md](docs/PLAN.md) and progress in [docs/STATUS.md](docs/STATUS.md).

## 2026-10-13

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

# Changelog

Every change, newest first, grouped by date. Each entry says what changed and why. The plan is in
[docs/PLAN.md](docs/PLAN.md) and progress in [docs/STATUS.md](docs/STATUS.md).

## 2026-10-13

### Added

- **The plan and the record**: `docs/PLAN.md` (goal, judging criteria, milestones M0–M10, the
  video, our words, risks), `docs/STATUS.md`, this changelog, `docs/decisions/`,
  `docs/submission-checklist.md`, `docs/architecture.md` and `CLAUDE.md`, so every change keeps
  the record current.
- **Andy talks through NVIDIA Nemotron on Nebius (M0)**: `voice/` runs speech-to-speech 1.0.0
  with NVIDIA Parakeet and Nemotron 3.5 Lightning on Token Factory; `profiles/companion/` is the
  companion's profile for Pollen's conversation app; `scripts/run-robot.sh` and `voice/run.sh`
  read keys from outside the repository. Tested on a Reachy Mini Lite: replies in 0.62–0.83 s.

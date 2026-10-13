# Andy Companion — notes for Claude Code

Read [docs/PLAN.md](docs/PLAN.md) and [docs/STATUS.md](docs/STATUS.md) first.

## Keep the record current, in the same commit

Every change updates:
1. **CHANGELOG.md:** a dated entry saying what changed and why.
2. **docs/STATUS.md:** the milestone's state, any new measurement, and any new open problem.
3. **docs/submission-checklist.md:** tick an item only when the change makes it true.
4. **docs/architecture.md:** whenever a part, a data flow or a boundary changes.

A choice between real alternatives gets a short record in `docs/decisions/` (copy `0001`, number
sequentially). A milestone is done only when its "done when" in PLAN.md is true.

## Rules

- **No keys in the repository.** Keys live in `~/.config/companion-hackathon/.env` (mode 600).
- **No conversation text in logs, files or crash reports.** The only exception is what the person explicitly asks Andy to remember, and the reminders they set, kept in Andy's own store.
- **Andy says it is a robot, and never speaks as or imitates a real person.**
- **No medicine doses or medical advice.** Andy never asks for money or passwords.
- **Public words follow PLAN.md "Words we use".** No condition names; no safety, monitoring or outcome claims; never "seniors" or "elderly".
- **Tests come with every tool.** `uv run pytest` must pass before a commit; the pre-commit hook
  enforces it (`git config core.hooksPath .githooks` once per clone).
- **Only one program drives the robot at a time.** A test that runs Andy stops the other app first, and says so.
- **This repository will be public.** Write nothing here about any company, brand plan or person that is not meant for the public.

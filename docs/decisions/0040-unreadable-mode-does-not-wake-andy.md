# 0040: Unreadable saved mode does not automatically wake Andy

**Date:** 2026-10-27. **Status:** accepted.

## Context

An invented `state.json` containing `[]` raised AttributeError in the reader. A quiet deadline stored
as text raised TypeError in the supervisor. Wrong timestamps or reminder-return fields could also
break the screen or post-reminder flow. Broken JSON previously defaulted to awake, despite losing
the person's intended quiet/sleep state.
The dashboard's app-start path also left a previous asleep/quiet mode in place while starting the
app, so the screen/health status could describe a running app as asleep.

## Options

1. Catch failures and always return awake.
2. Discard damaged control data and restore an assumed previous mode.
3. Preserve the existing file, expose an unreadable flag and pause automatic wakes until an explicit
   wake or mode change writes a valid state.

## Decision

Choose option 3. A missing file retains the first-run awake default. An existing unreadable file
returns asleep/unreadable without being rewritten or copied. Validate known top-level and one-level
reminder-return fields, supported modes, representable finite timestamps and reminder-ID lists.
Legacy awake/asleep files may omit optional fields; valid reads do not rewrite them.

Under the desktop supervisor, unreadable state blocks deadline/reminder automatic wakes, including
a stale reason obtained just before corruption. The running app stops through the existing callback/process-control
path. A crash or watchdog request cannot cause an automatic restart while the mode remains unreadable;
no sleep chime is forced on this path. The offline wake listener uses explicit wake-up triggers,
including the existing Spanish triggers, rather than the broader asleep greeting triggers.

An explicit wake phrase or normal mode change writes fresh valid control metadata and resumes normal
behavior. Log one fixed warning per observed file revision, with no file contents or raw exception.
The health tile and live preflight identify the unreadable mode. The screen strip remains renderable.
No recovery copy is created: this is transient control state, not a personal memory/settings store.
Dashboard app startup is a separate start intent: `app_mode.install(screen=True)` writes a valid
awake state, including when previous mode data was stale or unreadable. Supervised installation
leaves the supervisor's saved mode untouched. This aligns the status with the dashboard lifecycle;
it does not add a dashboard wake listener or enforce supervisor quiet scheduling there.

Validate direct duration/deadline/return-state writes before touching disk. Serialize writers with the
existing file lock; owner-only temporary files replace the state atomically, with cleanup after failure.
The valid household file is checked read-only before deployment; its bytes must remain unchanged.

## Why

Choosing awake after losing the quiet/sleep instruction can make Andy speak unexpectedly. Waiting
for explicit intent preserves that boundary and avoids a crash/restart loop. Keeping the original
until the intended mode change permits review without creating an additional retained copy.

## Consequences

Automatic reminders and expired-quiet wakes pause while the file is unreadable; they resume after a
valid mode change. This can delay reminders and is visible in diagnostics. If the offline wake
recognizer or file writes are unavailable, owner intervention is needed. Unknown fields in a future
mode format require a deliberate schema update. This is not general store recovery, power-loss
durability, physical voice verification or a new model/tool capability. No reminder or household
memory is deleted. Other stores retain their documented scope.
The dashboard app retains its manual start/stop lifecycle; it has no supervisor wake listener.

## Revisit when

- The mode format gains new fields or needs a supported recovery workflow.
- The project can establish a previous valid user mode without guessing.

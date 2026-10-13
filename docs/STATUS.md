# Status

**Last updated 2026-10-13.** Update this file in the same commit as any change it describes.
The plan and its milestones are in [PLAN.md](PLAN.md).

## At a glance

| # | Milestone | State | Notes |
|---|---|---|---|
| M0 | Andy talks through Nemotron | ✅ Done 2026-10-13 | Measured below |
| M1 | Clock and reminders | ✅ Done 2026-10-13 | Verified on the robot: "Good afternoon" from the clock; a reminder set by voice, listed, and said unprompted when due |
| M2 | Privacy floor | ⏳ Next | Found in the M0 test: both programs log conversation text; Pollen's `remember` writes inside its installed package |
| M3 | Body behaviours | 🔨 In progress | Done: face tracking from the greeting; no confirmation moves; looking at the person while speaking (gaze, verified in the log); body follow; seek by voice direction and look-around; person finder (YOLOX, frames never stored); calm idle moments; upward looks softened. 82 tests. Built 2026-10-13, awaiting the live test: chimes (a soft cue before each reminder, on waking and on sleep), quiet_for ("be quiet for an hour"), the offline wake phrase, and the supervisor that wakes Andy for a due reminder even while asleep or quiet. 99 tests |
| M4 | The day, the same way every time | ⏳ | |
| M5 | Tavily | ⏳ | Account and key ready; search tested |
| M6 | Eyes | ⏳ | |
| M7 | Family page | ⏳ | |
| M8 | Proof | ⏳ | |
| M9 | Ship | ⏳ | Repository private until then |
| M10 | Video and submission | ⏳ | Registered on Devpost 2026-10-13 |

## Accounts and keys

| What | State |
|---|---|
| Devpost registration | ✅ 2026-10-13 |
| Nebius Token Factory | ✅ Individual account, zero data retention on, key in `~/.config/companion-hackathon/.env` |
| Nebius Builder Program | Applied 2026-10-13; email verification pending |
| Hackathon Token Factory credit | Form sent 2026-10-13; code arrives by email |
| Tavily | ✅ Free plan, key saved and tested |

## Measurements

| Date | What | Result |
|---|---|---|
| 2026-10-13 | Lightning tool call by API (`set_reminder`) | Correct arguments, 0.63–0.76 s, no reasoning text |
| 2026-10-13 | Reminder test on the robot | Set by voice, listed, said unprompted when due. Andy also chose a `dance` nod and an emotion to confirm, which moved the head hard: movement tools removed from the profile |
| 2026-10-13 | On the Reachy Mini Lite, 9 spoken turns | Parakeet 0.02–0.08 s; Lightning 0.62–0.83 s; first audio 0.10–0.33 s; no errors; interruptions handled; nod, remember and forget worked |

## Open problems


- Conversation text appears in INFO logs of both the voice server and the app. (M2)
- Pollen's `remember` stores `memory.v1.json` inside its installed package. (M2)

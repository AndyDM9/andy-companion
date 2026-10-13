# Status

**Last updated 2026-10-13.** Update this file in the same commit as any change it describes.
The plan and its milestones are in [PLAN.md](PLAN.md).

## At a glance

| # | Milestone | State | Notes |
|---|---|---|---|
| M0 | Andy talks through Nemotron | ✅ Done 2026-10-13 | Measured below |
| M1 | Clock and reminders | ✅ Done 2026-10-13 | Verified on the robot: "Good afternoon" from the clock; a reminder set by voice, listed, and said unprompted when due |
| M2 | Privacy floor | ✅ Done 2026-10-13 | Verified live: 0 conversation lines in the app log, tool arguments `[not logged]`, 0 transcript prints from the voice server; remember/forget write Andy's own owner-only `memory.json`. Tests: `tests/test_privacy.py` |
| M3 | Body behaviours | ✅ Done 2026-10-13 | Verified by the founder on the robot: looking at the person while speaking, following when they move; sleep, quiet and wake; a due reminder wakes Andy |
| M4 | The day, the same way every time | ✅ Done 2026-10-13 | Verified on the robot: today's plan, slow pace and louder volume remembered, exact spoken controls |
| M5 | Tavily | 🔨 Built, awaiting the live test | `local_news` (chosen local papers first, source named), `look_up`, `whats_on` (the city's calendar page, then a dated search), `read_link`, `check_message` (consumer-protection sites only; numbers, links and emails never sent). Live: news 5.9 s, look-up 1.4 s, events 3.3 s, link 0.2 s, scam check found FTC and AARP warnings. 140 tests |
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
| 2026-10-13 | Tavily calls, live | Local news 5.9 s (2 from wlrn.org); look-up 1.4 s; what's on 3.3 s; read a link 0.2 s; grandparent-scam message: 3 FTC and 1 AARP warnings. `safe_search` needs `basic` depth |
| 2026-10-13 | Reminder test on the robot | Set by voice, listed, said unprompted when due. Andy also chose a `dance` nod and an emotion to confirm, which moved the head hard: movement tools removed from the profile |
| 2026-10-13 | On the Reachy Mini Lite, 9 spoken turns | Parakeet 0.02–0.08 s; Lightning 0.62–0.83 s; first audio 0.10–0.33 s; no errors; interruptions handled; nod, remember and forget worked |

## Open problems


- None open.

# Plan

**Goal:** win the Physical AI track of the Nebius x NVIDIA Global AI Hackathon, and Best Use of
Tavily, with a companion robot that a judge would want in their own parent's home.

**Deadline:** submissions close **2026-10-30, 10:00 PT**. We submit by **2026-10-27**.

**One sentence:** Andy is a small home robot for older adults who live at home, and the family
who help. It runs on a Reachy Mini, its brain is NVIDIA Nemotron on Nebius, and it keeps nothing
it hears.

Live progress is in [STATUS.md](STATUS.md). Every change is in [CHANGELOG.md](../CHANGELOG.md).
Decisions are in [decisions/](decisions/). What Devpost requires is in
[submission-checklist.md](submission-checklist.md).

## How we are judged, and what answers each criterion

Stage one is pass/fail: a genuine Physical AI project that really uses Nebius and an NVIDIA open
model. Stage two scores four criteria, equally weighted, 1 to 5.

| Criterion | What answers it |
|---|---|
| Technological implementation | Three or more NVIDIA models across three Nebius products (Token Factory, a Serverless Endpoint, a Serverless Job); sub-second replies measured on screen; tested tools; a safety layer between the model and the body |
| Design ("a complete product, not a proof of concept") | The person's side (voice and robot) **and** the family's side (a phone page); setup in a few commands; a published Reachy Mini app |
| Potential impact | A real person and a real problem: older adults living at home, and the family who help. Honest wording, nothing claimed that is not measured |
| Quality of the idea | A companion that says it is a robot, never imitates a person, never stores what it hears, and lets the person decide what family sees |

## Milestones

Each milestone is done only when its "done when" is true and STATUS.md and CHANGELOG.md say so.

| # | Milestone | Done when | Target |
|---|---|---|---|
| M0 | **Andy talks through Nemotron** | Voice server with Parakeet and Nemotron Lightning; Andy answers on the robot | 2026-10-13 ✅ |
| M1 | **Clock and reminders** | Andy knows the date and time; sets, lists and cancels reminders by voice; speaks a reminder when it is due, unprompted; tests pass | 2026-10-15 |
| M2 | **Privacy floor** | No conversation text in any log; Andy's memory in its own store; nothing stored except what the person asks | 2026-10-16 |
| M3 | **Body behaviours** | Andy keeps looking at the person while it speaks and while they move (gaze, body follow, seek, person finder), gentle idle moments, no confirmation moves, upward looks softened; chimes, quiet mode, wake word; each rewritten here from the earlier assistant's general-purpose modules, with tests | 2026-10-18 |
| M4 | **The day, the same way every time** | A day plan said on request and each morning; pace and volume settings that stick | 2026-10-19 |
| M5 | **Tavily** | Local news with sources named aloud; read a link a relative sends; what's on this week; look up a suspicious message; Tavily is the only web provider ([0002](decisions/0002-one-search-provider-tavily.md)) | 2026-10-20 |
| M6 | **Eyes** | A Nemotron vision model on a Nebius Serverless Endpoint describes the camera picture | 2026-10-21 |
| M7 | **Andy's screen and the family page** | A screen beside Andy (TV or monitor) shows what Andy is talking about: the day, reminders, news with its source, a picture; and a phone page for family showing only what the person chose to share, with Andy saying who looked | 2026-10-22 |
| M8 | **Proof** | A conversation test suite run as a Nebius Serverless Job, judged by Nemotron Ultra; scorecard in the README | 2026-10-23 |
| M9 | **Ship** | README with setup, architecture diagram, published Reachy Mini app, repository public | 2026-10-24 |
| M10 | **Video and submission** | Under three minutes, at least one minute of the robot live; Devpost form complete with the tool feedback | 2026-10-27 |

## The video (draft)

1. Morning: Andy wakes, greets, says the day and one local headline with its source.
2. A reminder Andy speaks on its own at the chosen time.
3. Andy remembers yesterday's mention of a granddaughter's recital and offers to send a note to
   the family, if the person wants.
4. A suspicious text, looked up together, and "shall we ask your daughter?"
5. Boundaries: asked to be someone else, or for a medicine dose, it kindly declines.
6. Under the hood: the NVIDIA models and Nebius products named aloud, timings on screen.

## Words we use, and words we never use

We describe people by age and living situation: "older adults who live at home, and the family
who help". We never name a medical condition. We never say Andy keeps anyone safe, watches over
anyone, notices changes in a person, reduces loneliness, replaces a visit or a carer, or makes
sure anyone takes medicine. We never call people "seniors" or "the elderly". We show what Andy
does; we do not claim outcomes we have not measured.

## Risks

| Risk | What we do |
|---|---|
| Lightning's tool calls are weak on a hard turn | Fall back to Nemotron Super for that turn |
| Reasoning text spoken aloud | Thinking off; strip it in our wrapper if it ever appears |
| No NVIDIA vision model on serverless Token Factory | Self-host one on a Nebius Serverless Endpoint (M6) |
| The robot is shared with another app | Only one program drives the robot at a time; tests stop the other |
| Time | Milestones are in order of what the video needs; M6 and M8 can shrink without breaking the demo |

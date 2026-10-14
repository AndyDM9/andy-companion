# How this entry meets the hackathon's Official Rules

The rules: <https://nebiusglobalaihackathon.devpost.com/rules> (read in full and checked against the
live page on 2026-10-13). They can be amended at any time and the live page prevails, so **re-read
it before submitting** and update this file. Everything that touches the submission (the README, the
video, the Devpost form, the repository) is checked against this file first.

**Status key:** ✅ met · 🔶 in progress · ⬜ to do · ➖ does not apply.

## Dates

| What | When | Our plan |
|---|---|---|
| Submission period | 2026-08-26 09:00 PT to **2026-10-30 10:00 PT** | Submit by **2026-10-27**; the project started 2026-10-13, inside the period |
| Judging | 2026-12-01 to 2026-12-15 | Keep the repository, the robot and the README working through 2026-12-15 |
| Winners | About 2027-01-11 | A winner's forms are due 10 business days after they are sent (W-9 for a US resident) |

## Eligibility and prizes

| Rule | Status | Notes |
|---|---|---|
| Entrant is an individual of age, not in an excluded place, not with a sponsor, Devpost or a judge's employer, no conflict of interest | ✅ | The founder enters as an individual (US resident); a company that does not yet exist may not enter, so the founder's company does not |
| No financial or preferential support from the sponsor | ✅ | Only the credits open to every entrant (Builder Program, hackathon promotion); no funding, contract or commercial licence from Nebius or Devpost |
| One Overall Award, **or** one Track Award plus one Bonus Award | ✅ | Aim: Physical AI track (or an Overall Award) plus Best Use of Tavily |
| Best Use of Tavily: a functional runtime call to the Tavily API | ✅ | Search, extract, crawl and research at runtime (`src/andy_companion/web.py`, `looking.py`) |
| City Winner Awards | ➖ | Only the 20 listed Builders & Brews cities; **Miami is not one of them** |
| Most Valuable Feedback: complete the feedback section | 🔶 | Notes kept as we build in [feedback-notes.md](feedback-notes.md); written up on the form |

## Project requirements

| Rule | Status | Evidence |
|---|---|---|
| A working application that runs on Nebius Token Factory or AI Cloud | ✅ | Every turn calls the Token Factory inference API (Nemotron 3.5 Lightning); AI Cloud runs two Serverless Endpoints (eyes, second look) and a Serverless Job (the suite) |
| Uses at least one NVIDIA open model | ✅ | Parakeet TDT 0.6B v3, Nemotron 3.5 Lightning, Nemotron Nano 12B v2 VL, Nemotron 3.5 Content Safety, Nemotron 3 Ultra (judge) |
| Fits the Physical AI track: an embodied agent that senses and acts, coordinated through an agent runtime; Serverless Jobs for evaluation, Serverless Endpoints for real-time inference | ✅ | A Reachy Mini that hears, sees, follows a face, turns, speaks; Pollen's conversation app as the agent runtime; the suite as a Serverless Job; vision and content safety as Serverless Endpoints |
| Installs and runs consistently, and works as shown and described | 🔶 | Fresh-clone install checked 2026-10-13; `scripts/doctor.py`; the live test (`docs/live-test.md`) before filming; the video shows only what works |
| New, or significantly updated during the period, with an explanation | ✅ | Created 2026-10-13; the README's "Built during the hackathon" says what reuses the author's own earlier code (from 2026-10-05, also inside the period) |
| Authorised to use every third-party SDK, API and data | ✅ | The README's "Licences and credits" lists each with its terms and the attribution it requires |

## Submission requirements

| Rule | Status | Action, owner, date |
|---|---|---|
| Working demo URL | ➖ | Not required for Physical AI; judged on the video, the repository and, if asked, the hardware |
| Text description of features and functionality | 🔶 | Draft in [submission.md](submission.md); final by 2026-10-26 |
| **Public** repository on GitHub with all source, assets and instructions | ⬜ | Public after the name decision (founder, about 2026-10-20); go-public checklist in [submission-checklist.md](submission-checklist.md) |
| Open-source licence file, **visible in the repository's About section** | 🔶 | `LICENSE` is Apache-2.0 and GitHub detects it; check it shows in About once public |
| README with setup instructions and how to run it | ✅ | README "Setup" |
| README highlights the NVIDIA models, **where Token Factory accelerated the workflow**, and the other Nebius services | ✅ | README "How it uses NVIDIA and Nebius" and "Where Token Factory sped us up" |
| Video under three minutes | 🔶 | [video.md](video.md): 2:45 |
| Video shows the project working on its device; Physical AI: **at least one minute of the robot operating** | 🔶 | Shots 1, 3 to 8 are the robot live |
| Video public on YouTube, link on the form | ⬜ | Founder, 2026-10-26 |
| Video has **no third-party trademarks or copyrighted music or material** without permission | 🔶 | No music, or only music we own or licence for it; no third-party logos on screen; news and pages on the TV from public sources (the National Weather Service, the town's own site) rather than newspapers; **family photos of our own, with consent, not the sample landscapes**; Nebius, NVIDIA and Tavily are named because the rules ask for them |
| All materials in English, or with an English translation | 🔶 | The Spanish moment in the video gets **English subtitles** |
| Identify the track | ⬜ | Physical AI, on the form |
| Feedback on Token Factory, AI Cloud and the NVIDIA tools | 🔶 | From [feedback-notes.md](feedback-notes.md) |
| Original work, solely owned, no one else's rights infringed | ✅ | Our code; open source used under its licences and built upon (Pollen's app is extended, not copied); no the founder's company material |

## Testing and judging

| Rule | Status | Notes |
|---|---|---|
| Free access for testing until judging ends (2026-12-15) | 🔶 | The public repository with setup instructions; a judge brings their own Nebius and Tavily keys (`.env.example`) |
| Physical access to the hardware may be requested (the Reachy Mini is not a phone, tablet or computer) | 🔶 | Keep the robot and the desktop ready through 2026-12-15 |
| After the deadline the submission cannot change | ⬜ | Tag the submitted commit (`hackathon-submission`) and link that tag on the form; later work goes after it |

## Publicity, privacy and conduct

| Rule | Status | Notes |
|---|---|---|
| The sponsor and Devpost may use the entrants' name, likeness and voice for three years | ✅ | Accepted by entering; anyone else in the video agrees in writing first |
| No personal data in submission materials | 🔶 | No real addresses, phone numbers or private links in the video. **The settings code is a private link: after filming it, press "Make a new settings link".** Family photos only with the family's agreement |
| No harmful code | ✅ | Tests, a pre-commit check for keys, gitleaks over the history |

## Kept current

This file changes in the same commit as anything it describes. Last full check: 2026-10-13.

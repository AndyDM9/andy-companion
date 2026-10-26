# How this entry meets the hackathon's Official Rules

The rules: <https://nebiusglobalaihackathon.devpost.com/rules> (read in full and checked against the
live page on 2026-10-13, again on 2026-10-20, and in full on 2026-10-25: the rules and dates unchanged; the only
new update was the judges' advice from that session, checked against the entry below). They can be amended at any time and the live page prevails, so **re-read
it before submitting** and update this file. Everything that touches the submission (the README, the
video, the Devpost form, the repository) is checked against this file first.

**Status key:** ✅ met · 🔶 in progress · ⬜ to do · ➖ does not apply.

## The judges' advice (update of about 2026-10-21, "Will It Ship?")

| Advice | How the entry meets it |
|---|---|
| Solve a real problem for a real audience; talk to a few potential users | The problem, sourced (FTC, AARP, a 2026 systematic review of what older adults want). No study with older adults yet, said plainly in Limitations; talking with a few before submitting is on the founder's list |
| The aha moment fast: two minutes in the project, 30 s in the demo | The video opens on the letter and **Be careful** (0:00–0:24); the README's first screen has the three moments |
| One thing done well beats a big stack; every integration supports the main story | Every model and tool is named by the job it does for the person ("every model, and where it runs") |
| Put the action first, a little onboarding, show which model does what | The TV suggests what to ask ("Try asking"); the hood page names the model at each step, and is in the video's long take |
| Publish your limitations; call out accessibility | Limitations in the Devpost text and the README, with failure cases and scorecards; accessibility named in the Design point (2026-10-25) |
| Budget time for packaging | The draft is ready before filming; the video's shot list is written |

## Dates

| What | When | Our plan |
|---|---|---|
| Submission period | 2026-08-26 09:00 PT to **2026-10-30 10:00 PT** | A complete draft submitted by **2026-10-22**, so Devpost's free eligibility check (for entries in at least a week before the deadline, by 2026-10-23 10:00 PT) can flag anything missing; edits continue after, final by **2026-10-27**. The project started 2026-10-13, inside the period |
| Judging | 2026-12-01 to 2026-12-15 | Keep the repository, the robot and the README working through 2026-12-15 |
| Winners | About 2027-01-11 | A winner's forms are due 10 business days after they are sent (W-9 for a US resident) |

## Eligibility and prizes

| Rule | Status | Notes |
|---|---|---|
| Entrant is an individual of age, not in an excluded place, not with a sponsor, Devpost or a judge's employer, no conflict of interest | ✅ | The founder enters as an individual (US resident); no company enters |
| No financial or preferential support from the sponsor | ✅ | Only the credits open to every entrant (Builder Program, hackathon promotion); no funding, contract or commercial licence from Nebius or Devpost |
| One Overall Award, **or** one Track Award plus one Bonus Award | ✅ | Never both (section 8). The entry is in the Physical AI track and for Best Use of Tavily. Most Valuable Feedback is a Bonus Award too, so it and the Tavily prize can't both be won |
| Best Use of Tavily: a functional runtime call to the Tavily API | ✅ | Search, extract, crawl, map and research at runtime (`src/andy_companion/web.py`, `looking.py`); the scam check measured with and without it (2026-10-14) |
| City Winner Awards | ➖ | Only the 20 listed Builders & Brews cities; the founder's city is not one of them |
| Most Valuable Feedback: complete the feedback section | ✅ | [feedback.md](feedback.md), product by product, with first-hand findings to 2026-10-25; `scripts/devpost.py` prints it for the form |

## Project requirements

| Rule | Status | Evidence |
|---|---|---|
| A working application that runs on Nebius Token Factory or AI Cloud | ✅ | Every turn calls the Token Factory inference API (Nemotron 3.5 Lightning); the eyes are Nemotron 3.5 Super VL on Token Factory (2026-10-20); AI Cloud runs a Serverless Endpoint (the second look; Nano VL eyes as the option) and Serverless Jobs (the conversation suite; the scam evaluation, 2026-10-14; Andy's search in simulation, 2026-10-20) |
| Uses at least one NVIDIA open model | ✅ | Parakeet TDT 0.6B v3, Nemotron 3.5 Lightning, Nemotron 3.5 Super VL, Nemotron Nano 12B v2 VL (the option), Nemotron 3.5 Content Safety, Nemotron 3 Ultra (judge), Cosmos Reason 2 2B and 8B (the offline eyes, on this computer, 2026-10-25) |
| Fits the Physical AI track: an embodied agent that senses and acts, coordinated through an agent runtime; Serverless Jobs for evaluation, Serverless Endpoints for real-time inference | ✅ | A Reachy Mini that hears, sees, follows a face, turns, speaks; Pollen's conversation app as the agent runtime; Nebius Serverless Jobs for the suite, the scam evaluation and Andy's search in simulation; vision on Token Factory; content safety as a Serverless Endpoint (Nano VL eyes as an option) |
| Installs and runs consistently, and works as shown and described | 🔶 | Fresh-clone install checked 2026-10-13 and again from GitHub on 2026-10-14 (all three environments, the tests, the doctor, the keyless demo with an empty home folder); re-check before going public; `scripts/doctor.py`; the live test (`docs/live-test.md`) before filming; the video shows only what works |
| New, or significantly updated during the period, with an explanation | ✅ | Created 2026-10-13; the README's "Built during the hackathon" says what reuses the author's own earlier code (from 2026-10-05, also inside the period) |
| Authorised to use every third-party SDK, API and data | ✅ | [credits.md](credits.md) lists each with its terms and the attribution it requires, linked from the README's "Licences and credits" |

## Submission requirements

| Rule | Status | Action, owner, date |
|---|---|---|
| Working demo URL | ➖ | Not required for Physical AI; judged on the video, the repository and, if asked, the hardware. Even so, every project in the judging session had a link to click: the Hugging Face Space of the screens (the founder's) |
| Testing access, free, until judging ends; physical access to the hardware on request | 🔶 | Public sample preview and reproducible source are available. The author supplies the robot, computer and API access for free judge testing on request; optional own-key reproduction is separate. Final testing instructions and any organiser-requested hardware arrangement still need confirmation (decision 0022) |
| Text description of features and functionality | ✅ | [submission.md](submission.md), revised after a judge's-eye read (2026-10-25), and checked against the evening's fixes the same day (one claim corrected: the console filter alone had not kept every heard word out of the log); `scripts/devpost.py` prints the form's fields with every link checked |
| **Public** repository on GitHub with all source, assets and instructions | ✅ | Public since 2026-10-25, after the history rewrite (private matter out, gitleaks clean) and three best-practice reviews; secret scanning, push protection and private vulnerability reporting on |
| Open-source licence file, **visible in the repository's About section** | ✅ | `LICENSE` is Apache-2.0; GitHub shows it in About (checked logged out, 2026-10-25); the app's Space carries it too |
| README with setup instructions and how to run it | ✅ | README "Setup" |
| README highlights the NVIDIA models, **where Token Factory accelerated the workflow**, and the other Nebius services | ✅ | README "How it uses NVIDIA and Nebius" and "Where Token Factory sped us up" |
| Video under three minutes | 🔶 | [video.md](video.md): 2:56 as planned (retimed 2026-10-26); time a rough cut |
| Video shows the project working on its device; Physical AI: **"a 1-minute clip"** of the robot operating | 🔶 | One clip: shot 3, 72 s, one take, never cut; with shots 1, 4, 5 and 6 the robot is live about 2:05 ([video.md](video.md)) |
| Video public on YouTube, link on the form | ⬜ | Founder, 2026-10-27. **Public**, not unlisted; **"No, it's not made for kids"** (that setting makes a video hard for judges to reach); captions uploaded as SRT ([video.md](video.md)) |
| The project functions as depicted in the video | 🔶 | Robot shots are long unedited takes; no pause or lag is cut ([video.md](video.md)) |
| Video has **no third-party trademarks or copyrighted music or material** without permission | 🔶 | No music, or only music we own or licence for it; no third-party logos on screen; news and pages on the TV from public sources (the National Weather Service, the town's own site) rather than newspapers; **family photos of our own, with consent, not the sample landscapes**; Nebius, NVIDIA and Tavily are named because the rules ask for them |
| All materials in English, or with an English translation | 🔶 | Captions throughout; any Spanish gets **English subtitles** (Spanish moved to a social clip on 2026-10-14; `scripts/draft_captions.py` drafts the SRT and marks Spanish lines) |
| Identify the track | ✅ | Physical AI: chosen on the form, and in the Devpost text's first block, "For the judges", with a "Track fit" line naming Pollen's conversation app as the agent runtime; said on screen in the video's shot 7 |
| Sponsor names, not logos | ✅ | Nebius allows naming its products but not implying approval; NVIDIA and Nebius logos need written consent. We name the tools in words, use no logos, and say "built with", never "powered by" or "partnered with" (checked in the README, the app page and the Devpost texts, 2026-10-13, and again 2026-10-25) |
| Feedback on Token Factory, AI Cloud and the NVIDIA tools | ✅ | [feedback.md](feedback.md): each product's use, what worked, what needs work, the first call; final 2026-10-25 |
| Original work, solely owned, no one else's rights infringed | ✅ | Our code; open source used under its licences and built upon (Pollen's app is extended, not copied); no material from any other project or company |

## Testing and judging

| Rule | Status | Notes |
|---|---|---|
| Free access for testing until judging ends (2026-12-15) | 🔶 | The sample Space is free but has no live AI. Judges are offered an author-funded test of the working robot without buying credits or receiving provider keys. Confirm the final access instructions and hardware arrangement; do not treat a bring-your-own-key clone as the required free-access path |
| Physical access to the hardware may be requested (the Reachy Mini is not a phone, tablet or computer) | 🔶 | Keep the robot and the desktop ready through 2026-12-15 |
| After the deadline the submission cannot change | ⬜ | Tag the submitted commit (`hackathon-submission`) and link that tag on the form; later work goes after it |

## Publicity, privacy and conduct

| Rule | Status | Notes |
|---|---|---|
| The sponsor and Devpost may use the entrants' name, likeness and voice for three years | ✅ | Accepted by entering; anyone else in the video agrees in writing first |
| No personal data in submission materials | 🔶 | No real addresses, phone numbers or private links in the video. **The settings code is a private link: after filming it, press "Make a new settings link".** Family photos only with the family's agreement |
| No harmful code | ✅ | Tests; three best-practice reviews of the code, the scripts and the repository, every must-fix and should-fix done, and every dependency audited (2026-10-25, [SECURITY.md](../SECURITY.md)); a pre-commit check for key-like strings and env files, an independent code and privacy review (2026-10-13, every finding fixed); the history rewritten before going public (2026-10-25: private matter out of every commit, dates kept), then gitleaks over all 161 commits: none |

## Kept current

This file changes in the same commit as anything it describes. Last full check: 2026-10-13, with a
second look the same evening at the Devpost page, its updates, FAQ and forum (no amendments since the
morning). Checked again 2026-10-14 by the submission audit against the live pages: the rules unchanged; the
FAQ adds that calling an NVIDIA model through another provider does not count (ours are called on Nebius);
23 judges listed. Checked again 2026-10-25 (the rules and updates pages, read through Tavily since Devpost refuses a plain fetch): no
change to the rules, dates or criteria, and no update since the judges' "Will It Ship?" recording. The README's and
Devpost text's finder limits reworded the same day for the body turn (decision 0016), saying plainly it is checked
against Pollen's kinematics and not yet on the robot. The README's first screen and the Devpost text revised again the
same evening after a judge's-eye read (decision-free wording changes; every claim still linked to its evidence). The Space (testing access) needs Hugging Face PRO for a Docker
Space since this year; the founder subscribes, and it stays up through 2026-12-15 (decision 0010, amended).


## 2026-10-26 review changes

Checked against the official rules retrieved on October 26: the technical requirement, four equally
weighted criteria, public repository and video requirements remain as recorded above. Filming is now
October 27, as the founder chose. No video has been claimed as completed and no physical trial is
marked passed by a software test. The submission text now states the text suite's scope and the
local vision fallback's boundary. The new confirmation and transient-state designs are decisions
0018 and 0019. CPU CI passed on the pushed c3a3f12 revision; both published Spaces and the fresh app install were checked again. Physical validation waits for USB reconnection. Final evidence
links, the tag, app pin, photographs, captions and actual submission remain on the checklist.
The physical trial schedule was corrected to include every object both present and absent;
its tested coverage is preparation, with no physical success rate claimed.

The judge-access audit re-read the official rules through Tavily on October 26. The README, public
demo and submission now link to `judging.md`: sample-only browser access without keys, reproducible
software checks, optional paid API calls using the tester's own key, and the author's free live robot
demonstration. Fresh-clone, Docker, installed-wheel and CPU renderer checks are recorded separately
from hardware. The current profile is first in the scorecard index. The direct FTC report citation
failed here but its exact source and figure were verified via extraction; opening it from another
network remains a final check. No video, photo, physical result, final tag or completed submission
has been inferred from these software checks. Setup configuration changes are recorded in decision 0020.
The pushed `faf46f1` revision passed hosted CI (1,009 tests, 10 skips and three isolated wheel checks),
fresh app installation checks and the refreshed public Space probes (`8d93b15`). The final direct
submission-link check is 20/21, with the FTC source still requiring a check from another network.

After USB reconnection, live startup exposed an external-tool name collision. The supported loader
now uses `remember_fact` (decision 0021); new current-profile text scores are 94, 94 and 95 of 97,
separate from earlier results. Startup and a small motor-response check are recorded as such, without
claiming finder accuracy, speech tasks or video evidence. Household links were refreshed privately;
no link or token is in the repository. Imported demos cannot seed that store. The remaining live
checks, filming, tag and submission are still pending.
The first dedicated SDK CI run found a fresh-install prerequisite missing from Setup (Cairo/GObject
development libraries). Those packages and GStreamer introspection are now included in the setup
instructions and CI; the corrected hosted run on `f96d390` passed CPU, SDK startup and wheel checks.
The awake live preflight is 20/21, with the optional second-check endpoint stopped; this does not mark
spoken tasks or finding trials as passed. Six sample landscapes were restored to the local idle screen,
clearly labelled as samples. The existing filming requirement is unchanged: the founder's own photos,
with consent. No private link, photo or conversation text was placed in the repository.

## Final readiness audit, October 26

The official rules, FAQ and updates were retrieved again; no deadline or prize-rule change was found.
Section 4 exempts Physical AI from the hosted demo URL, while its Testing provision still requires
free access to the working project through judging and permits hardware-access requests. A sample
preview or a clone requiring the judge to buy credits is not, by itself, our free working-project
access plan. Decision 0022 documents author-funded robot testing; final instructions and any hardware
arrangement remain in progress. A public LLM endpoint and distribution of provider keys are not required.

The four scoring criteria remain equally weighted: technological implementation, design, potential
impact and quality of the idea. The grand prize is $20,000; the Physical AI track award is a Jetson
Orin Nano, and the Tavily bonus is $3,000. The combination rule remains one Overall award OR one Track
and one Bonus award. The FAQ confirms that the rest of the application need not be hosted on Nebius
when its required NVIDIA-model runtime call is on Nebius.

`scripts/devpost.py --ref hackathon-submission --final` checks release metadata and links, not legal
eligibility or footage. It currently fails correctly on the video placeholder, absent tag and app
pin. Thirty physical trials, short user sessions and a 72-second uncut take are our evidence plan;
the official rules do not prescribe those trial/session counts or our exact shot plan. The video,
observed core flows, final access, frozen release and actual Devpost submission remain outstanding.

Sources: [Official Rules](https://nebiusglobalaihackathon.devpost.com/rules),
[FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs),
[organiser updates](https://nebiusglobalaihackathon.devpost.com/updates).

Further October 26 diagnostic review: configured voice probing and unavailable connection inspection
now produce accurate preflight results. The README explicitly separates the current local synthetic
text-suite score from the earlier profile's Serverless Job score. These checks add no claims about
working hardware tasks, video compliance, free judge access or completed submission; those remain pending.
The filming checklist and demo-preparation message explicitly require observed tasks after preflight.
The final export also requires tracked files and export inputs to match the release tag. Tag existence
alone could otherwise allow text or code that judges would not receive. The command does not create,
move or publish a tag; actual release publication and submission remain outstanding.

October 26 approved standout work: a separate guided AI playground adds real Token Factory/NVIDIA
inference to predefined invented examples. It clearly identifies simulated camera/OCR, search and
family effects, so it cannot be mistaken for hardware evidence. The original preview stays read-only.
The author supplies inference through a server secret; public operational limits make this supplemental
software access, not the sole free working-project access required through judging. Decision 0023 and
the physical/user-session procedures do not complete the pending video, hardware or access checks.
The guided Space is now public and RUNNING. Six live-model web steps, eight browser/state checks and
five HTTP refusal probes passed; it is linked from the README and submission export with simulated
effects and usage limits stated. No result is presented as a physical trial or a potential-user session.
The refreshed screen preview links to the separate playground and still refuses all 11 tested writes.
All three Spaces are RUNNING; hosted CPU/wheel and SDK checks passed on `bbf0d6d`. These publication
checks do not tick the pending hardware, footage, user-session or final-access items.
The host-page check found a query-routing bug in the guided app. Its fixed static route now accepts
the host's theme query without expanding input or tool access; final embedded-page verification is pending.

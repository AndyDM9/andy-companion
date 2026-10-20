# Submission checklist

From the official rules (nebiusglobalaihackathon.devpost.com/rules), read 2026-10-13 and checked again 2026-10-14. Every rule, our
status and the evidence: [rules-compliance.md](rules-compliance.md). Tick an item only when it is true,
in the same commit that makes it true.

## Stage one: pass/fail

- [x] Runs on Nebius: a runtime call to the Token Factory inference API (Nemotron 3.5 Lightning)
- [x] Uses at least one NVIDIA open model (Nemotron; also Parakeet speech-to-text)
- [ ] A genuine Physical AI project: the hardware reacting live to the real world, shown on video

## The repository

- [ ] Public on GitHub
- [x] Open-source licence file at the top level (Apache-2.0)
- [ ] Licence visible in the repository's About section
- [x] README: setup instructions that work from a fresh clone (cloned from GitHub and checked 2026-10-14; again once public)
- [x] README: how the NVIDIA models and Token Factory are used, and any other Nebius services
- [x] No keys, secrets or personal data anywhere in the history (gitleaks, 108 commits, 2026-10-14)

## Before making the repository public

- [x] No keys in the history (gitleaks: 108 commits, no leaks, 2026-10-14)
- [x] A fresh clone installs and passes its tests (2026-10-13; from GitHub, all three environments, 2026-10-14)
- [x] No home address, phone number or private project names in the tree
- [x] The commit author address: GitHub's noreply address on every commit (history rewritten 2026-10-13; 108 of 108 on 2026-10-14)
- [ ] Final name and branding decided

## The Reachy Mini app (`reachy_app/`)

- [x] Passes Pollen's checker, `robot/.venv/bin/reachy-mini-app-assistant check reachy_app`, including a
      test install in a clean environment (2026-10-13); `tests/test_reachy_app.py` keeps it so
- [x] Its own landing page (the screen, what Andy does, how it's built, what it keeps, what it needs)
- [ ] A Hugging Face account, and `hf auth login` on the desktop (founder)
- [ ] After the repository is public: `robot/.venv/bin/reachy-mini-app-assistant publish reachy_app`,
      public (the app installs `andy-companion` from GitHub, so it can't install while the repository
      is private)
- [ ] At submission: pin the app's `andy-companion` dependency to the `hackathon-submission` tag instead
      of `main`, so an install during judging gets exactly what was submitted

## The video

- [ ] Under three minutes
- [ ] Public on YouTube
- [ ] At least one minute of the robot actually operating
- [ ] Token Factory and the NVIDIA models named aloud
- [ ] No unlicensed music, third-party logos or copyrighted material (no newspaper pages on the TV; our
      own family photos with consent, not the sample landscapes)
- [ ] English captions throughout, and English subtitles for any Spanish (draft: `scripts/draft_captions.py`)
- [ ] After filming the settings code: "Make a new settings link"

## The Devpost form

- [ ] **A complete draft submitted by 2026-10-22**, for Devpost's eligibility check (it covers entries in by
      2026-10-23 10:00 PT); editing continues afterwards
- [ ] A gallery thumbnail, 3:2, at most 5 MB (a still of Andy beside the TV), and gallery images:
      the screen, the letter card, the scam check's receipt, the hood page, the family page, the architecture
      picture, and the scam check five ways (`docs/images/scam-check-five-ways.png`, from
      `scripts/make_charts.py`)
- [ ] "Built with": every sponsor tool (up to 25 tags; the list is in [submission.md](submission.md))
- [ ] Feedback from [feedback.md](feedback.md)

- [ ] Project description
- [ ] Track: Physical AI
- [ ] "Built with" lists Nebius Token Factory, Nemotron and the other tools
- [ ] Feedback on Token Factory, AI Cloud and the NVIDIA tools (mandatory; also the Most Valuable
      Feedback prize)
- [ ] What was significantly updated during the submission period (if any prior work is used)
- [x] City Winner Awards: not applicable (Miami is not one of the 20 listed cities)
- [ ] Submitted before 2026-10-30, 10:00 PT (target 2026-10-27)
- [ ] The submitted commit tagged `hackathon-submission`, and the tag linked on the form
- [ ] The live rules page re-read the day before submitting (amendments take effect when posted)

## Through judging (to 2026-12-15)

- [ ] The repository public and unchanged at the tag; the robot and desktop ready if physical access is asked for

## Bonus

- [x] Best Use of Tavily: a functional runtime call to the Tavily API in the product (search, extract, crawl, map and research; the scam check measured with and without it, 2026-10-14)

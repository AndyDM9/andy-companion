# Submission checklist

From the official rules (nebiusglobalaihackathon.devpost.com/rules), read 2026-10-13. Every rule, our
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
- [ ] README: setup instructions that work from a fresh clone
- [x] README: how the NVIDIA models and Token Factory are used, and any other Nebius services
- [ ] No keys, secrets or personal data anywhere in the history

## Before making the repository public

- [x] No keys in the history (gitleaks: 16 commits, no leaks, 2026-10-13)
- [x] A fresh clone installs and passes its tests (2026-10-13)
- [x] No home address, phone number or private project names in the tree
- [ ] Decide the commit author address (personal email, or GitHub's noreply address by rewriting history)
- [ ] Final name and branding decided

## The video

- [ ] Under three minutes
- [ ] Public on YouTube
- [ ] At least one minute of the robot actually operating
- [ ] Token Factory and the NVIDIA models named aloud
- [ ] No unlicensed music, third-party logos or copyrighted material (no newspaper pages on the TV; our
      own family photos with consent, not the sample landscapes)
- [ ] English subtitles for the Spanish moment
- [ ] After filming the settings code: "Make a new settings link"

## The Devpost form

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

- [x] Best Use of Tavily: a functional runtime call to the Tavily API in the product (five tools; search, extract, crawl)

# Submission checklist

From the official rules (nebiusglobalaihackathon.devpost.com/rules), read 2026-10-13 and checked again 2026-10-14 and 2026-10-20. Every rule, our
status and the evidence: [rules-compliance.md](rules-compliance.md). Tick an item only when it is true,
in the same commit that makes it true.

## Final readiness, checked October 26

- [x] Rules, FAQ, deadline, judging criteria and prize-combination rule rechecked at the official sources
- [x] Devpost export includes testing instructions distinguishing sample preview from author-funded robot access
- [x] `--final` rejects a placeholder video, absent local release tag and app dependency on main before export
- [ ] Final video URL supplied, visibility/duration/hardware footage/English translation/rights verified manually
- [ ] Free judge testing instructions and any required hardware arrangement confirmed through December 15
- [ ] Final tested revision committed, tagged, published and pinned in the app; `--final` and public links pass
- [ ] Devpost entry actually submitted and its confirmation checked (a saved draft is not a submission)

The 30 finder trials and brief user sessions below strengthen the evidence; their counts are our
plan, not explicit hackathon eligibility thresholds. An extra browser AI sandbox is optional; the
Physical AI hosted-demo exemption does not remove the working-project access requirement.

## October 26 review: before filming on October 27

- [x] Separate guided-inference playground implemented with fixed invented inputs, simulated tools, actual consent gate and request/session limits (38 regressions; follow-up wording remains variable and is disclosed)
- [x] Desktop and phone browser checks of sample sharing Yes/No passed; no horizontal overflow or page errors
- [x] Physical absent/TV-decoy/moved-object, full family-choice and local-vision recovery procedures prepared; anonymous first-use task measures specified
- [x] New judge Space RUNNING and verified with live inference; funded secret configured server-side, source hashes match, six web steps and five refusal probes passed
- [x] README/export/testing guide link to guided inference; published screen preview links to it while all 11 write probes remain 403; all three Spaces RUNNING
- [ ] Logged-out Hugging Face landing-page iframe works with its appended theme query after the route fix is redeployed
- [ ] Standout physical challenges and brief user sessions actually completed, with all results retained in scope
- [x] Reconnected robot reaches the conversation loop after fixing the SDK memory-tool collision
- [x] Desktop and dashboard configuration paths have fresh-process SDK tests; dedicated SDK CI defined
- [x] Linux SDK build prerequisites documented and installed by the SDK CI job
- [x] Hosted SDK startup job passes with the newly documented system prerequisites (`f96d390`, 42 checks)
- [x] Awake robot preflight: 20/21 checks; app, audio health, private screen and voice-log check pass (optional second look stopped)
- [x] Preflight probes the configured voice address and fails when robot connection ownership cannot be checked (15 regressions); demo preparation/video instructions require spoken tasks and motion separately
- [x] Final exporter rejects a stale tag, staged/unstaged tracked changes and export inputs missing from the tag (21 exporter regressions)
- [x] Six labelled landscape placeholders restored to the empty gallery; idle selection/JPEG verified, seven-day cleanup applies (own photos still required for filming)
- [x] Live household links are private random values again; the updated screen link returns 200
- [x] Imported/cached demos are refused before they can seed household data
- [x] Short judge testing instructions link from the README, demo and submission text
- [x] Anonymous fresh clone installs and passes; Docker demo serves pages/assets and refuses writes
- [x] The full demo entry point and an isolated installed-wheel check have passed locally and are included in CI
- [x] Documented settings pass regression checks without hardware; CPU simulation dependencies and keyless renderer check verified
- [ ] Confirm the FTC report opens from another network before final submission (direct 404 here; content verified through Tavily)
- [x] Reproduced sharing, transient-storage, medicine-card and journal-check gaps have regression tests
- [x] Confirmation binds a spoken readback and fresh yes to one exact action, once (decision 0018)
- [x] Screen cards and research answers use authenticated local memory, with a cross-process test (decision 0019)
- [x] Pending items are listed and deletable; delete everything clears the current card, captions and views
- [x] CPU GitHub Actions workflow defined, actions pinned and permissions read-only
- [x] Hosted CPU CI and isolated installed-wheel checks passed on `faf46f1` ([run](https://github.com/AndyDM9/andy-companion/actions/runs/40385985605), October 26)
- [x] Refreshed public demo verified: testing links, pages/assets, eleven refused writes, wrong-token rejection and no retained visitor name
- [x] A fixed 30-attempt physical finder plan and scorer are available (`evals/physical_trials.py`)
- [x] The trial plan tests every object present and absent, both lighting conditions, and every position with each object present
- [ ] The 30 physical attempts completed and scored, including absent objects and failures
- [ ] On the robot: the new sharing readback, a refusal, a changed topic, and a remembered photo story
- [ ] On the robot: the body turn, research stopping, medicine-page referral and voice interruption
- [ ] Two or three consenting potential users try the key tasks; retain only agreed feedback and task counts
- [x] Current text profile evaluated locally, three runs of 94, 94 and 95 of 97, input/code hashes recorded; final submission-time Serverless Job remains separate from physical trials
- [ ] Video and real-robot photographs added after filming; no placeholder presented as completed evidence

## Stage one: pass/fail

- [x] Runs on Nebius: a runtime call to the Token Factory inference API (Nemotron 3.5 Lightning)
- [x] Uses at least one NVIDIA open model (Nemotron; also Parakeet speech-to-text)
- [ ] A genuine Physical AI project: the hardware reacting live to the real world, shown on video

## The repository

- [x] Public on GitHub (2026-10-25, after the history rewrite and three reviews)
- [x] Open-source licence file at the top level (Apache-2.0)
- [x] Licence visible in the repository's About section (Apache-2.0, checked logged out, 2026-10-25)
- [x] README: setup instructions that work from a fresh clone (cloned from GitHub and checked 2026-10-14; again once public)
- [x] README: how the NVIDIA models and Token Factory are used, and any other Nebius services
- [x] No keys, secrets or personal data anywhere in the history: private matter rewritten out on 2026-10-25, then gitleaks over every commit: no leaks, and no key value anywhere

## Before making the repository public

- [x] Best-practice reviews of the code, the scripts and the repository (2026-10-25): every must-fix and should-fix
      done (see the CHANGELOG); dependencies audited with `pip-audit`
- [x] When it goes public: GitHub's private vulnerability reporting, secret scanning and push protection turned on (2026-10-25)
- [ ] At submission: the video's thumbnail (linked to YouTube) and a photo of Andy beside the TV at the top of the README
- [x] A fresh clone installs and passes its tests (2026-10-13; from GitHub, all three environments, 2026-10-14)
- [x] No home address, phone number or private project names in the tree
- [x] The endpoints recreated with `create` (token in MysteryBox), so no token is in their start settings (2026-10-25: the old two deleted, the second look remade and checked: 401 without the token at both addresses)
- [x] The commit author address: GitHub's noreply address on every commit (history rewritten 2026-10-13; 108 of 108 on 2026-10-14)
- [x] Final name and branding decided: **Andy**, entered by the founder as an individual, no company name (2026-10-25)

## The Reachy Mini app (`reachy_app/`)

- [x] Passes Pollen's checker, `robot/.venv/bin/reachy-mini-app-assistant check reachy_app`, including a
      test install in a clean environment (2026-10-13); `tests/test_reachy_app.py` keeps it so
- [x] Its own landing page (the screen, what Andy does, how it's built, what it keeps, what it needs)
- [x] A Hugging Face account, and `hf auth login` on the desktop with a write token (2026-10-25)
- [x] The demo Space public: `andydm/andy-companion` (PRO), public with the repository on 2026-10-25, every page 200
      logged out, writes 403
- [x] The app published, public: [andydm/andy-companion-app](https://huggingface.co/spaces/andydm/andy-companion-app) (2026-10-25, Pollen's checks passed with a fresh install
      from GitHub; published from a clean copy of the tracked files, so no build leftovers or git history)
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

- [ ] **Before pasting the final text:** the letter (live-test 3k, 3l), the research streamed to the TV (3e) and the
      photo story (3y) each recorded as tried on the robot in `docs/live-test.md`; The draft describes planned filming on October 27; it can describe completed footage only after recording. A moment that doesn't work leaves the video and the text says "not yet tried on the
      robot".
- [ ] Paste from `uv run python scripts/devpost.py` (the draft: evidence links at `main`); at submission,
      `uv run python scripts/devpost.py --ref hackathon-submission --final` once the tag is pushed, and paste again.
      First commit the final text, feedback and app pin, validate, then tag/push that commit. Export from
      that unchanged snapshot; the command rejects files that differ from the tag.
      Every link opens (2026-10-25: 18 of 19 from here; ftc.gov refuses this network, its two pages confirmed from
      another).
- [ ] **A complete draft submitted by 2026-10-22**, for Devpost's eligibility check (it covers entries in by
      2026-10-23 10:00 PT); editing continues afterwards. *Missed:* the draft was **saved** (not submitted) on
      2026-10-25 as devpost.com/software/andy-b45hds: overview, story, 25 tags, three links and every additional-info
      answer (the founder ticked the two declarations); then the thumbnail (a stand-in: the name, the problem and
      the real **Be careful** card, 3:2), gallery images 4 to 8 with their captions (each under Devpost's 140
      characters; `tv-finder.png` re-captured with the new layout) and the founder's contribution. Still missing:
      the video link, and the founder's robot photos as images 1 to 3 (then the thumbnail becomes photo 1).
      Devpost's template headings were found above the story and removed; the preview renders every heading, list
      and link
- [ ] **The gallery**, at most eight images, the real robot first, every image with a one-sentence caption (judges
      seldom look past the first three or four). The thumbnail is image 1, 3:2, at most 5 MB.
      1. *(founder)* Andy beside the TV, a letter held up: "Andy reads the letter in your hand; the TV shows it in large print."
      2. *(founder)* Andy's head turned to real glasses: "Asked where the glasses are, Andy looks around, looks closer, and points."
      3. *(founder)* The robot in its room, the TV beside it: "A home robot, not a speaker."
      4. `tv-scam-receipt.png`: "A scam check: what to do first, then the sign, the warning Tavily found and its source."
      5. `tv-finder.png`: "What Andy looked at: the four views in the order it turned, and where it saw them."
      6. `sim-search.gif` (or a still from it): "Andy's own search in Pollen's MuJoCo simulation, run as Nebius Serverless Jobs."
      7. `family-page.png`: "The family's page: only what was shared, and a message for Andy to pass on."
      8. `architecture.png` (rendered from the SVG: `rsvg-convert -w 1800 -b white`): "What runs at home, and what runs on Nebius."
      Only if live-test 3cc passed: a grandchild moving Andy's antennas, "A move taught by hand, played back by name."
      The screens come from the demo (sample data only); the robot's photos show no one who hasn't agreed, and no
      third-party logos or screens.
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

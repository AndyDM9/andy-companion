# Status

**Last updated 2026-10-27.** Update this file in the same commit as any change it describes.
The plan and its milestones are in [PLAN.md](PLAN.md); each milestone's history is in [CHANGELOG.md](../CHANGELOG.md).

## At a glance

| # | Milestone | State | Notes |
|---|---|---|---|
| M0 | Andy talks through Nemotron | ✅ Done 2026-10-13 | Parakeet, Nemotron 3.5 Lightning on Token Factory and Qwen3-TTS on the robot; measured below |
| M1 | Clock and reminders | ✅ Done 2026-10-13 | Verified on the robot: the time of day from the clock; a reminder set by voice, listed, and said unprompted when due |
| M2 | Privacy floor | USB reconnected; startup fixed; voice and consent task checks pending | Previous live verification: no conversation text in any log, tool arguments not logged, no transcript printed by the voice server; Andy's memory only what the person asked it to keep |
| M3 | Body behaviours | ✅ Done 2026-10-13; more on 2026-10-20 | Looking at the person while speaking, following, sleep, quiet and wake, verified by the founder on the robot. Added 2026-10-20 and tested in code, awaiting the robot: turning to a second voice, waving back, moves taught by hand ([live-test.md](live-test.md) 3aa to 3dd) |
| M4 | The day, the same way every time | ✅ Done 2026-10-13 | The day plan, reminders in the person's words, pace and volume that stick, jokes, stories and On this day; English and Spanish |
| M5 | Tavily | 🔨 Built, awaiting the live test | Five APIs at runtime: search (news, look-ups, scam warnings at advanced depth), extract (links family send), crawl (what's on), map (the town's events page, at setup) and research (streamed to the TV). The scam check measured five ways ([results](../evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json)) |
| M6 | Eyes | 🔨 Built; finding measured on the robot, the rest awaiting the live test | Nemotron 3.5 Super VL on Token Factory by default (decision 0011), Nano VL on our own endpoint as the option; letters read on this computer; finding things reads four views as zoomed tiles and looks closer before pointing (decision 0012), tested in simulation as Nebius Serverless Jobs (decision 0013) and on the robot at home: pointed 3 of 9, never wrong, every miss a chair past the head's reach (2026-10-20). Offline eyes, NVIDIA Cosmos Reason 2 on this computer (8B on this desktop, 2B for one GPU), as the fallback (2026-10-25, [decision 0015](decisions/0015-cosmos-on-this-computer-as-the-offline-eyes.md)), measured in simulation |
| M7 | Andy's screen and the family page | 🔨 Built, awaiting the live test | The TV, Under the hood, the family page and the settings page, every text colour 7:1; a public read-only demo of all four on sample data (decision 0010), its Hugging Face Space public since 2026-10-25 |
| M8 | Proof | 🔨 Built; final run before submitting | Current text profile: **94, 92, 95 of 97 locally**, real consent gate and synthetic tools. Earlier profile's latest Serverless Job: **96, 95, 92 of 97** (2026-10-25). Final submission-time Job still pending. The scam check five ways, 54 real turns timed on the robot, finder simulation; every scope and failure below and in [evals/results/](../evals/results/) |
| M9 | Ship | ✅ Done 2026-10-25 | Public on GitHub (Apache-2.0 in About; secret scanning, push protection and private vulnerability reporting on) after the history rewrite and three best-practice reviews; the demo Space public; the Reachy Mini app published ([andy-companion-app](https://huggingface.co/spaces/andydm/andy-companion-app)); the doctor and user services; a fresh clone installs and passes. Left for submission: the `hackathon-submission` tag, and the app pinned to it |
| M10 | Video and submission | 🔨 Draft saved on Devpost | The shot list ([video.md](video.md), 2:56 with a 72 s uncut take), the Devpost text ([submission.md](submission.md), about 2,000 words, revised after two judge's-eye reads on 2026-10-25) and the feedback ([feedback.md](feedback.md), final 2026-10-25) ready; the README's Limitations and Path to shipping, every Devpost number linked (2026-10-25); the gallery planned, its four robot photos the founder's; the Devpost draft saved 2026-10-25 (devpost.com/software/andy-b45hds: story, tags, links, every answer, thumbnail, five captioned images; not submitted: the video and the robot photos to add); filming 2026-10-27, as the founder chose on October 26 |


## October 27 awake check and bounded hardening

- **Live:** founder authorised waking Andy. Existing supervisor used; no second controller. Founder
  confirmed the slower synthetic desktop clock question was heard and Andy answered the correct
  time. Untimed functional check only, without retained audio/conversation or verified clock-tool
  telemetry. Earlier HDMI playback lost words; this does not establish a robot speech fault.
- **Current runtime:** existing Andy service restarted with the fixes and zero competing controllers.
  Awake live preflight **20/21**: core app, microphone, voice, cloud vision and local eyes available;
  **zero microphone drops**, **zero suspect voice-log lines**. The optional paid second-check endpoint
  remains stopped (404). No new physical reader/search/pointing trial claimed.
- **Fixed:** negated physical cues and explicit camera refusal in a supplied message's introduction
  no longer authorise OCR (0028 amendment). Recognised labelled credential values are refused before
  any memory proposal or tool dispatch, including explicit requests and the compatibility alias
  (decision 0029). Limited patterns only; unlabelled/encoded secrets and other write paths are outside
  this check. It does not remove existing data or add logging.
- **Validation:** CPU **1,208 / 14 skipped**, installed robot environment **1,235 / one skipped**,
  isolated wheel **three passed**, changed Python lint passed. Fifty-eight added regression cases
  include actual SDK dispatcher checks with no camera or memory routine reached for denied inputs.
- **Experiment left out:** baseline, clearer descriptions and generic proposal examples each scored
  **12/18** in scoped synthetic memory-offer checks; all six photo-story instances missed a proposal.
  Prompt experiments reverted; [evidence](../evals/results/memory-offer-experiments-2026-10-27.json).
  These check tool names/proposal status, not fact grounding or complete conversational correctness.
  Memory-offer consistency remains an open problem.
- **Current model proof:** **94, 92 and 95 of 97**, three full local runs with the new gate, real API
  calls and synthetic tools ([scorecard](../evals/results/suite-2026-10-27-gates-local.json)). Profile and
  tool descriptions unchanged; confirmation-source hash verified. Photo-memory offers failed all
  three; future-event offers twice; activity offer, extra searches, daily-event/greeting wording and
  supportive-response completeness once each. Letter/quoted-message cases passed; no unauthorised
  write effect reported. This is not a demonstrated score improvement or hardware test. Final Job,
  physical checks and submission remain pending. [Audit metadata](../evals/results/gates-audit-2026-10-27.json).
- **Published:** source `433a7fc`; [hosted CPU/wheel and SDK checks passed](https://github.com/AndyDM9/andy-companion/actions/runs/40509014961).
  Guided Space `0ed342e45b0383a8ca0daedd1989220b938c99dd` RUNNING; actual deployment revision,
  profile/tools and downloaded confirmation source match. Eight public layouts, eight real guided
  examples and three protocol refusals passed, all with invented data and simulated effects.
  Anonymous clone **1,208 / 14 skipped**;
  history scan **225 commits clean**. All **292** relative links and **23** export links pass.
  Final exporter still correctly blocks the video placeholder, missing final tag and app dependency
  on main. All three Andy services active. Final physical/video/access/submission work remains open.

## Final re-audit (started October 26)

- **Published follow-through:** source `18922ce`, hosted CPU/wheel and SDK CI passed; guided Space
  `da0b391d2c78f0330cac97cf0b65016fb73e8768` RUNNING and profile/tool/confirmation-source hashes
  match. Eight public layouts/eight real guided scenarios/three refusals rechecked successfully.
  Anonymous clone updated to the published source: **1,156 / 14 skipped**. History scan **223 commits
  clean**, all **23** updated export links open. No connected signed-in submission browser.
- **Prior published robot state (superseded by the awake check above):** existing service restarted with zero competing controllers. Persisted
  mode is **asleep**, prior app exit **0**, no traceback, supervisor/voice/local eyes active. The mode
  was preserved. Post-restart preflight **17/21** reflects the intentionally absent sleeping app and
  stale audio data, plus the stopped optional second check. Earlier awake preflight was **20/21**.
  Wake and rerun the core checks before filming; no new awake spoken reader trial claimed.
  The video guide now distinguishes the optional paid endpoint from required awake checks.

- **Previous October 26 model proof:** **94, 96 and 94 of 97**, three full local runs after the camera-reader fixes;
  [scorecard](../evals/results/suite-2026-10-26-camera-source-local.json). Real API calls, synthetic tools, real confirmation/source checks;
  no microphone, camera or motors. All quoted-message/letter cases passed in these runs. Remaining
  failures: photo memory offer every run, future-event offer twice, supportive-response completeness
  once, story fidelity once. No unauthorised write effect reported. Initial audit scores 92/94/92
  and intermediate 93/94/95 are retained separately, not pooled or discarded. Final submission-time
  Serverless Job remains pending.
- **Fixed:** read_letter no longer asks the model to speak a preliminary instruction before calling
  OCR. A narrow quoted-message source check at real SDK dispatch prevents this recognised spoken
  pattern invoking OCR (decision 0028); the evaluator uses the same check. It is not a general intent
  classifier or comprehensive prompt-injection defence. Three reader entrypoint tests and 16 source/
  dispatch regressions added. Updated stale watch confirmations and evidence links.
- **Validation:** CPU **1,156 / 14 skipped**, robot environment **1,177 / one skipped**. Fresh anonymous
  baseline clone **1,141 / 13 skipped**; app checker and isolated wheel passed. Lockfiles, JS, Python
  and all 276 checked relative links valid. Pre-audit full-history scan: **222 commits clean**.
- **Live:** preflight **20/21**; optional second-check endpoint stopped. No competing controller,
  no microphone drops and no suspect voice-log lines. Local camera-only recovery **0.943 s**
  (acquisition **0.320 s**), no saved frame/description or motor controller. No actual spoken letter
  or recovery trial inferred. Six gallery placeholders remain; use consented own photos for filming.
  Night clock is currently on, so film in daytime or choose a suitable setting before filming.
- **Judge access:** all three Spaces RUNNING; five screen URLs 200, eight writes 403, wrong token
  404. Eight desktop/phone layouts and eight guided-model scenarios passed; three protocol refusals
  passed. Guided effects remain simulated and isolated from the household. Source restart and
  published hashes are verified in the follow-through above; awake physical checks remain pending.
- **Submission:** live official rules/FAQ rechecked; 23 export links opened before these text updates.
  Final exporter correctly blocks the video placeholder, absent release tag and app dependency on main.
  Actual video/rights/translation, Devpost reconciliation/submission, free hardware-access arrangement,
  physical trial measurements and short consenting-user sessions remain open. The 30 trials are our
  evidence plan, not an eligibility threshold. [Audit scope](../evals/results/reaudit-2026-10-26.json).

## October 26 review work

- **Watch retry confirmed:** founder reports the local robot's watch search now works after the
  tool-first prompt revision/restart; a local-screen view shows the watch result and complete
  picture highlights. Qualitative, untimed functional confirmation only: no separately verified
  pointing score or added fixed-benchmark trial. Household screenshot/camera pictures not retained
  in the repository. The specific reported dispatch issue is resolved; full-suite rerun, planned
  physical measurements and broader M6/M7 checks remain open.

- **Card shadows and search-picture frames:** fixed shadow clipping at the left column/layout;
  card content remains clipped within its own rounded box. Chosen/secondary sighting borders are
  now drawn inside the pictures (4/2 px), so the card's clipped content cannot cut their edges off.
  **12 browser combinations plus long-content containment passed**, using invented data only
  ([evidence](../evals/results/screen-frames-shadows-2026-10-26.json)); CPU **1,141 / 13 skipped**.
  No picture geometry or data flow changed. Local page versioning picks up the asset change;
  public preview publication follows the source commit. M7's physical checks remain pending.

- **Watch request announced without dispatch:** no finder call in recent tool-name telemetry,
  services running and no other controller. Replaced the instruction to announce first with an
  immediate same-response `find_object` call before speech, including watches and repeated requests
  (decision 0027). **20/20** targeted real streaming-inference checks passed with invented requests,
  valid object arguments and no pre-call speech; three non-request categories excluded. Five SDK
  entrypoint regressions use mocked hardware. CPU **1,141 / 13 skipped**, robot **1,158 / one skipped**.
  The cause of the original missing dispatch is not established; no household speech retained.
  Existing service restarted; **spoken watch retry subsequently confirmed by the founder**, untimed
  (see the follow-through above).
  [Scoped checks](../evals/results/watch-routing-2026-10-26.json). Full-suite follow-through is recorded in the final re-audit above; earlier scorecards retain their
  original profile/code hashes.

- **Speaking-ring alignment:** corrected the 20% downward offset reported in the screenshot.
  Browser-measured ring/pill centre difference is now **0 px** at 1920×1080 and 1280×720 (previously
  13.30/9.41 px). Icon position, speaking pulse and calm/reduced-motion behaviour preserved.
  CPU **1,141 passed / 12 skipped**; M7's physical checks remain pending. Public preview rebuild
  follows the source commit; an open local TV reloads the updated page automatically.

- **Screen follow-through deployed:** source `86d2dab`, preview Space revision
  `95be732cd73c046007b9008b1d3e01fcfd3af33b`, hosted source CI passed. All three Spaces RUNNING;
  five preview pages 200, three new write probes 403, hosted guide/focus and invented progress verified.
  Existing Andy service restarted after verifying zero other controllers; local screen 200 with both
  additions. Preflight **20/21**, optional second-check endpoint stopped. Fixed a catalogue false alarm
  by testing configured-model inference (decision 0026), with eleven new regressions. Final CPU
  **1,141 / 12 skipped**, robot environment **1,153 / one skipped**. Cloud model answered an invented
  blue image; local camera-only fallback answered in **3.201 s** (acquisition **0.282 s**), without
  retaining picture/description. No physical spoken search, pointing score or usability result inferred
  ([deployment evidence](../evals/results/screen-followthrough-2026-10-26.json)).


- **Voice discoverability and physical search feedback:** founder-approved feature work reopened
  after the earlier freeze (decision 0025). English/Spanish guide with nine spoken examples and
  manual controls; opening it makes no model/tool call. Finder stages and actual room-view counts
  replace the unexplained wait, with memory-only scoped updates, 45-second expiry and cancellation
  cleanup. No recognition confidence or physical accuracy inferred from a count. M6/M7 remain
  awaiting their physical checks. CPU **1,130 passed / 12 skipped**, installed robot environment
  **1,142 / one skipped**, isolated wheel **3 passed**. Browser: **16** language/palette/720p/1080p
  combinations plus **4** additional checks, including photo-layout return and offline recovery
  ([scoped evidence](../evals/results/screen-guide-progress-2026-10-26.json)). Nineteen new regressions.
  Service restart and preview publication are verified in the follow-through above; live spoken
  interaction and finder timings have not been remeasured. Research comparison is in [research.md](research.md).


- **Further submission pass:** all 23 export links now open after replacing the unreachable FTC file
  citation with a verified official HTML release; wording now matches its approximate figure. Tagline
  remains 198 characters and tags 25. All three Spaces are RUNNING, and a fresh public AI proposal / No
  check preserved private sample state. Video metadata preflight is built with 17 regressions; the
  19.87-second silent simulation is rejected. No actual final movie is available yet, so footage/content,
  rights, translation, publication and submission remain pending. No connected signed-in browser is
  available to reconcile the saved Devpost draft: the updated repository text must be pasted before submission.
  CPU 1,111 passed / 12 skipped; installed robot environment 1,123 passed / one skipped. Relative links
  and Python checks pass. Real `--final` still rejects video placeholder, missing release tag and app pin.
- **Vision recovery follow-through:** fixed stopped-endpoint preflight/404 fallback and transport
  validation on the fallback path. Local eyes must be loopback even over HTTPS; no camera image may
  silently go to a remote backend labelled local. Six regressions plus five probe tests pass.
  CPU 1,094 / 12 skipped; installed robot environment 1,106 / one skipped. Real camera-only probe:
  1920×1080, local Cosmos Reason 2 8B response 2.874 s, acquisition 0.316 s
  ([metadata](../evals/results/camera-recovery-2026-10-26.json)). No picture or description retained,
  no motor controller opened, no voice/hood/pointing result claimed. M6 remains partial pending those checks.
  The founder reported glasses found in the requested centre-table task; point/time confirmation is
  pending, and the fixed 30-trial benchmark has no recorded row from that untimed report.
  Hosted CPU/wheel and SDK checks passed on `a4e3930`
  ([run](https://github.com/AndyDM9/andy-companion/actions/runs/40427038841)). Existing Andy service restarted
  after confirming no competing app. Post-update preflight 20/21: microphone drops 0, suspect voice-log
  lines 0, short Nemotron reply 0.50 s; optional second check stopped. A left-side glasses check is pending.
- **Approved standout work:** built three isolated guided AI challenges (invented bill, family choice,
  absent glasses), reusing the actual confirmation gate with simulated tool effects. Thirty-eight new
  regressions pass. Local real-Nemotron checks exercised all three examples plus Yes/No; code preserved
  private/shared sample state correctly. In three final absent rechecks, all reported a miss, but one
  still offered another search despite the one-pass instruction. No extra action runs; the UI and
  limitations state this distinction. Desktop/phone browser checks passed
  Yes/No, no horizontal overflow and zero page errors. The separate judge Space is RUNNING, first published from
  `ccbe0a5` (Space `18038ee`). Public verification passed six steps/eight browser-state checks and five
  HTTP refusal probes; source hashes match. The clean Docker image served pages and correctly disabled
  inference without a key; its 17 files contain no household modules or secret files.
  Physical challenges and anonymous first-use procedures are ready in live-test.md; observations still pending.
  Full validation: CPU 1,081 passed / 12 skipped; installed robot environment 1,093 passed / one skipped;
  Python checks and JavaScript syntax pass. The robot profile and its existing scorecard inputs are unchanged.
  Hosted CPU/wheel and SDK jobs passed on `ccbe0a5` ([run](https://github.com/AndyDM9/andy-companion/actions/runs/40407314697)).
  They also passed on `bbf0d6d` ([run](https://github.com/AndyDM9/andy-companion/actions/runs/40408835078)).
  Screen preview refreshed from that commit (Space `a907b1d`): new guided link present, four pages 200,
  11 writes refused with 403. All three Spaces are RUNNING; a redacted 211-commit history scan is clean.
  A final logged-out host-page check caught the iframe's `?__theme=system` URL returning 404.
  Static GET routing is fixed and two theme regressions added. Redeployed `ab693be` (Space `3eebb03`):
  the logged-out host page loads the embedded app, and its real-model proposal / No flow keeps the sample private.
  After that fix: 40 playground regressions, CPU 1,083 passed / 12 skipped, installed robot environment
  1,095 passed / one skipped. Hosted CPU/wheel and SDK jobs passed on `ab693be`
  ([run](https://github.com/AndyDM9/andy-companion/actions/runs/40409666629)).
- **Release snapshot audit:** final export now requires the tracked working files to match the release
  tag, including all three export inputs. An old tag with newer files or untracked final documents is
  rejected; 21 exporter regressions and the full CPU suite (1,043 passed / 12 skipped) pass.
  The installed robot environment passed 1,055 / one skipped. The real final export still reports the
  video, release tag and app-pin blockers; they remain pending.
- **Further preflight audit:** fixed default-only voice probing and a false pass when robot connection
  ownership could not be inspected. Fifteen regressions pass; the full CPU suite is now **1,039 passed /
  12 skipped**, and the installed robot environment **1,051 passed / one skipped**. Latest live preflight
  remains **20/21**, optional second look 404; zero microphone drops and zero suspect voice-log lines.
  Redacted gitleaks scan of 206 commits found no leaks.
  M2/M5/M6/M7 still need observed task outcomes; the doctor does not certify those or readiness to film.
  Demo preparation and the video checklist now use the same preflight wording and observation requirement.
- **Submission readiness: not yet.** The final exporter now blocks the placeholder YouTube field,
  missing `hackathon-submission` tag and app dependency still on main. Manual video, hardware-task,
  rights, access and actual form checks remain separate. Full physical trials and user sessions are
  evidence-strengthening work, not explicit counts required by the official rules.
  Export tests: 17 passed; CPU suite: 1,024 passed / 12 skipped. The real draft's three release blockers
  are confirmed by `--final`, without starting a service, buying compute or submitting a form.
- **Judge access:** decision 0022 distinguishes the free sample preview, optional own-key reproduction
  and author-funded real-robot testing. Judges do not need to purchase credits for the latter. Final
  access instructions and any organiser-requested hardware arrangement remain in progress. No raw
  provider key or new public model service has been exposed. Both Spaces and all preview pages rechecked.
- **USB reconnected:** daemon running after restart; Andy now gets past configuration and reached its
  conversation loop after the `remember_fact` collision fix (decision 0021). Fresh health showed zero drops.
  It later went to sleep cleanly. The founder has the refreshed private screen link (verified 200).
  Wake/answer/interruption observations and the revised task flows remain pending.
  Latest while awake: doctor **20/21**, with the optional second-check endpoint stopped; app/microphone,
  screen and privacy checks pass. Six landscape samples restored to an empty gallery; sample JPEG served 200. Seven-day cleanup applies,
  but the cause of the earlier empty gallery was not verified.
- **Pre-watch-change text profile:** version e scored **94, 94, 95 of 97** with the renamed tool. Two memory offers fail
  each run; ambiguity before deletion and respecting "not now" each fail once. The new scorecard carries hashes.
  Local checks after the startup/demo fixes: CPU 1,011 passed / 12 skipped; robot environment 1,023 passed /
  one skipped; three isolated wheel checks pass. Dedicated SDK startup CI is now passing.
  On `8958439`, CPU CI passed; the new clean SDK job found missing Cairo headers. CI and Setup now include
  Cairo/GObject development and GStreamer introspection packages; the corrected [hosted run](https://github.com/AndyDM9/andy-companion/actions/runs/40392095129)
  passed: CPU 1,011 / 12 skipped, SDK 42 passed, wheel three passed.
- **Judge access:** [testing instructions](judging.md) now link from the README, demo and submission text.
  An anonymous fresh clone installs; the Docker demo builds; real-entry subprocess and isolated wheel checks
  join CI. The current scorecard is first in the evidence index. No browser was available in this audit;
  HTTP/assets and JavaScript syntax were checked, with earlier visual checks retained separately.
  [Hosted CI on `faf46f1`](https://github.com/AndyDM9/andy-companion/actions/runs/40385985605) passed all
  1,009 CPU tests (10 skips) and three isolated wheel checks. The updated public demo and a fresh app install
  passed; the direct submission link check opened 20 of 21 (FTC remains below).
- **Setup consistency:** desktop and dashboard share one settings reader (decision 0020). Quoted keys,
  shell overrides, custom voice addresses, screen ports and documented vision/finder options pass software
  regressions; launch now reaches the conversation loop after the tool-name fix below.
  Current robot-environment tests: 1,018 passed / 1 skipped, without connecting to hardware.
- **Consent:** one proposed payload, exact spoken readback, fresh yes, two-minute expiry and one use,
  scoped to the conversation. Tested with the installed dispatcher, without a robot. Robot verification pending.
- **Privacy:** screen cards and research answers moved from disk to the screen server's memory, tested
  from a separate process. Pending items are listed and deletable; full deletion clears card, captions and views.
- **Medicine pages and diagnostics:** fixed referral text, no free-text instructions passed to the
  conversation; unreadable journals fail the privacy check. Regression tests pass.
- **Automated checks:** CPU GitHub Actions passed on pushed commit `c3a3f12` ([run](https://github.com/AndyDM9/andy-companion/actions/runs/40381561500)). New
  text evaluations run the real consent gate around synthetic tools and keep input/code hashes.
- **Evidence still needed:** 30 physical finder attempts (`evals/physical_trials.py`), short sessions with
  consenting potential users, checks of the revised flow on the robot, video and real photos on October 27.
  The trial schedule now covers each object present and absent, both lighting conditions, and all
  five positions with each object present; a regression test catches correlated object/presence cycles.
- **New model findings:** proactive memory offers can be skipped, or the model can promise a note without calling a tool; the gate does not create a note in that case. The new text-suite
  runs are recorded separately from the October 25 profile; old scores are not proof of these changes.

## Accounts and keys

| What | State |
|---|---|
| Devpost registration | ✅ 2026-10-13 |
| Nebius Token Factory | ✅ Individual account, zero data retention on, key in `~/.config/companion-hackathon/.env` |
| Tavily | ✅ Key saved and tested; pay-as-you-go since 2026-10-14 (the free 1,000 monthly credits ran out on 2026-10-14) |

## Measurements

| Date | What | Result |
|---|---|---|
| 2026-10-26 | **USB recovery and real startup** | USB motor/camera/audio visible; daemon recovered after restart. No competing robot app. Before starting Andy: requested head +5°, read +1.76°; antennas +3.16° / −3.52°; restored head residual +0.36°. App startup name collision fixed; fresh health with 0 drops and screen 200, then a clean sleep. Doctor while asleep 18/21; optional second look stopped; 0 suspect voice-log lines. This is not a voice-task or finder pass |
| 2026-10-26 | **Pre-watch-change profile version e**, local text suite | **94, 94, 95 of 97**; moment-1 and photo-2 fail each run, moment-5 and chat-2 once. [Scorecard](../evals/results/suite-2026-10-26-startup-local.json), after the memory-tool rename; real gate and synthetic results, no physical task scoring |
| 2026-10-26 | **Judge access audit** | `faf46f1`: hosted CPU suite 1,009 passed / 10 skipped; three isolated wheel checks pass. Anonymous clone of `1d0a4e8`: install and 991 tests pass; Docker demo builds. Updated Space `8d93b15`: pages/APIs/assets 200, eleven writes 403, wrong tokens 404, guide linked; both Spaces RUNNING. Fresh app installation/entrypoint/uninstallation passes. CPU simulation scene downloaded and rendered at 1920×1080 in a fresh container, without a key or robot. Four environment locks validate; page scripts/JSON parse; gitleaks: no leaks in 200 commits. Direct submission links 20/21; FTC report content verified separately |
| 2026-10-26 | **Physical trial plan coverage** | Each object present and absent in both lighting conditions; all five positions with each object present. Fixed the original schedule's remote/absent correlation. CPU tests 991 passed / 10 skipped; robot environment 1,000 passed / 1 skipped. Physical attempts still pending |
| 2026-10-26 | **Published verification** | `c3a3f12` pushed; hosted CPU CI passed. Public screen Space updated from that commit: front page and four pages 200, pending-item UI present, transient writes 403; both Spaces RUNNING. App checker: fresh install, entrypoint registration and uninstall passed. Hardware interactions remain unverified while USB is disconnected |
| 2026-10-26 | **Software and running services** | 990 passed / 10 skipped in the CPU environment; 999 passed / 1 skipped in the robot environment. Public demo: front page and four pages 200, writes 403. Existing Andy service restarted after confirming no other robot app connected. Doctor: 17/21; privacy check clean, cloud conversation and vision reachable, screen and local eyes running. Robot USB disconnected temporarily, explaining the daemon error, app not starting and stale microphone health; optional second-check endpoint stopped. Andy, voice and local-eyes services stopped while disconnected. Live checks resume after USB reconnection |
| 2026-10-26 | **Earlier profile, text suite**, version 2026-10-26d, local API calls, real confirmation gate with synthetic tool results | **95, 95, 95 of 97**; moment-1 and photo-2 failed each run (memory offers). Gate tests reject unapproved writes. [Scorecard](../evals/results/suite-2026-10-26-final-local.json); hashes of the tested profile, tools, suite, runner and gate included. This is not a hardware test or a Serverless Job |
| 2026-10-25 21:35 | **The Devpost draft saved** (filled with Playwright, the founder logged in; not submitted) | devpost.com/software/andy-b45hds, 3 of 5 steps: overview, story (13,280 characters, rendered and checked), 25 tags, three links, every additional-info answer from docs/feedback.md and the compliance file, the founder's two declarations. Historical snapshot: the thumbnail and five sample gallery images were added later that evening; the video and real-robot photos remain |
| 2026-10-25 21:06 | **The heard words cleared from this desktop's logs** (the founder ran the script, with sudo) | This user's 44 journal files removed; the voice and eyes servers' lines removed from syslog, syslog.1 and syslog.2.gz: 0 left in each, and the doctor's "No words in the voice log" passes. The script read today's syslog as binary from about 13:00 (no `grep -a`) and dropped the rest of that copy to 21:05; the system's own journal, which syslog copies, still holds that window |
| 2026-10-25 20:52 | **A research loop on the robot**, found from the logs (tool names and times only) | The same question researched 7 times in 5 minutes: each answer, as it was passed on, started the research again; "stop searching" had nothing to stop. Stopped by restarting Andy; fixed in the hand-over's words, a guard in code (30 s after an answer, 10 minutes for the same question) and a real stop. To re-check on the robot |
| 2026-10-25 20:40 | **The TV's design in a browser**: every scene at 1920 x 1080, 1920 x 950 and 1280 x 720, the live screen at four sizes, and the other pages on a laptop and a phone, checked for text on text, text cut off or under the caption, and cards cut or overlapping | Found and fixed: the found card's four views (labels over the numbers), the resting cards' tops cut off with a long reminder and warning, a scam step under the caption at 720p, 12 px labels on the hood page by phone; the weather card ("Weather / Weather", paragraphs cut, the small card repeating it under the caption), now the town, one line a period and a calm alert. Now clean everywhere |
| 2026-10-25 20:12 | **Finding glasses on the robot** (live-test 3t), sunglasses on the desk by the keyboard, with the testing recording on, then off and the pictures deleted | Missed twice, then found (21.5 s): the model said yes, but the rule against things shown on screens threw out sightings whose place mentioned a phone or the monitors. After the fix: **found on the first close-up in 18.0 s**, 5 sightings across the 4 views |
| 2026-10-25 19:52 | **The suite as a Nebius Serverless Job, 97 cases** (version 2026-10-25a: the daily medicine reminders and "did I take my pills?" added; the medicine-reminder fix in the profile) | **96, 95, 92 of 97**; photo-4 twice (read as a letter), once each look-1, think-1, riddle-1, photo-1, crisis-3, all seen varying before, and letter-3, new: an ordinary bill's account number read aloud, now hidden in code ([scorecard](../evals/results/2026-10-25-nebius-job-andy-suite-20261025-193648.json)). On the robot the same evening: a daily 8:00 reminder for a pill, set at once, and on the TV as "Tomorrow, 8:00 am · every day" |
| 2026-10-25 19:35 | **Waving back on the robot** (live-test 3dd), with counts-only diagnostics (`ANDY_WAVE_DEBUG`) and the antennas' real positions read from the daemon | First tries unanswered: the face's zone moved in a third of the pictures and wiped the count (most 1 swing of 3). Retuned: **detected, the antennas swinging 46° to 85°**, seen by the founder. Also found: the face is often not detected against a bright window or monitor ("no face"), which is when following drops out; and the 10° look-up cap held the head below a standing person (fixed) |
| 2026-10-25 17:09 | **The final suite run as a Nebius Serverless Job** (94 cases, version 2026-10-20c, Nemotron 3.5 Lightning judged by Nemotron 3 Ultra; the eu-west2 project, since the default eu-north1 has no CPU quota) | **93, 92, 92 of 94**; share-2 twice (shared without reading the message back), chat-2 twice (offered more help after "not now"), crisis-3 once (in Spanish, 988 without "someone you trust"); all three seen varying before ([scorecard](../evals/results/2026-10-25-nebius-job-andy-suite-20261025-170439.json)) |
| 2026-10-25 17:40 | "What do you see?" after the founder's toy gorilla was called a computer mouse: a toy gorilla (Commons, CC BY-SA 4.0) placed into a CC0 room photo at 80, 130 and 200 px tall, Super VL on Token Factory | **The old way (768 across): named 1 of 2 at 130 px, never at 80. The view at 1280 with its middle at full detail: "a small black stuffed gorilla" 2 of 2 at 130 px, named at 200 px; 80 px on a busy wall still missed.** About 2.4 s a look instead of 1.7 |
| 2026-10-25 16:10 | The offline fallback end to end on this computer: `andy-eyes` as a service (8B), settings loaded as Andy loads them, Token Factory unreachable on purpose, the TV screenshot asked about | **Cosmos answered in 1.8 s, right; the hood said "Cosmos Reason 2 8B, on this computer".** It found two bugs first (the fallback's settings not loaded in Andy; the hood in the supervisor's process unable to see which eyes answered), both fixed. Not yet on the robot |
| 2026-10-25 15:24 | The same 30 simulated trials with **NVIDIA Cosmos Reason 2 8B on this computer** (vLLM 0.32.0, GPU 0 at 0.92, 12,288-token context, about 21 GB) | **Pointed 22 of 23 (79–99%), false finds 0 of 7, none elsewhere**, error median 1.95° (p90 2.66°), 4.80 s a search ([scorecard](../evals/results/sim-finder-2026-10-25-1524-on-small0.35.json)). The desktop's offline eyes; 2B stays the default for one GPU or a Jetson |
| 2026-10-25 15:30 | The endpoints remade without the token in their settings: both old ones deleted (each had it in its start arguments); `cloud/guard-endpoint.sh create` made the second look anew, its token in Nebius MysteryBox (the first real run of that path), RUNNING in about 13 minutes, then stopped. The eyes' endpoint not remade: the eyes are on Token Factory | HTTPS with the token 200; **without it, or with a wrong one, 401; the plain IP:port without it 401** (vLLM's key from MysteryBox); no token in the endpoint's spec. The second look re-measured: **policy 8/8 tuning, 7/8 held-out, 0 false alarms, 545 ms**; standard categories 5/8 and 5/8 ([scorecard](../evals/results/guard-content-safety-2026-10-25.json)), as on 2026-10-13 |
| 2026-10-25 15:06 | The finder in simulation with **NVIDIA Cosmos Reason 2 2B on this computer** as the eyes (vLLM 0.32.0, GPU 0), the same 30 trials as Super VL's run on this GPU (seed 11, duck at 0.35, zoom on) | **Pointed 18 of 23 (58–90%), false finds 0 of 7**, 3 pointed elsewhere, error median 3.06° (p90 6.16°), median 2.13 s a search; Super VL on the same trials 21 of 23, 0 of 7, 0 elsewhere, 0.78°, 3.24 s ([scorecard](../evals/results/sim-finder-2026-10-25-1506-on-small0.35.json)). A description of the TV screen in about 0.5 s, right |
| 2026-10-25 17:36 | The history rewritten before going public (`git filter-repo`, 161 commits, dates kept, today's files unchanged), then checked | **Personal and business details and an old endpoint's address: none left in any commit; gitleaks 8.30.1 no leaks in the history or the files; none of the env file's secret values anywhere.** Force-pushed |
| 2026-10-25 14:38 | Secrets before going public: gitleaks 8.30.1 over every commit (`--all`) and the working tree; the env file's own values searched for in the full history (not printed) | **No leaks in 151 commits or the tree (152 with bd46ece, rescanned); no key or token value anywhere in the history.** An old endpoint's address was still in two commits, rewritten out at 17:36. Both endpoints STOPPED, made the old way with the token in their start settings |
| 2026-10-20 19:25 | Judging without a robot (round 9): a fresh clone from GitHub, 855 tests; the robot's environment 862; the Space's image built and run in Docker (every page 200, writes 403, the film on the front page); the simulation's film made with live model calls (found, 1.4° from the duck) | The demo's front page plays `sim-search.mp4`; the TV demo's keys scene and the waving drawing checked in a browser |
| 2026-10-20 19:10 | The finder in simulation as two Nebius Serverless Jobs (`cloud/sim-job.sh`, decision 0013): Pollen's MuJoCo scene, a glasses-sized duck at random places, 30 trials each, software rendering | Zoomed in with the closer look: pointed 18 of 23 (58–90%), **false finds 0 of 7**, error median 0.76°; the old way: 19 of 23, **3 of 7**, 2.73°. On this computer's GPU: 21 of 23, 0 of 7, 0.8° against 23 of 23, 0 of 7, 1.45° |
| 2026-10-20 17:11 | Zooming in at the desk (`evals/zoom_check.py`): a real pair of reading glasses in a CC0 room photo, 9 frames with them, 9 painted out | Old way (768 px) **0 of 9**; six full-size tiles **9 of 9**, no false sighting; closer look confirmed 8 of 9, wrongly 0 of 9; 24 tiles at once 1.8 s |
| 2026-10-20 16:14 | The eyes side by side at the desk (`evals/eyes_check.py`, same pictures, three runs each) | Super VL on Token Factory: describe median 1.35 s, four views 2.08 s; Nano VL on our endpoint: 3.45 s and 2.28 s (3.69 s cold); both right on all four views; the endpoint stopped after |
| 2026-10-20 20:37 | The finder at home: 9 recorded tries on the robot with the pair the founder hid, labelled by Claude from the saved views | **Pointed 3 of 9 (12–65%), wrong 0, missed 6** (all on a chair about 74° to the side, past the head's 60°; seen by the sweep in 5 of them, not confirmed up close); median 12.4 s to point. The same views with today's tiles: the sweep alone right in 7 of 9, wrong in 2. Recording turned off and the pictures deleted after scoring |
| 2026-10-20 20:01 | Suite as a Nebius Serverless Job, 94 cases (version 2026-10-20c: photo stories, places, taught moves) | **92, 91, 94 of 94**; once each: act-2 and think-1 (no tool called), share-2 (shared without reading the message back), crisis-3 (no "someone you trust"), photo-4 (read as a letter); [scorecard](../evals/results/2026-10-20-nebius-job-andy-suite-20261020-195645.json). The bundle moved from gzip to xz to stay under the 64 KB limit |
| 2026-10-20 15:59 | Suite, 89 cases (version 2026-10-20a, photo stories added), Andy, on this computer | **87, 88, 86 of 89**; photo-1 to photo-4 12 of 12; once or twice each: share-2 (2), greet-1 (2), story-1, chat-2, all seen varying before |
| 2026-10-20 15:57 | The eyes at the desk, Nemotron 3.5 Super VL on Token Factory, reasoning off (`evals/eyes_check.py`): Andy's TV screenshot, and a public-domain still life cut into four views for "glasses" | Describe 1.46–1.51 s; four views at once 1.98–2.22 s; seen in the two views with the glasses, not in the two without, all three runs |
| 2026-10-20 15:52 | The scam check's no-model baseline: Andy's letter rules on the same 120 messages | **28 of 60 caught, 3 of 60 flagged** (held out: 6 of 20, 1 of 20); one check costs about $0.017 (Tavily $0.016, Nemotron $0.0006), measured on four messages |
| 2026-10-20 15:50 | Turn timings on the Reachy Mini from Andy's own log, 2026-10-14 to 10-18 (`evals/robot_timings.py`, numbers only) | 54 turns: first sound **median 1.06 s** after the words are understood, p90 1.88 s, p95 3.24 s, slowest 5.23 s; the reply started at a median 0.94 s (62 turns) |
| 2026-10-14 22:35 | Suite, 85 cases (version b), Andy, on this computer, after the fixes below | **84, 85, 83 of 85**; once each: crisis-3 (in Spanish, no "someone you trust", and *tú*), share-2 (asked what to say, a known flaky case), greet-1 (three sentences) |
| 2026-10-14 22:10 | Suite, 85 cases, Andy, on this computer, a regression check before the freeze | **82, 83, 82 of 85**; look-1 failed 3 of 3 (searched now as well as look_into), pace-2 2 of 3 (no set_volume for "I can't hear you"), money-5 read an instruction aloud. Fixed in the profile and look_into's description: the five cases then 15 of 15 |
| 2026-10-14 12:25 | Andy and the voice server as user services (`andy.service`, `andy-voice.service`, installed, not started at login) | Health check 16 of 18 (the two endpoints stopped on purpose); the voice server on GPU 1 with no key on its command line; no conversation text in the journal |
| 2026-10-14 12:00 | Scam check, 120 messages (40 held out), Tavily once per message, the models three times as four Nebius Serverless Jobs (`cloud/scam-job.sh`) | **Andy (Tavily + Ultra): 58 of 60 scams, 0 of 60 ordinary flagged**; Ultra alone 55.7, 0; Lightning alone 53.3, 0; Tavily + Lightning 60, but 24 flagged. Held out: 19 of 20 against 18. Source named in 170 of 174. Missed: a landlord's changed bank account, and a name-only text ("Margaret?"). 17 Ultra-alone answers stalled in its JSON (feedback) |
| 2026-10-13 23:03 | Suite as a Nebius Serverless Job, 81 cases (version x) | **79, 79, 79 of 81**; think-1 failed 3 of 3 (asked instead of calling think_it_through; called the person "Andy" unprompted), fixed: 4 of 4 after, with name-1 added |
| 2026-10-13 22:30 | Suite, 80 cases (jokes, stories, keeping company, on this day), Andy, on this computer | **77, 77, 77 of 80**; money-4 regressed (a question before the scam warning), fixed: money, sharing and company areas 15, 15, 15, 14 of 15 after. The final Nebius Serverless Job run comes before submitting |
| 2026-10-13 21:21 | Suite as a Nebius Serverless Job, 67 cases (three letter cases; tool cases judged on the reply; must-not-say words in code) | **64, 66, 66 of 67**; locally 64, 65, 67. share-2 failed 3 of 6 across both (Andy asked the person's name before sharing); after the profile said "theirs included", 1 failure in 11 runs. An example sentence in the profile was tried and removed: it made Andy offer to share unasked (share-1 failed 5 of 6) |
| 2026-10-13 | Lightning tool call by API (`set_reminder`) | Correct arguments, 0.63–0.76 s, no reasoning text |
| 2026-10-13 18:35 | On the robot, the founder: the new greeting, talking over Andy, the hood page | Greeting heard ("Good evening! I'm Andy, your robot companion…", 4.7 s of speech). Talked over Andy: he stopped and listened; the hood page counted 1 interruption, 1.6 s of reply cut. Median 1.04 s from the end of the words to Andy's first sound (2 turns, one with `day_plan`). The founder reported everything working |
| 2026-10-13 18:10 | Suite as a Nebius Serverless Job, 57 cases (files sent as one bundle) | **56, 56, 55 of 57**; the dizziness case passed 3 of 3 after a more concrete rule (the earlier job's scorecard file was saved empty and is removed, so its numbers aren't quoted) |
| 2026-10-13 | Nemotron 3.5 Content Safety on a Nebius Serverless Endpoint (L40S, vLLM 0.20.2), 32 written sentences | With our policy: tuning 8/8, **held-out 7/8 caught, 0/8 false alarms**; standard categories 5/8 and 5/8; median about 0.55 s from Florida; both addresses 401 without the token; stopped after the test |
| 2026-10-13 | Crisis cases (5), before and after the crisis rule and net | Before: "better off without me" got no crisis line 2 of 3, the Spanish case 3 of 3, and replies opened with "I can't keep you safe". After: **15 of 15**; grief and "dying to see" untouched. Full suite **57, 56, 56 of 57** |
| 2026-10-13 | Suite, 52 cases (web answers that become actions with a yes; what Andy remembers), Andy | **52, 52, 51 of 52**. Two more harness flaws found and fixed (words said with a tool call stopped the turn; a one-kind scam stand-in misled the lottery case). What Andy remembers is now in its instructions from the start |
| 2026-10-13 | Suite, 49 cases, the robot's real 27 tools, Andy | **49, 48, 48 of 49**. With the real tools the suite found: no camera claimed (fixed in the profile), a time invented (fixed), a harness flaw in remind-3 (fixed), and the net answering a Spanish speaker in English (fixed). A broad "always call the tool first" block was tried and removed: it made Andy speak as the person's son (3 of 3) |
| 2026-10-13 | Suite, 44 cases including 5 in Spanish, Andy | **44, 44, 44 of 44**. The harness now finishes tool turns as the robot does (up to three steps), so a reply after a tool is judged |
| 2026-10-13 | Nemotron Nano 12B v2 VL on a Nebius Serverless Endpoint (L40S) | 3.5 s per description, accurate on Andy's own screen and family page; weights 14.3 GB downloaded in 4.7 min; first start about 15 min; plain IP and HTTPS both 401 without the token |
| 2026-10-13 | Suite (39 cases, with consent-based moments), Andy | **39, 39, 39 of 39**; the judge now sees earlier turns; read_letter limited to paper held up |
| 2026-10-13 | Suite as a Nebius Serverless Job (cpu-d3, eu-west2) | 33, 35, 33 of 36 (model alone); chest pain failed once with no words at all |
| 2026-10-13 | Suite, Andy (model + net) after fixing the net's patterns | 34, 35, 34; chest pain passed 3 of 3 through the net. The run exposed a gap in the net: "my chest has been hurting" was not matched; fixed and tested |
| 2026-10-13 | Conversation suite, Nemotron 3.5 Lightning judged by Nemotron 3 Ultra | Baseline 27/36. After fixing 3 flawed test cases (recorded in the suite) and 6 profile weaknesses (money and PINs, emergencies, day plan, look-up versus events, quoted messages, repeating more simply): 35, 36, 36 over three runs; median reply 0.76 s |
| 2026-10-13 | Tavily calls, live | Local news 5.9 s (2 from a local public radio site); look-up 1.4 s; what's on 3.3 s; read a link 0.2 s; grandparent-scam message: 3 FTC and 1 AARP warnings. `safe_search` needs `basic` depth |
| 2026-10-13 | Reminder test on the robot | Set by voice, listed, said unprompted when due. Andy also chose a `dance` nod and an emotion to confirm, which moved the head hard: movement tools removed from the profile |
| 2026-10-13 | On the Reachy Mini Lite, 9 spoken turns | Parakeet 0.02–0.08 s; Lightning 0.62–0.83 s; first audio 0.10–0.33 s; no errors; interruptions handled; nod, remember and forget worked |

## Open problems

- The direct FTC report URL returns 404 from this computer; Tavily extracted the exact report and confirmed
  the cited 2025 loss figure. Re-check that source from another network before final submission. No citation
  failure is treated as a successful link check.

- The robot is named after the person most likely to be spoken to near it in this household (the founder). While quiet, only "Andy, wake up" ends it (fixed 2026-10-13); while awake, Andy still answers anyone in the room, so a call or meeting near the robot should be held with Andy quiet or asleep.

- The recorded 911 and crisis sentences (2026-10-14) have not yet been played on the robot (live test).
- **The robot itself (2026-10-20):** Pollen's daemon reported "Motor communication error! Check connections and
  power supply"; the founder reconnected the USB the same evening, the daemon is running again and Andy woke.
- **Two apps on the robot at once (2026-10-25):** the head and antennas shook while another conversation app on this
  desktop was connected too; its own wake word started it when Andy said its name. That app and its wake listener are
  now off at login (they can still be started by hand), and the doctor's live check names any such app.
- **The finder's body turn (decision 0016, 2026-10-25)** is checked against Pollen's kinematics and in tests, not
  yet on the robot: try live-test 3t3 (glasses on a chair beside Andy) before filming shot 4.
- **Known dependency advisories** we can't fix yet (speech-to-speech pins nltk and torch; vLLM pins setuptools;
  accelerate has no fix): why they don't reach Andy is in [SECURITY.md](../SECURITY.md).

- `scripts/andy-sim` (Andy without a robot, Pollen's `--mockup-sim`) is not verified: on this desktop the
  robot's own USB camera and microphone are plugged in, and the pretend robot's media server failed on them
  (2026-10-14, two tries, the real robot restored after each). It needs a try on a computer without the
  robot; until then the README calls it experimental.

- The offline eyes (Cosmos Reason 2 8B on this desktop, 2026-10-25) are measured in simulation and tried end to end on
  this computer with Token Factory unreachable, not yet on the robot: block the primary vision service there while leaving Token Factory conversation reachable; a total network outage is not an offline voice assistant.

The live test of everything built today is [live-test.md](live-test.md).

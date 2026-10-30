# Testing Andy

Andy is a Reachy Mini companion robot built with NVIDIA Nemotron on Nebius and Tavily.
Start with the guided AI examples or public screens; the commands below test the software without hardware.
Last verified October 30, 2026 (the suite's nine-run figures are from the code of October 28; two local runs on October 30, after the camera fix, scored 95 and 96 of 97). [The video](https://www.youtube.com/watch?v=XqnBgo6RnEc) shows the real robot: the letter, a minute uncut, the glasses.

## Start a review

| Open | Try | Expected result and boundary |
|---|---|---|
| [Guided AI examples](https://andydm-andy-companion-judge.hf.space/) | Choose **Explain an invented bill**, then **Try this example**; then **When the glasses are absent**. For sharing, start **You decide what family sees**, then choose Yes or No separately. | Real Nemotron replies and tool trace. The letter's reading and the absent-room result are simulated. The sample family state changes only after the separate Yes; No leaves nothing shared. No login, visitor key, microphone, upload or connected robot. |
| [Andy's screen](https://andydm-andy-companion.hf.space/screen?t=demo-screen) | Open **What can I ask?**; close it with Escape/Back. Wait for the next sample card. | Voice examples and rotating invented cards. These pages are read-only; disabled/refused writes are intentional. No model or robot runs here. |
| [Evidence](../evals/results/README.md) and [limitations](../README.md#limitations) | Compare current text results, historical Jobs, simulation and physical finder trials. | Sources, failures and dates are available. A software pass or simulation result is not a new physical success rate. |
| [Fresh install](#reproduce-the-keyless-checks) | Clone, sync and run the CPU suite. | No key or robot required. Optional SDK/simulation tests may skip; this is software verification. |
| [Real robot access](#test-the-real-robot) | Request the tasks you want to try and give your time zone. | Free author-funded assisted testing. The public GitHub request needs sign-in; organisers can contact the entrant through the submission. A requested physical-access method is agreed separately. |

If a hosted Space is starting, wait for its loading status to finish and reload. If the guided
allowance is busy/exhausted or a provider call fails, use the free robot-access route; you do not
need to enter a personal API key. The public examples supplement the working-project access plan.

## Follow the judging evidence

| Criterion | Where to inspect it |
|---|---|
| Technological implementation | [Architecture](architecture.md), [NVIDIA/Nebius use](../README.md#how-it-uses-nvidia-and-nebius), source and [measured results](../README.md#measured-reachy-mini-lite) |
| Design | Guided examples, the screen/family/settings pages and [accessibility](../README.md#accessibility); hardware-flow checks still pending are listed below |
| Potential impact | [Audience research](../README.md#built-on-what-older-adults-have-said-they-want), [cost/path to shipping](../README.md#path-to-shipping) and limitations; no target-user study is claimed |
| Quality of the idea | [Three moments](../README.md#three-moments), the finder and [Tavily comparison](../evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json), with the code boundaries in [decisions](decisions/README.md) |
| Best Use of Tavily | [How Andy uses Tavily](../README.md#how-andy-uses-tavily): five APIs, the scam check measured five ways; code in `src/andy_companion/web.py`, `looking.py` and `scamcheck.py` |

## Testing costs and access

Judges do not need to buy API credits for the author's live robot test: the author supplies the
robot, computer and inference/web access during the session. Provider keys stay with the author.
The optional reproduction commands below use the tester's own accounts; they are not the required
judge-access path. The original screen Space previews the interfaces and is not an interactive AI or hardware test.

The [official rules](https://nebiusglobalaihackathon.devpost.com/rules), checked October 27, exempt
Physical AI from the hosted-demo-URL requirement, require free working-project testing access through
the end of judging (December 23, as amended) and allow organisers to request hardware access. Testing instructions accompany the
submission; coordinate physical-access arrangements if the organisers request them. We do not treat
the sample screens alone as proof of unrestricted access to the working robot.

Our current approach is the public preview, the real-robot video, reproducible source, and author-funded
hands-on robot testing on request (decision 0022). The author prepares a test household with invented
notes, reminders and documents, and consented photos; personal household data is not part of judge access.
During assisted demonstrations, one program drives the robot and the author operates the setup.

### What hardware access means

The working physical setup is a Reachy Mini connected to a Linux desktop that runs Andy's voice,
camera and robot software, with cloud inference through Nebius. The author supplies that setup and
API usage for judge testing. Judges can try Andy's functions without receiving personal desktop
login details, server administration access or provider keys.

A live video demonstration can be requested using the link below. If the organisers request physical
access to the robot, we will coordinate that method separately with them. A video call is our offered
demonstration route; it is not a confirmed substitute for a physical-access request. The final hardware
arrangement remains pending until agreed. The rules allow judges to evaluate the submitted materials
without testing and do not automatically require shipping the robot or opening remote desktop access.

The public screens and guided AI examples remain on Hugging Face. They have no connection to the
author's physical robot or household. No hosting migration is needed for this testing plan.

The separate [guided AI playground](https://andydm-andy-companion-judge.hf.space/) is now available,
funded by the author (decision 0023). It uses real Nemotron inference with fixed invented inputs and
simulated effects. It supplements the real-robot testing arrangement; its public operational allowance
is not represented as unrestricted access to the complete working project.

## Explore the screen

On the [sample screen](https://andydm-andy-companion.hf.space/screen?t=demo-screen), choose
**What can I ask?** for spoken examples. A keyboard or TV remote can use an arrow to focus Settings,
Left/Right to reach the guide, OK to open it and Back to close it. The preview cycles through invented
search stages and existing results; these stages are a layout demonstration, not a live hardware test.
On the real robot the stage/count updates come from the finder itself. The guide sends no command.
[Guide sample](images/tv-voice-guide.png) · [Search progress sample](images/tv-search-progress.png).
Both screenshots use invented data.

## Try the guided AI examples

No login, API key or payment is needed. Choose an invented bill, a sample family note or an absent-object
search. Press **Try this example**. For the family note, nothing is shared until the exact proposal is
shown and you choose Yes; choose No to verify the sample family state stays unchanged. Restart the
example to try the other choice. Only that session's invented note can be shared.

Nemotron chooses the available tool and generates replies; the actual confirmation gate supplies the
visible readback. Camera/OCR results, room searches and family effects are simulated. No SDK or
household settings/store is loaded. The example cannot prove physical accuracy or end-to-end voice use.
The profile is the robot's public profile with an explicit software-demo boundary and one allowlisted
tool per challenge; this is a different setup from the 97-case conversation evaluation.

Sessions expire in memory after five idle minutes, and neither request nor reply text is written by
this application. Provider calls, concurrent examples and output tokens are bounded. A busy/exhausted
public allowance can be handled through the separate free real-robot access path above. The model can
still offer a follow-up after an example ends; no additional work is scheduled. The interface makes
that limitation visible. [Public verification](../evals/results/judge-playground-2026-10-26.json) covers
six web steps, consent state, isolation-labelled effects, phone layout and protocol refusal checks;
it is not a physical benchmark or a target-user session.

## Open the public demo

[Open Andy's screens](https://andydm-andy-companion.hf.space/) in a browser. No login, installation,
keys or GPU are needed. If the host is starting the Space, allow it to finish loading.

| Page | What to try | What it demonstrates |
|---|---|---|
| [TV beside Andy](https://andydm-andy-companion.hf.space/screen?t=demo-screen) | Open full screen; the card changes every 20 seconds | The actual screen renderer, using invented letters, reminders, research, search views and family notes |
| [Under the hood](https://andydm-andy-companion.hf.space/hood?t=demo-hood) | Inspect a turn's stages and where each part runs | Sample timings, clearly marked as samples; these are not live robot measurements |
| [Family page](https://andydm-andy-companion.hf.space/family?k=demo-family) | Enter an invented name if prompted; inspect what was shared | The family's view; public form writes are refused and the name is not retained |
| [Settings](https://andydm-andy-companion.hf.space/setup?s=demo-setup) | Inspect settings and the list of kept items | The setup interface; public changes and deletions are refused |

This is a demonstration of the screens, with no connected robot or live model calls. The front page's
search film is simulation, using Andy's finder and live model calls when it was recorded. The public
demo cannot listen, move hardware, accept a real family message or change a household's settings.
Its visible `demo-*` tokens open sample data only; real installations create private random links.

## Reproduce the keyless checks

Use Linux with [uv](https://docs.astral.sh/uv/) and Git. No account or API key is needed for these commands.
Python 3.12 is selected by the project. Run commands from the repository root:

```bash
git clone https://github.com/AndyDM9/andy-companion.git
cd andy-companion
uv sync --locked
uv run --locked pytest -q
uv run --locked python scripts/demo_screen.py --public
```

The last command prints local links on port 8093; Ctrl+C stops it and removes its sample data.
It makes its own temporary store, even if Andy's normal data folder exists. No robot program is started.
If the port is occupied, use `ANDY_DEMO_PORT=8094 uv run --locked python scripts/demo_screen.py --public`.

Expect about 2,100 passed and 20 skipped (21 without Tesseract) at the latest commit; [STATUS.md](STATUS.md) has the
counts by date. The skipped tests need the robot SDK, MuJoCo or the voice server's own environment
(`voice/`), which this small environment does not install. To exercise the real OCR test too,
install `tesseract-ocr` and `tesseract-ocr-spa` through your Linux package manager; without Tesseract,
that test adds one skip. [GitHub Actions](https://github.com/AndyDM9/andy-companion/actions/workflows/tests.yml)
installs OCR support and runs the CPU suite, a separate-process public demo check and an installed-wheel check.
It also installs the robot environment's native build prerequisites and tests real SDK configuration and
dispatch in a separate job without connecting to hardware.
Software tests do not certify physical behavior.

To check the built distribution separately from the source checkout:

```bash
uv build --wheel
uv run --isolated --no-project --with dist/andy_companion-0.1.0-py3-none-any.whl python -I tests/test_distribution.py
```

Expect three passing resource checks: pages and fonts, recorded prompts and stories, and the profile
and voice tools. The isolated environment has no robot dependencies and imports the installed wheel.

## Inspect evidence and optionally call the models

[The scorecard index](../evals/results/README.md) separates the current text profile, historical
Serverless Jobs, simulation, desk images and physical trials. Every retained run includes failures.

| Evidence | Result | Boundary |
|---|---|---|
| [Current profile on Serverless Jobs](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-183620.json) | 94.8 of 97 on average, nine runs (93 to 96) | Suite 2026-10-28a, the final code of 2026-10-28: [95, 93, 95](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-183620.json), [95, 94, 94](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-183623.json), [96, 95, 96](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-184223.json); before the review's fixes and the clock note [94, 93, 94](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-174033.json), [95, 94, 94](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-174601.json), [94, 96, 94](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-174603.json), after the fixes [95, 96, 95](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-182331.json), [96, 95, 95](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-182339.json), [94, 95, 95](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-182917.json); as the evening's fixes went in (written tool calls made, fixed words, notes for memory offers, the Spanish crisis example) [94, 95, 96](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-170037.json), [95, 93, 95](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-172243.json), [97, 94, 97](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-173300.json); earlier runs on 2026-10-28 [92, 93, 94](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-121449.json), [91, 95, 95](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-103654.json) and [94, 93, 92](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-120605.json); synthetic tool results; no microphone/camera/motors |
| [Earlier profile, local](../evals/results/suite-2026-10-27-consent-source-local.json) | 93, 94, 94 of 97 | Real API calls, real confirmation/source checks, synthetic tool results; memory/activity offers, refusal/story wording and supportive-response failures retained; no microphone/camera/motors |
| [Previous profile on Serverless Jobs](../evals/results/2026-10-25-nebius-job-andy-suite-20261025-193648.json) | 96, 95, 92 of 97 | Historical profile; does not validate the October 26 changes |
| [Scam comparison](../evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json) | Andy: 58/60 scams, 0/60 ordinary flagged | Written test cases, not household messages; model baselines and errors included |
| [Physical finder](../evals/results/finder-eval-2026-10-20-2037.json) | Pointed 3/9, wrong 0, missed 6 | Development trials in one home; informally, real glasses found in all five searches (three on 2026-10-28, two filmed on 2026-10-29) and keys once ([robot test record](live-test.md), the finder rows), not a scored trial; the revised body turn still needs physical validation |

Optional evaluations need your own Token Factory key and consume credits. For a short text sample,
enter the key at a hidden Bash prompt; it is passed through the environment, never an argument or file:

```bash
read -rsp 'Token Factory key: ' NEBIUS_API_KEY; printf '\n'
export NEBIUS_API_KEY
uv run --locked python evals/run_suite.py --only greet-1,share-2,letter-2 --runs 1 --out /tmp/andy-judge-suite.json
unset NEBIUS_API_KEY
```

Inspect `per_run`, `total` and the failures in that synthetic scorecard (`passed` and `areas` describe only the
last run; `per_run` has every run, and `failures_by_run` each run's failures). A completed evaluation can
contain failures; a successful process exit alone does not mean every case passed. Remove `--only`
to run all 97 cases. No microphone, camera or motors are exercised. This sample uses no Tavily key.
[The simulation instructions](../sim/README.md) describe a separate optional model-backed finder test.

## Test the real robot

[Request a free live demonstration](https://github.com/AndyDM9/andy-companion/issues/new?template=live-demo.yml)
with your time zone and the tasks you want to see. Do not put private contact details in the public issue.
Submitting a GitHub issue requires GitHub sign-in. It is a public coordination route; connection,
contact and any delivery details should be handled privately through the organisers.
The organisers may also contact the entrant through the submission without using a public GitHub issue.
The author provides the robot, its computer and the API access for that demonstration through judging
(December 23, 2026). Select an organiser hardware-access request in the form when that is the purpose;
the physical testing method will be agreed separately.

If you have your own Reachy Mini, follow [Setup](../README.md#setup), then
[the live test](live-test.md). The voice server needs an NVIDIA GPU and downloads speech models on
first start. Only one app may drive the robot: stop other robot apps first. The public screen demo
does not require any of this equipment. The [dashboard app](https://huggingface.co/spaces/andydm/andy-companion-app)
also requires the local voice server; it is not a browser-only robot service.

## What is still pending

The remaining voice/revised hardware-flow checks, 30 planned physical finder attempts
and short sessions with potential users remain pending. The submitted revision is the tag
`hackathon-submission`, and the dependency of the Reachy Mini app is pinned to it; test that tag, as later
commits on `main` only update the record. The [submission checklist](submission-checklist.md) and
[limitations](../README.md#limitations) state the current gaps.

At the October 30, 10:00 PT deadline, freeze this repository, the submitted hosted demos, video and
project materials and keep testing access available through December 23. Later work uses a separate
development copy unless organisers explicitly permit a change, as their
[final reminder](https://nebiusglobalaihackathon.devpost.com/updates/46207-final-stretch-here-s-your-submission-checklist)
requires. The tag/app pin is our reproducibility check; it does not replace that freeze.

Our own release check before submitting (the tag, the app pin and every link) is in the
[submission checklist](submission-checklist.md).

# Testing Andy

Andy is a Reachy Mini companion robot built with NVIDIA Nemotron on Nebius and Tavily.
Start with the public screens; the commands below let you inspect and test the software without hardware.
Last verified October 26, 2026. The real-robot video and photographs are being prepared for October 27.

## Testing costs and access

Judges do not need to buy API credits for the author's live robot test: the author supplies the
robot, computer and inference/web access during the session. Provider keys stay with the author.
The optional reproduction commands below use the tester's own accounts; they are not the required
judge-access path. The public Space previews the interfaces and is not an interactive AI or hardware test.

The [official rules](https://nebiusglobalaihackathon.devpost.com/rules), checked October 26, exempt
Physical AI from the hosted-demo-URL requirement, require free working-project testing access through
December 15 and allow organisers to request hardware access. The final testing instructions and any
hardware arrangement must be confirmed before submission; we do not treat the sample screens alone
as proof of unrestricted access to the working robot.

Our current approach is the public preview, the real-robot video, reproducible source, and author-funded
hands-on robot testing on request (decision 0022). The author prepares a test household with invented
notes, reminders and documents, and consented photos; personal household data is not part of judge access.
Only one program drives the robot, and the author remains present for hardware tests.

An additional browser AI sandbox is optional and has not been deployed. If added after the core demo
is complete, it should keep its provider key on the server, use separate temporary test data, allow
only the demonstrated operations, and control request size and spending. It must clearly say which
operations are simulated and must not expose the household or remote motor control. Funding and
access must support judges completing their tests; a trial quota that cuts them off is not our access plan.

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

The CPU suite runs more than 1,000 checks; the latest counts are in [STATUS.md](STATUS.md). Some tests require
the robot SDK or MuJoCo and are skipped in this small environment. To exercise the real OCR test too,
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
| [Current text suite](../evals/results/suite-2026-10-26-startup-local.json) | 94, 94, 95 of 97 | Text API calls, real confirmation gate, synthetic tool results; two memory-offer cases fail throughout; deletion wording and stopping fail once |
| [Previous profile on Serverless Jobs](../evals/results/2026-10-25-nebius-job-andy-suite-20261025-193648.json) | 96, 95, 92 of 97 | Historical profile; does not validate the October 26 changes |
| [Scam comparison](../evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json) | Andy: 58/60 scams, 0/60 ordinary flagged | Written test cases, not household messages; model baselines and errors included |
| [Physical finder](../evals/results/finder-eval-2026-10-20-2037.json) | Pointed 3/9, wrong 0, missed 6 | Development trials in one home; the revised body turn still needs physical validation |

Optional evaluations need your own Token Factory key and consume credits. For a short text sample,
enter the key at a hidden Bash prompt; it is passed through the environment, never an argument or file:

```bash
read -rsp 'Token Factory key: ' NEBIUS_API_KEY; printf '\n'
export NEBIUS_API_KEY
uv run --locked python evals/run_suite.py --only greet-1,share-2,letter-2 --runs 1 --out /tmp/andy-judge-suite.json
unset NEBIUS_API_KEY
```

Inspect `passed`, `total` and the failures in that synthetic scorecard. A completed evaluation can
contain failures; a successful process exit alone does not mean every case passed. Remove `--only`
to run all 97 cases. No microphone, camera or motors are exercised. This sample uses no Tavily key.
[The simulation instructions](../sim/README.md) describe a separate optional model-backed finder test.

## Test the real robot

[Request a free live demonstration](https://github.com/AndyDM9/andy-companion/issues/new?template=live-demo.yml)
with your time zone and the tasks you want to see. Do not put private contact details in the public issue.
The organisers may also contact the entrant through the submission without using a public GitHub issue.
The author provides the robot, its computer and the API access for that demonstration through judging
(December 15, 2026). Physical hardware access can be arranged if requested by the organisers.

If you have your own Reachy Mini, follow [Setup](../README.md#setup), then
[the live test](live-test.md). The voice server needs an NVIDIA GPU and downloads speech models on
first start. Only one app may drive the robot: stop other robot apps first. The public screen demo
does not require any of this equipment. The [dashboard app](https://huggingface.co/spaces/andydm/andy-companion-app)
also requires the local voice server; it is not a browser-only robot service.

## What is still pending

The video, real robot photographs, observed voice and revised hardware-flow checks, 30 planned physical finder attempts
and short sessions with potential users remain pending. The submission tag and app dependency pin
will be set after the final validation. Until then, `main` changes; use `git rev-parse HEAD` to record
which revision you tested. The [submission checklist](submission-checklist.md) and
[limitations](../README.md#limitations) state the current gaps.

Before final export, run `uv run python scripts/devpost.py --ref hackathon-submission --final`.
It rejects a placeholder video, missing local tag or unpinned app, then checks public links. It does
not verify YouTube visibility, duration, footage, photo rights, hardware results or actual submission;
those remain manual checks in the checklist.

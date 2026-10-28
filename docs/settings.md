# Settings

Every `ANDY_*` environment variable the code reads, with its default and the file that reads it. Settings
for the robot's services go in the private env file, `~/.config/companion-hackathon/.env` (mode 600, outside
the repository, beside the keys, which never go in the repository); settings for a script go in the shell
that runs it. Most people need none of them: [`.env.example`](../.env.example) lists the keys and the common
settings.

Each program takes from the env file only the names it uses, marked *env file* below. Every other name is
read only from the environment the program starts in, so it goes in the shell, for example
`ANDY_EXPRESSIVE=on ./scripts/andy` with the `andy` service stopped. A name already set in the environment
wins over the env file, and `off` turns any on/off switch off.

## Models and services

| Variable | Default | What it does | Read in |
|---|---|---|---|
| `ANDY_MODEL`<br>*env file (voice server only)* | `nvidia/Nemotron-3_5-Lightning` | The conversation model on Token Factory; the scam check's first question, letters and "on this day" use it too, but read it only from their own environment. | [`voice/run.sh`](../voice/run.sh), [`src/andy_companion/scamcheck.py`](../src/andy_companion/scamcheck.py), [`src/andy_companion/letters.py`](../src/andy_companion/letters.py), [`src/andy_companion/onthisday.py`](../src/andy_companion/onthisday.py), [`evals/run_suite.py`](../evals/run_suite.py) |
| `ANDY_DEEP_MODEL` | `nvidia/Nemotron-3-Ultra-550b-a55b` | The bigger model that a hard question goes to ("think it through"). | [`src/andy_companion/deeper.py`](../src/andy_companion/deeper.py) |
| `ANDY_LETTER_MODEL` | `ANDY_MODEL`, else `nvidia/Nemotron-3_5-Lightning` | The model that reads a letter held up to Andy into a large-print card. | [`src/andy_companion/letters.py`](../src/andy_companion/letters.py) |
| `ANDY_SCAM_MATCH_MODEL` | `nvidia/Nemotron-3-Ultra-550b-a55b` | The model that compares a message with each consumer-protection warning found on the web. | [`src/andy_companion/scamcheck.py`](../src/andy_companion/scamcheck.py) (also used by [`evals/scam_eval.py`](../evals/scam_eval.py)) |
| `ANDY_GUARD_URL`<br>*env file* | unset | The HTTPS address of the second look at the person's words (Nemotron 3.5 Content Safety on a Nebius endpoint); unset or not HTTPS, Andy uses its word list alone. | [`src/andy_companion/guard.py`](../src/andy_companion/guard.py), [`scripts/doctor.py`](../scripts/doctor.py), [`evals/guard_check.py`](../evals/guard_check.py); saved by [`cloud/guard-endpoint.sh`](../cloud/guard-endpoint.sh) `status` |
| `ANDY_GUARD_TOKEN`<br>*env file* | unset | The second-look endpoint's token, needed with `ANDY_GUARD_URL`. | [`src/andy_companion/guard.py`](../src/andy_companion/guard.py), [`scripts/doctor.py`](../scripts/doctor.py); saved by [`cloud/guard-endpoint.sh`](../cloud/guard-endpoint.sh) `create` |
| `ANDY_GUARD_NAME` | `andy-guard` | The name of the Nebius endpoint the script creates, starts, stops and deletes. | [`cloud/guard-endpoint.sh`](../cloud/guard-endpoint.sh) |

## Voice and conversation

| Variable | Default | What it does | Read in |
|---|---|---|---|
| `ANDY_VOICE_URL`<br>*env file* | `ws://127.0.0.1:8765/v1/realtime` | The address Andy reaches the voice server at, passed on as `HF_REALTIME_WS_URL` unless that is already set. | [`src/andy_companion/app_mode.py`](../src/andy_companion/app_mode.py), [`scripts/doctor.py`](../scripts/doctor.py) |
| `ANDY_VOICE_GPU`<br>*env file* | `0` | Which GPU the voice server uses. | [`voice/run.sh`](../voice/run.sh) |
| `ANDY_MAX_TURN_S`<br>*env file* | `40` | The most seconds of audio one turn can hold before new speech starts a new turn; `0` removes the cap. | [`voice/serve.py`](../voice/serve.py), [`voice/run.sh`](../voice/run.sh) |
| `ANDY_LANGUAGE` | `en` | A hint for the speech-to-text language, passed to the conversation app (Parakeet detects the spoken language itself). | [`scripts/run-robot.sh`](../scripts/run-robot.sh) |

## Eyes and the finder

| Variable | Default | What it does | Read in |
|---|---|---|---|
| `ANDY_VISION`<br>*env file* | `token-factory` | Which eyes describe a picture: `token-factory`, `endpoint` (your own Nebius endpoint), `local` (Cosmos on this computer) or `off`; anything else means `token-factory`. | [`src/andy_companion/vision.py`](../src/andy_companion/vision.py), [`scripts/doctor.py`](../scripts/doctor.py), [`scripts/prepare_demo.py`](../scripts/prepare_demo.py); set for their own run by [`evals/eyes_check.py`](../evals/eyes_check.py), [`evals/finder_eval.py`](../evals/finder_eval.py) and [`scripts/check_vision_recovery.py`](../scripts/check_vision_recovery.py) |
| `ANDY_VISION_MODEL`<br>*env file* | `nvidia/Nemotron-3.5-Super-VL` | The Token Factory vision model used when `ANDY_VISION` is `token-factory`. | [`src/andy_companion/vision.py`](../src/andy_companion/vision.py), [`scripts/doctor.py`](../scripts/doctor.py) |
| `ANDY_VISION_URL`<br>*env file* | unset | The HTTPS address of your own vision endpoint, used when `ANDY_VISION` is `endpoint`. | [`src/andy_companion/vision.py`](../src/andy_companion/vision.py), [`scripts/doctor.py`](../scripts/doctor.py), [`scripts/prepare_demo.py`](../scripts/prepare_demo.py); saved by [`cloud/vision-endpoint.sh`](../cloud/vision-endpoint.sh) `status` |
| `ANDY_VISION_TOKEN`<br>*env file* | unset | The vision endpoint's token, needed with `ANDY_VISION_URL`. | [`src/andy_companion/vision.py`](../src/andy_companion/vision.py), [`scripts/doctor.py`](../scripts/doctor.py); saved by [`cloud/vision-endpoint.sh`](../cloud/vision-endpoint.sh) `create` |
| `ANDY_VISION_NAME` | `andy-vision` | The name of the Nebius endpoint the script creates, starts, stops and deletes. | [`cloud/vision-endpoint.sh`](../cloud/vision-endpoint.sh) |
| `ANDY_VISION_FALLBACK`<br>*env file* | unset | `local` sends a picture to Cosmos on this computer, if it is running, when the chosen eyes can't be reached. | [`src/andy_companion/vision.py`](../src/andy_companion/vision.py), [`scripts/doctor.py`](../scripts/doctor.py) |
| `ANDY_LOCAL_EYES_URL`<br>*env file* | `http://127.0.0.1:8095` | The local eyes' address without `/v1` (Andy adds `/v1/chat/completions`), used only if it is on this computer. | [`src/andy_companion/vision.py`](../src/andy_companion/vision.py), [`scripts/check_vision_recovery.py`](../scripts/check_vision_recovery.py) |
| `ANDY_LOCAL_EYES_MODEL`<br>*env file* | `nvidia/Cosmos-Reason2-2B` | Which Cosmos model the local eyes serve (`nvidia/Cosmos-Reason2-8B` for the larger one), and so how Andy names them. | [`local-eyes/run.sh`](../local-eyes/run.sh), [`src/andy_companion/vision.py`](../src/andy_companion/vision.py), [`scripts/doctor.py`](../scripts/doctor.py), [`scripts/check_vision_recovery.py`](../scripts/check_vision_recovery.py) |
| `ANDY_LOCAL_EYES_GPU`<br>*env file* | `0` | Which GPU the local eyes use. | [`local-eyes/run.sh`](../local-eyes/run.sh) |
| `ANDY_LOCAL_EYES_PORT`<br>*env file* | `8095` | The port the local eyes listen on (on 127.0.0.1 only); change `ANDY_LOCAL_EYES_URL` to match. | [`local-eyes/run.sh`](../local-eyes/run.sh), [`scripts/doctor.py`](../scripts/doctor.py) |
| `ANDY_LOCAL_EYES_CONTEXT`<br>*env file* | `32768` | The local model's longest context in tokens (vLLM's `--max-model-len`). | [`local-eyes/run.sh`](../local-eyes/run.sh) |
| `ANDY_LOCAL_EYES_MEMORY`<br>*env file* | `0.6` | The share of the GPU's memory the local eyes may take (vLLM's `--gpu-memory-utilization`). | [`local-eyes/run.sh`](../local-eyes/run.sh) |
| `ANDY_FINDER_TURN`<br>*env file* | `on` | `off` keeps the finder within the head's own reach instead of turning the body to look further to the side. | [`src/andy_companion/finder.py`](../src/andy_companion/finder.py) |
| `ANDY_FINDER_ZOOM` | `on` | `off` reads each view as one shrunk picture instead of zoomed tiles and a closer look, for comparison. | [`src/andy_companion/finder.py`](../src/andy_companion/finder.py); set for their own run by [`evals/zoom_check.py`](../evals/zoom_check.py) and [`sim/finder_sim.py`](../sim/finder_sim.py) |
| `ANDY_OUTLINE_URL`<br>*env file* | unset | A numeric loopback address (`http://127.0.0.1:<port>`) of a separately run mask service that outlines a found thing on the TV picture ([object-outline.md](object-outline.md)); anything else is ignored. | [`src/andy_companion/outline.py`](../src/andy_companion/outline.py) |

## The body (following, looking, idle movement)

| Variable | Default | What it does | Read in |
|---|---|---|---|
| `ANDY_BODY_FOLLOW` | `on` | `off` stops the body turning to face the person and, since they run in the same control step, every other behaviour in this table except the idle moments. | [`src/andy_companion/body/body_follow.py`](../src/andy_companion/body/body_follow.py), [`src/andy_companion/body/attach.py`](../src/andy_companion/body/attach.py) |
| `ANDY_SEEK` | `on` | `off` stops Andy finding the person again when it loses their face (turning to their voice, looking around, following their body). | [`src/andy_companion/body/seek.py`](../src/andy_companion/body/seek.py) |
| `ANDY_SEEK_LOOK_UP_DEG` | `0` | How many degrees the head may look up for a face above the picture while seeking. | [`src/andy_companion/body/seek.py`](../src/andy_companion/body/seek.py) |
| `ANDY_PERSON_FOLLOW` | `on` | `off` stops Andy looking for a person's body in the camera picture when no face is seen. | [`src/andy_companion/body/person.py`](../src/andy_companion/body/person.py) |
| `ANDY_PERSON_SCORE` | `0.45` | The lowest detector score that counts as a person. | [`src/andy_companion/body/person.py`](../src/andy_companion/body/person.py) |
| `ANDY_PERSON_THREADS` | `2` | How many CPU threads the person detector uses. | [`src/andy_companion/body/person.py`](../src/andy_companion/body/person.py) |
| `ANDY_TURN_TO_SPEAKER` | `on` | `off` stops Andy turning its head to a second voice from the side while it follows one face. | [`src/andy_companion/body/seek.py`](../src/andy_companion/body/seek.py) |
| `ANDY_SPEAK_FOLLOW` | `on` | `off` brings back Pollen's pause in face following while Andy speaks. | [`src/andy_companion/body/gaze.py`](../src/andy_companion/body/gaze.py) |
| `ANDY_MAX_LOOK_UP_DEG` | `10` | How many degrees the head may tilt up while a recorded emotion plays; `off` sends every pose as it is. | [`src/andy_companion/body/gaze.py`](../src/andy_companion/body/gaze.py) |
| `ANDY_GLANCE` | `on` | `off` stops the glance at the TV when something new appears on it. | [`src/andy_companion/body/glance.py`](../src/andy_companion/body/glance.py) |
| `ANDY_IDLE` | `calm` | The idle moments between conversations: `calm` (every 5 minutes), `lively` (every 2), `off` (still apart from breathing) or `pollen` (Pollen's own); anything else means `calm`. | [`src/andy_companion/body/idle.py`](../src/andy_companion/body/idle.py), [`src/andy_companion/body/attach.py`](../src/andy_companion/body/attach.py) |
| `ANDY_LISTENING` | `on` | `off` stops the antennas lifting a little while the person speaks. | [`src/andy_companion/body/listening.py`](../src/andy_companion/body/listening.py) |
| `ANDY_LISTENING_SIGN` | `1` | `-1` flips the antennas' direction while listening, for a robot where they go down instead of up. | [`src/andy_companion/body/listening.py`](../src/andy_companion/body/listening.py) |
| `ANDY_THINKING` | `on` | `off` stops the slow antenna lean that shows Andy is working on an answer. | [`src/andy_companion/body/thinking.py`](../src/andy_companion/body/thinking.py) |
| `ANDY_GIGGLE` | `on` | `off` stops the antenna wiggle after a joke's punchline. | [`src/andy_companion/body/giggle.py`](../src/andy_companion/body/giggle.py) |
| `ANDY_WAVE` | `on` | `off` stops Andy waving back with its antennas when someone waves at it. | [`src/andy_companion/body/wave.py`](../src/andy_companion/body/wave.py) |
| `ANDY_WAVE_DEBUG`<br>*env file* | unset | `1` logs, every five seconds, counts of why no wave was seen (never a picture), for tuning on the robot. | [`src/andy_companion/body/wave.py`](../src/andy_companion/body/wave.py) |
| `ANDY_EXPRESSIVE` | `off` | `on` turns on the glance away while thinking and the head tilt on a question, which stay off until checked on the robot. | [`src/andy_companion/body/expressive.py`](../src/andy_companion/body/expressive.py) |

## The screen and pages

| Variable | Default | What it does | Read in |
|---|---|---|---|
| `ANDY_SCREEN_PORT`<br>*env file* | `8090` | The screen server's port (the TV screen, family, under-the-hood and settings pages), where Andy also sends captions and turn times. | [`src/andy_companion/screen_server.py`](../src/andy_companion/screen_server.py), [`src/andy_companion/transient.py`](../src/andy_companion/transient.py), [`src/andy_companion/captions.py`](../src/andy_companion/captions.py), [`src/andy_companion/turns.py`](../src/andy_companion/turns.py), [`scripts/settings.py`](../scripts/settings.py), [`scripts/doctor.py`](../scripts/doctor.py) |
| `ANDY_SCREEN_HOST` | `0.0.0.0` | The address the screen server listens on: every address by default, so the TV and phones at home can open it. | [`src/andy_companion/screen_server.py`](../src/andy_companion/screen_server.py) |
| `ANDY_DEMO_PORT` | `8093` (`$PORT` when public) | The port of the sample-data demo of the screens. | [`scripts/demo_screen.py`](../scripts/demo_screen.py) |
| `ANDY_DEMO_PUBLIC` | unset | `1` does what `--public` does: a read-only copy on every address, for a hosted page anyone can open. | [`scripts/demo_screen.py`](../scripts/demo_screen.py); set to `1` by [`space/Dockerfile`](../space/Dockerfile) |
| `ANDY_DEMO_SCENE` | unset (every scene in turn) | Holds one scene for screenshots or filming: `research`, `searching`, `found`, `letter`, `scam`, `today`, `note`, `keys`, `story` or `quiet`. | [`scripts/demo_screen.py`](../scripts/demo_screen.py) |
| `ANDY_DEMO_VIDEO` | unset | An `https://` link to the video, shown on the demo's front page (any other link is left out). | [`scripts/demo_screen.py`](../scripts/demo_screen.py) |
| `ANDY_DEMO_REPO` | `https://github.com/AndyDM9/andy-companion` | The "The code" link on the demo's front page. | [`scripts/demo_screen.py`](../scripts/demo_screen.py) |

## Paths and processes

| Variable | Default | What it does | Read in |
|---|---|---|---|
| `ANDY_ENV_FILE` | `~/.config/companion-hackathon/.env` | Where the private env file is. | [`src/andy_companion/app_mode.py`](../src/andy_companion/app_mode.py), [`scripts/doctor.py`](../scripts/doctor.py), [`voice/run.sh`](../voice/run.sh), [`local-eyes/run.sh`](../local-eyes/run.sh), [`cloud/guard-endpoint.sh`](../cloud/guard-endpoint.sh), [`cloud/vision-endpoint.sh`](../cloud/vision-endpoint.sh), [`cloud/scam-job.sh`](../cloud/scam-job.sh), [`cloud/sim-job.sh`](../cloud/sim-job.sh), [`cloud/suite-job.sh`](../cloud/suite-job.sh) |
| `ANDY_DATA_DIR` | `~/.local/share/andy-companion` | The folder of Andy's own store: reminders, settings, what the person asked it to remember, photos and the health file. | [`src/andy_companion/reminders.py`](../src/andy_companion/reminders.py) (every other store takes the folder from there); set to a throwaway folder by [`scripts/demo_screen.py`](../scripts/demo_screen.py) for its own run |
| `ANDY_APP_PYTHON` | `robot/.venv/bin/python` (in the repository) | The Python that runs the supervisor and the conversation app. | [`scripts/andy`](../scripts/andy) (which passes it on), [`scripts/run-robot.sh`](../scripts/run-robot.sh) |
| `ANDY_WATCHDOG` | `on` | `off` stops the conversation app asking for a restart when the microphone keeps dropping audio; the counting and the health file stay. | [`src/andy_companion/watchdog.py`](../src/andy_companion/watchdog.py) |

## Evaluations, jobs and simulation (for testers)

| Variable | Default | What it does | Read in |
|---|---|---|---|
| `ANDY_FINDER_RECORD`<br>*env file* | unset | Testing only: a folder that keeps every finder try and every "what do you see?" look (pictures of the room and what the eyes said, never the person's words); leave it unset otherwise, and always while filming. | [`src/andy_companion/finder.py`](../src/andy_companion/finder.py), [`src/andy_companion/vision.py`](../src/andy_companion/vision.py), [`scripts/doctor.py`](../scripts/doctor.py) (warns while it is set) |
| `ANDY_JUDGE` | `nvidia/Nemotron-3-Ultra-550b-a55b` | The model that judges each answer in the conversation suite. | [`evals/run_suite.py`](../evals/run_suite.py) |
| `ANDY_YES` | unset | `1` answers yes to the "this costs money, start it?" question, for a run nobody is watching. | [`cloud/secret.sh`](../cloud/secret.sh) (used by the endpoint and job scripts in `cloud/`) |
| `ANDY_SUITE_RUNS` | `3` | How many runs of the conversation suite the Nebius job makes. | [`cloud/suite-job.sh`](../cloud/suite-job.sh) |
| `ANDY_SUITE_ARGS` | unset | More arguments for [`evals/run_suite.py`](../evals/run_suite.py) inside the job. | [`cloud/suite-job.sh`](../cloud/suite-job.sh) |
| `ANDY_SCAM_PARTS` | `4` | How many parts (one job each) the scam evaluation's messages are split into. | [`cloud/scam-job.sh`](../cloud/scam-job.sh) |
| `ANDY_JOBS_AT_ONCE` | `2` | How many of those jobs run at the same time. | [`cloud/scam-job.sh`](../cloud/scam-job.sh) |
| `ANDY_SCAM_STAMP` | the date and time (`YYYYmmdd-HHMMSS`) | The run's stamp, which names its jobs and `evals/results/scam-parts-<stamp>/`; reuse one to run missing parts again. | [`cloud/scam-job.sh`](../cloud/scam-job.sh) |
| `ANDY_SCAM_ONLY` | every part (`1` to `ANDY_SCAM_PARTS`) | Which part numbers to run, separated by spaces. | [`cloud/scam-job.sh`](../cloud/scam-job.sh) |
| `ANDY_SCAM_COLLECT` | unset | Part numbers whose jobs already ran under `ANDY_SCAM_STAMP`, whose scorecards are fetched from the job logs instead of run again. | [`cloud/scam-job.sh`](../cloud/scam-job.sh) |
| `ANDY_SIM_SEED` | `21` | The random seed for the finder simulation jobs. | [`cloud/sim-job.sh`](../cloud/sim-job.sh) |
| `ANDY_SIM_MJCF` | unset (the robot environment's installed scene, else one fetched once from PyPI into `sim/.cache`) | The folder of Pollen's Reachy Mini MuJoCo scene for the finder simulation. | [`sim/finder_sim.py`](../sim/finder_sim.py); set inside its job by [`cloud/sim-job.sh`](../cloud/sim-job.sh) |

## Internal (set by Andy's own scripts)

These are set by a script for the program it starts; people don't set them.

| Variable | Default | What it does | Read in |
|---|---|---|---|
| `ANDY_SIM` | unset | `1` lets the sleeping Andy listen for its wake words on this computer's default microphone when there is no robot. | [`src/andy_companion/wake.py`](../src/andy_companion/wake.py); set by [`scripts/andy-sim`](../scripts/andy-sim) |
| `ANDY_IN_JOB` | unset | Set, the scam evaluation prints its scorecard to the job's log in numbered pieces instead of writing a file. | [`evals/scam_eval.py`](../evals/scam_eval.py); set by [`cloud/scam-job.sh`](../cloud/scam-job.sh) inside each job |
| `ANDY_SIM_WHERE` | `this computer` | Where the finder simulation ran, as written in its scorecard. | [`sim/finder_sim.py`](../sim/finder_sim.py); set by [`cloud/sim-job.sh`](../cloud/sim-job.sh) inside each job |

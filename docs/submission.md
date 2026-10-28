# Devpost submission

The text for the Devpost form, field by field. Every sentence is true and checkable in the repository; each number
comes from the scorecard or measurement named in the README. Rewritten 2026-10-21 to the length and shape of
recent winning entries (about 2,000 words now, Devpost's own headings, each number said once); re-read against
[rules-compliance.md](rules-compliance.md) before submitting. Every number links to its scorecard or source; the
links point at the `hackathon-submission` tag on GitHub, so they work once the tag is pushed and the repository is public. The fuller story is in the [README](../README.md).

## Form fields

- **Project name:** Andy
- **Tagline** (198 of 200 characters): A small robot that reads the letter in your hand and looks for your glasses: a
  companion for older adults who live at home, and the family who help. Built with NVIDIA Nemotron on Nebius, and Tavily.
- **Track:** Physical AI. **Bonus prize:** Best Use of Tavily.
- **Video:** *[the YouTube link: public, "not made for kids"]*
- **Code:** *[the repository link, at the `hackathon-submission` tag]*
- **Try it:** https://huggingface.co/spaces/andydm/andy-companion-judge (guided real AI with invented inputs and simulated tools),
  https://huggingface.co/spaces/andydm/andy-companion (Andy's screens on sample data, no keys) and
  https://huggingface.co/spaces/andydm/andy-companion-app (the Reachy Mini app)
- **Testing instructions:** The public Space demonstrates the screens on sample data; it has no connected
  robot or live model calls. A separate guided playground at https://andydm-andy-companion-judge.hf.space/
  provides author-funded real Nemotron replies to fixed invented examples, with simulated camera/search/family
  effects and no visitor key. It supplements hardware access; public usage limits apply. For a free test of the real robot, request a session through
  https://github.com/AndyDM9/andy-companion/issues/new?template=live-demo.yml or contact the entrant through
  the organisers. The author supplies the robot, computer and API access during that session; judges do not
  need to purchase credits or receive personal desktop/provider credentials. The public GitHub request form
  requires sign-in; the organiser contact route is also available. Requested physical hardware access will
  be agreed separately with the organisers; a video call is not a confirmed substitute and the final
  physical-access method is pending. Reproduction with your own equipment and keys is optional. Instructions and limits:
  https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/judging.md
- **Built with:** nebius-token-factory, nebius-ai-cloud, nebius-serverless-endpoints, nebius-serverless-jobs,
  nvidia-nemotron, nemotron-3.5-lightning, nemotron-3-ultra, nemotron-3.5-super-vl, nemotron-content-safety,
  nvidia-parakeet, nemotron-nano-vl, nvidia-cosmos, cosmos-reason-2, vllm, tavily, reachy-mini, pollen-robotics, mujoco, qwen3-tts, hugging-face,
  python, opencv, tesseract, vosk, wikipedia
- **Feedback** (mandatory; the ten best win a prize): [feedback.md](feedback.md), product by product.
- **Prior work:** Built during the submission period, from 2026-10-13. It reuses general-purpose robot behaviour
  code its author wrote earlier in the same period (from 2026-10-05), rewritten for this project.
- **Gallery** (captioned, the real robot first): see [submission-checklist.md](submission-checklist.md).

## The story ("About the project")

### For the judges

Andy is a small home robot for older adults who live at home, and the family who help. Scams reach people there, by
letter and by phone: adults 60 and over reported about $3 billion lost to fraud in 2025 ([FTC](https://search.ftc.gov/news-events/news/press-releases/2026/10/ftc-issues-annual-report-congress-agencys-actions-protect-older-adults)). Andy reads the
letter in your hand and puts **Be careful** first on a risky one, looks around the room and points at your glasses,
and looks things up with Tavily while it keeps talking with you. Measured: [58 of 60 scams caught, none of 60 ordinary
messages flagged](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json); [91, 95 and 95 of 97](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/2026-10-28-nebius-job-andy-suite-20261028-103654.json) text cases passed with the current profile; both evaluations ran as Nebius
Serverless Jobs. Three local runs of the same profile scored [93, 94 and 94](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/suite-2026-10-27-consent-source-local.json); each run has the real confirmation gate around synthetic tools. Entered in the **Physical AI track**.
- **Track fit:** an embodied agent on a Pollen Reachy Mini. Pollen's conversation app is the agent runtime; NVIDIA
  Nemotron on Nebius Token Factory talks, sees and decides, and its answers move the robot's head. **Eight models run
  on the computer beside the robot:** NVIDIA Parakeet hears, Qwen3-TTS speaks, and NVIDIA Cosmos Reason 2 can run vision locally (tried on the home computer, not yet on the robot), with local models for the wake phrase,
  reading letters and finding a face.
- **Nebius:** Token Factory answers every turn: a median of [1.06 s](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/robot-timings-2026-10-20-1550.json) from your words being understood to Andy's
  first sound, 54 turns on the robot. **Serverless Jobs** run Andy's search in Pollen's MuJoCo simulation, scored
  against the scene's truth, and the tests; a **Serverless Endpoint**, started when needed, serves NVIDIA Nemotron
  3.5 Content Safety as a second check on what the person says.
- **Design:** one household, three screens: the TV beside Andy, the family's phone page, a helper's settings page.
  **Built for ageing eyes and ears:** Atkinson Hyperlegible (the Braille Institute's typeface for low vision), no
  text under 14 px, captions on by default at 7:1 contrast, a slower pace on request, louder at "I can't hear
  you", and talking over Andy stops it. Installs as a
  [Reachy Mini app](https://huggingface.co/spaces/andydm/andy-companion-app); [try the screens](https://huggingface.co/spaces/andydm/andy-companion), no keys.
- **Limits, said plainly:** at home it pointed at hidden glasses 3 of 9 times, never at the wrong place; no study
  with older adults yet. The planned video uses live robot shots, with no cuts in the pauses; filming is October 27.
- **Testing access:** [short testing instructions](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/judging.md):
  a public sample demo without keys, reproducible software checks, optional model evaluations and a free live robot demonstration on request.

### Inspiration

Three in four US adults aged 50 and over want to keep living in their own homes ([AARP, December 2024](https://www.aarp.org/press/releases/2024-12-10-new-aarp-report-majority-adults-50-plus-age-place-policies-communities-catch-up.html)), and their
families want to help without taking over. Voice assistants answer questions, but they don't look at you, don't read
the letter in your hand, and don't tell you which of your family looked at what you shared. We wanted a small robot
that is useful every day, good company, honest about being a robot, and that keeps no recordings or transcripts:
only what you ask it to keep.

### What it does

Andy is a Pollen Robotics Reachy Mini that keeps looking at you while you talk. Three interactions bring the
camera, moving body and TV together. Filming is planned for October 27; each interaction's current test status is
recorded in the repository's live-test checklist:

- **"Can you read this for me?"** You hold up a letter. Andy reads it and the TV shows it in large print. If the
  page asks for a fee or gift cards, or rushes you, code, not the model, puts **Be careful** first: "Don't call or
  pay yet. Check with family first." Then Andy offers to look it up, and the TV shows the consumer-protection warning
  Tavily found, with its source.
- **"Where did I leave my glasses?"** Andy looks around the room, reads each view zoomed in, turns its head straight
  at the best sighting, checks a close-up, and only then points and says where. If it isn't sure, it says it
  couldn't see them. Nothing was trained: a vision model's answers move the robot.
- **"Could you look into whether the farmers market is on this Saturday?"** Andy says it will, and carries on
  talking with you while the TV shows Tavily's research step by step; within a minute it tells you the answer and
  where it found it.

Andy also checks a message you only mention ("a man called saying my grandson is in jail"), keeps reminders in your
words, every day if you like ("every morning at eight, my blood pressure pills": a reminder, never a dose), turns a
family photo into a story, speaks English and Spanish, and waves its antennas back when you wave (tried on the
robot). Family see only what you share, and Andy tells you who looked. New and tested in code, not yet tried on the
robot: turning to a second person speaking, a move taught by hand, and remembering where you put your keys.

### How we built it

- **At home:** NVIDIA Parakeet TDT 0.6B v3 and Qwen3-TTS on the home computer's GPU, so your voice never leaves the
  house, only words do; Silero VAD and Smart Turn v3.2, Vosk, Tesseract and YuNet on its CPU; and NVIDIA Cosmos
  Reason 2 for local vision; the conversation still calls Token Factory.
- **Thinking on Nebius Token Factory:** NVIDIA Nemotron 3.5 Lightning talks and calls 38 profile tools, plus two SDK task controls; NVIDIA Nemotron 3
  Ultra takes hard questions and judges the tests. Zero data retention is on.
- **Seeing:** NVIDIA Nemotron 3.5 Super VL on Token Factory reads each of four views as six zoomed-in parts, all 24
  at once in about 1.8 s, then a strict yes or no about a close-up. On one room photo, zooming in took the search
  from [0 of 9 to 9 of 9](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/zoom-check-2026-10-20-1711.json) (a direction, not a rate).
- **Seeing offline:** NVIDIA Cosmos Reason 2 8B on the home computer answers the same questions: in 30 simulated
  searches it pointed at the hidden object [22 of 23 times](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/sim-finder-2026-10-25-1524-on-small0.35.json) (Super VL 21 on the same trials), less precisely
  (1.95° against 0.78°), and never claimed a find that wasn't there; tried on the computer, not yet on the robot.
- **The body:** Pollen's Reachy Mini conversation app is the agent runtime; Andy's profile, tools and body
  behaviours plug into it without forking it. What must always hold is enforced in code, not left to the model: the
  scam warning, consent before anything is kept or shared, and the 911 or 988 line when someone says urgent words.
- **Measured as Nebius Serverless Jobs:** 97 spoken situations judged by Nemotron 3 Ultra, three runs, every failure
  published; and Andy's own search in Pollen's MuJoCo simulation, a glasses-sized object hidden at random: with the
  close-up check, [no false find in 7](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/sim-finder-20261020-185613-on-small0.35-nebius-job.json) searches without the object, against [3 in 7](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/sim-finder-20261020-185613-off-small0.35-nebius-job.json) without it.
- **A second check** on the person's words, NVIDIA Nemotron 3.5 Content Safety on a Nebius Serverless Endpoint, caught
  [7 of 8](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/guard-content-safety-2026-10-25.json) urgent phrasings our word list missed.

### How Andy uses Tavily

Five of Tavily's APIs, each where it fits: **search** for local news and for scam warnings on consumer-protection
sites; **extract** for links family send; **crawl** for what's on this week; **map** to find the town's events page at
setup; and **research**, streamed step by step to the TV for "look into it for me".

What Tavily adds to the scam check, on 120 messages written as a person would read them to Andy, three runs as Nebius
Serverless Jobs: Tavily's warnings, matched by Nemotron 3 Ultra, caught **[58 of 60 scams and flagged none of 60
ordinary messages](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json)**, naming a source in 170 of 174 verdicts. Each model alone caught about as many and
also flagged none, so what Tavily adds is the named source: the warning the person can check, from a site they
trust. Matched by the smaller model, the same warnings flagged 24 ordinary messages, so only the stronger model keeps
that source without false alarms. About [$17 per 1,000 checks](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/cost.md#the-scam-check-per-check-measured-2026-10-20).

### Challenges we ran into

- **A topic is not a trick.** A grandchild's recital invitation and a "grandchild in trouble" scam share their
  words. One broad question flagged [11 of 40](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/decisions/0007-the-scam-check-two-narrow-questions.md) ordinary messages; two narrow questions, the second asked of a stronger
  model, flagged none of 60.
- **Our judge passed a reply it should have failed:** Andy read out a scam letter's phone number. Words that must
  never be said are now checked in code, and Andy never sees a letter's account or phone numbers.
- **Privacy in someone else's code, twice:** a speech component printed what it heard to a console. We filtered
  its prints; an update then added a new one, and words reached our log for ten days before we found them. Now
  the health check reads the log itself and fails on any line that could hold what was heard.
- **A crisis line we nearly missed:** at first "everyone would be better off without me" got no crisis line in 2 of
  3 runs, and none in Spanish. A rule and a check in code fixed it, tested not to fire on grief.

### Accomplishments that we're proud of

Every number has a dated scorecard in the repository, failures included, and Andy claims only what it shows.

### What we learned

What older adults want from a home robot, across 21 studies ([a 2026 systematic review](https://pubmed.ncbi.nlm.nih.gov/41538893/)):
voice, control over their privacy and data, companionship and help with daily tasks. Andy is built around that, and
leaves out fall detection and health monitoring on purpose. Measure the product, not just the model: Andy's real
profile and tools, three runs each, beside a baseline. And put hard rules in code and judgment in the model.

### Limitations: what doesn't work yet

- **Finding things at home misses more than it finds.** In [9 tries on the robot](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/finder-eval-2026-10-20-2037.json), Andy pointed at the hidden glasses
  3 times and never at the wrong place; all 6 misses were a pair on a chair beyond the head's reach, which the sweep
  saw in 5 of them but the closer look didn't confirm. Andy now turns its body to look past the head's reach; that is
  checked against Pollen's kinematics, not yet tried on the robot.
- No study with older adults yet; a pilot with an ethics review comes next.
- The current profile scored [91, 95 and 95 of 97](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/2026-10-28-nebius-job-andy-suite-20261028-103654.json) as a Nebius Serverless Job and [93, 94 and 94](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/suite-2026-10-27-consent-source-local.json)
  locally, with real confirmation/source checks and synthetic tools. Photo-story memory offers fail every run; other
  offers, a refusal, a story and a crisis reply vary. Once, Nemotron wrote the letter-reading tool's call out as text
  instead of making it; Andy no longer speaks such text. No unapproved write effect was reported. A working watch
  search is founder-confirmed and untimed; physical measurements remain pending.
- It needs a computer with an NVIDIA GPU beside the robot, not yet a Jetson; English and Spanish only.
- Our numbers are our own and small: the scam check's 120 messages were written by us for the test, not taken from
  real households; the suite is judged by a model; and the cost is an estimate from list prices, not a bill.
- The local vision fallback needs a GPU of its own (the 8B model a whole 24 GB one) and hasn't been tried on the
  robot with the primary vision service blocked. The voice conversation and tool selection still need Token
  Factory: this is not a complete offline assistant. GR00T and Sonic are for robots with arms or legs.

### What's next for Andy

A pilot with older adults and their families; more languages (Parakeet already hears 25); and the Jetson version
below.

### Path to shipping

- **Hardware, once:** a Reachy Mini Lite ($399 listed by Hugging Face, read 2026-10-25), a TV the household already
  has, and today a computer with an NVIDIA GPU (8 GB for hearing and speaking; more for the offline eyes), which most
  homes don't have. That computer is likely the biggest cost, and the reason for the Jetson plan.
- **Running, monthly:** about [$2.30 a month, estimated](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/cost.md) from list prices for one household's
  conversation and web lookups, not from a bill; the eyes add about half a cent a search. The second check is not in
  that figure: its endpoint is started when needed, about $1.55 an hour while it runs.
- **A Jetson port needs:** hearing and speaking in well under 7.6 GB (a smaller voice than Qwen3-TTS), thinking and
  seeing staying on Token Factory, and Cosmos Reason 2 2B for when the network is down (about 4 GB of weights; what it
  needs on a Jetson is not yet measured). Planned, not tried on a Jetson.
- **Who pays:** we expect the family who help, not the person; that is a guess the pilot has to test.

### How to test it without a robot

The screens on sample data, no keys: https://huggingface.co/spaces/andydm/andy-companion. Andy's search in
simulation: a 20-second film there and in the README, rerun with a Token Factory key. The real robot: live on a video
call until judging ends ([ask here](https://github.com/AndyDM9/andy-companion/issues/new?template=live-demo.yml)), and the hardware on request.

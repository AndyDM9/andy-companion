# Devpost submission

The text for the Devpost form, field by field. Every sentence is true and checkable in the repository; each number
comes from the scorecard or measurement named in the README. Rewritten 2026-10-21 to the length and shape of
recent winning entries (about 1,500 words, Devpost's own headings, each number said once); re-read against
[rules-compliance.md](rules-compliance.md) before submitting. Every number links to its scorecard or source; the
links point at the `hackathon-submission` tag on GitHub, so they work once the tag is pushed and the repository is public. The fuller story is in the [README](../README.md).

## Form fields

- **Project name:** Andy *[the final name, once decided]*
- **Tagline** (198 of 200 characters): A small robot that reads the letter in your hand and looks for your glasses: a
  companion for older adults who live at home, and the family who help. Built with NVIDIA Nemotron on Nebius, and Tavily.
- **Track:** Physical AI. **Bonus prize:** Best Use of Tavily.
- **Video:** *[the YouTube link: public, "not made for kids"]*
- **Code:** *[the repository link, at the `hackathon-submission` tag]*
- **Try it:** *[the Hugging Face Space's link]*
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

A small home robot that reads the letter in your hand, looks around the room for your glasses, and turns to whoever
is speaking. Entered in the **Physical AI track**.
- **Track fit:** Andy is an embodied agent that senses and acts: Pollen's Reachy Mini conversation app is its agent
  runtime, NVIDIA Nemotron on Nebius decides (with NVIDIA Cosmos Reason 2 as its eyes when offline), and the robot
  hears, sees, turns its head and points.
- **Technology:** NVIDIA Nemotron models on Nebius Token Factory talk, see and judge; a vision model's answers move
  the robot's head; Nebius Serverless Jobs test it all, including Andy's search in simulation.
- **Design:** one household, three screens: the TV beside Andy, the family's phone page, a helper's settings page.
- **Impact:** older adults who live at home, and the family who help, at the letter and the phone call where scams
  reach them.
- **Idea:** a robot, not a speaker, honest about being one, keeping only what you ask it to.

### Inspiration

Three in four US adults aged 50 and over want to keep living in their own homes ([AARP, December 2024](https://www.aarp.org/press/releases/2024-12-10-new-aarp-report-majority-adults-50-plus-age-place-policies-communities-catch-up.html)), and their
families want to help without taking over. Scams reach them there: adults 60 and over reported $2.4 billion lost to
fraud in 2024, four times 2020's figure ([FTC, December 2025](https://www.ftc.gov/news-events/news/press-releases/2025/12/ftc-issues-annual-report-congress-agencys-actions-protect-older-adults)). Voice assistants answer questions, but they don't look
at you, don't read the letter in your hand, and don't tell you which of your family looked at what you shared. We
wanted a small robot that is useful every day, good company, honest about being a robot, and that keeps no
recordings or transcripts: only what you ask it to keep.

### What it does

Andy is a Pollen Robotics Reachy Mini that keeps looking at you while you talk. Three moments show what a robot can
do that a phone can't:

- **"Can you read this for me?"** You hold up a letter. Andy reads it and the TV shows it in large print. If the
  page asks for gift cards or rushes you, code, not the model, puts **Be careful** first: "Don't call or pay yet.
  Check with family first."
- **"Where did I leave my glasses?"** Andy looks around the room, reads each view zoomed in, turns its head straight
  at the best sighting, checks a close-up, and only then points and says where. If it isn't sure, it says it
  couldn't see them. Nothing was trained: a vision model's answers move the robot.
- **"A man called saying my grandson is in jail and needs gift cards."** You just say it. Andy checks it against
  consumer-protection warnings found with Tavily, and the TV says what to do first, then why, with the warning's
  source.

Andy also notices the room: it turns to a second person speaking, and waves back with its antennas when you wave. It
remembers where you put your keys if you say yes, keeps reminders in your words, researches a question on the TV
while you carry on talking, turns a family photo into a story, and speaks English and Spanish. Family see only what
you share, and Andy tells you who looked. Captions are on by default, every text colour reaches 7:1 contrast, and
talking over Andy stops it.

### How we built it

- **Hearing and speaking at home:** NVIDIA Parakeet and Qwen3-TTS on the home computer's GPU, so your voice never
  leaves the house; only words do. On the robot, a median of [1.06 s](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/robot-timings-2026-10-20-1550.json) from the moment your words are
  understood to Andy's first sound (54 real turns).
- **Thinking on Nebius Token Factory:** NVIDIA Nemotron 3.5 Lightning talks and calls 38 tools; NVIDIA Nemotron 3
  Ultra takes hard questions and judges the tests. Zero data retention is on.
- **Seeing:** NVIDIA Nemotron 3.5 Super VL on Token Factory reads each of four views as six zoomed tiles, all 24
  at once in about 1.8 s, each a structured answer, then a strict yes or no about the close-up. On one room photo, zooming
  in took the search from [0 of 9 to 9 of 9](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/zoom-check-2026-10-20-1711.json).
- **Seeing offline:** when Token Factory can't be reached, the same questions go to NVIDIA Cosmos Reason 2 8B on the
  home computer's second GPU, so Andy can still find your glasses; nothing leaves the house. In the same simulated
  searches it pointed at the duck [22 of 23 times](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/sim-finder-2026-10-25-1524-on-small0.35.json), never at the wrong place, and never
  claimed a find that wasn't there; the 2B model, small enough for a Jetson, 18 of 23 ([decision 0015](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/decisions/0015-cosmos-on-this-computer-as-the-offline-eyes.md)).
- **The body:** Pollen's Reachy Mini conversation app is the agent runtime; Andy's profile, tools and body
  behaviours plug into it without forking it. Rules that must hold are in code, under the model: the scam warning,
  consent before anything is kept, and the 911 or 988 line when someone says urgent words.
- **Measured as Nebius Serverless Jobs:** a suite of 94 spoken situations judged by Nemotron 3 Ultra ([93, 92 and 92
  of 94](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/2026-10-25-nebius-job-andy-suite-20261025-170439.json) in three runs, every failure published); and Andy's own search in Pollen's MuJoCo simulation, scored against
  the scene's truth: with the closer look, [no false find in 7](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/sim-finder-20261020-185613-on-small0.35-nebius-job.json) trials without the object, against [3 in 7](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/sim-finder-20261020-185613-off-small0.35-nebius-job.json) the old way.
- **A second look** at the person's words, NVIDIA Nemotron 3.5 Content Safety on a Nebius Serverless Endpoint, caught
  [7 of 8](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/2026-10-13-guard-content-safety.json) urgent phrasings our word list missed.

### How Andy uses Tavily

Five of Tavily's APIs, each where it fits: **search** for local news and for scam warnings on consumer-protection
sites; **extract** for links family send; **crawl** for what's on this week; **map** to find the town's events page at
setup; and **research**, streamed step by step to the TV for "look into it for me".

What Tavily adds, measured on 120 messages read aloud, three runs as Nebius Serverless Jobs: Tavily's warnings,
matched by Nemotron 3 Ultra, caught **[58 of 60 scams and flagged none of 60 ordinary messages](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json)**, naming a source in
170 of 174 verdicts. Each model alone caught about as many, so the gain is a named source and no false alarms;
matched by the smaller model, the same warnings flagged 24 ordinary messages. About [$17 per 1,000 checks](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/cost.md#the-scam-check-per-check-measured-2026-10-20).

### Challenges we ran into

- **A topic is not a trick.** A grandchild's recital invitation and a "grandchild in trouble" scam share their
  words. One broad question flagged [11 of 40](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/decisions/0007-the-scam-check-two-narrow-questions.md) ordinary messages; two narrow questions, the second asked of a stronger
  model, flagged none of 60.
- **Our judge passed a reply it should have failed:** Andy read out a scam letter's phone number. Words that must
  never be said are now checked in code, and Andy never sees a suspicious page's numbers.
- **Privacy in someone else's code:** a speech component printed what it heard to a console our first fix missed. We
  found it in our own log, deleted it, and now filter every console.
- **A crisis line we nearly missed:** at first "everyone would be better off without me" got no crisis line in 2 of
  3 runs, and none in Spanish. A rule and a check in code fixed it, tested not to fire on grief.

### Accomplishments that we're proud of

Everything in the video is live on the real robot, with no cuts in the pauses. Every number has a dated scorecard
in the repository, failures included. And Andy is honest: it says it is a robot, never speaks as anyone, asks
before it remembers or shares, and claims only what the repository shows.

### What we learned

Measure the product, not just the model: Andy's real profile and tools, three runs each, beside a baseline. Put hard
rules in code and judgment in the model. And let the web find while a strong model judges: Tavily made the warnings
available, and only Nemotron 3 Ultra told the same trick from the same topic.

### Limitations: what doesn't work yet

- **Finding things at home misses more than it finds.** In [9 tries on the robot](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/finder-eval-2026-10-20-2037.json), Andy pointed at the hidden glasses
  3 times and never at the wrong place; all 6 misses were a pair on a chair beyond the head's reach, which the sweep
  saw but the closer look didn't confirm. Andy now turns its body to look at things past the head's reach; that is
  checked against Pollen's kinematics, [the robot test is next].
- No study with older adults yet; a pilot with an ethics review comes next.
- Turning to a voice, waving back and moves taught by hand are tested in code; on camera with two people, not yet.
- It needs a computer with an NVIDIA GPU beside the robot, not yet a Jetson; English and Spanish only.
- Our numbers are our own and small: the scam check's 120 messages were written by us for the test, not taken from
  real households; the suite is judged by a model; and the cost is an estimate from list prices, not a bill.
- The offline eyes are less precise and slower: Cosmos Reason 2 8B points with a median error of 1.95° against
  Super VL's 0.78°, in 4.8 s against 3.2 s, and fills a 24 GB GPU; the 2B model pointed
  [18 of 23 times](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/sim-finder-2026-10-25-1506-on-small0.35.json), three at the wrong place. Neither
  has been tried on the robot with the network unplugged. GR00T and Sonic, the track's other models, are for robots with arms or legs.

### What's next

A pilot with older adults and their families; more languages (Parakeet already hears 25); an NVIDIA Jetson beside
the robot with the big models staying on Token Factory; the body turn tried at home for things beside Andy;
and Andy published as a one-click Reachy Mini app on Hugging Face.

### Path to shipping

- **Hardware, once:** a Reachy Mini Lite ($399 listed by Hugging Face, read 2026-10-25), a TV the household already
  has, and today a computer with an 8 GB NVIDIA GPU, which most homes don't have. That computer is likely the biggest
  cost, and the reason for the Jetson plan.
- **Running, monthly:** about [$2.30 a month, estimated](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/docs/cost.md) from list prices for one household's
  conversation and web lookups, not from a bill; the eyes add about half a cent a search.
- **A Jetson port needs:** hearing and speaking in well under 7.6 GB (a smaller voice than Qwen3-TTS), thinking
  and seeing staying on Token Factory, and Cosmos Reason 2 2B, the smaller of Andy's offline eyes, for when the network is
  down. Planned, not tried on a Jetson.
- **Who pays:** we expect the family who help, not the person; that is a guess the pilot has to test.
- **Before anyone relies on it:** the pilot with an ethics review, the finder's closer look fixed, and the limits
  above.

### How to test it without a robot

1. **The video:** the real robot, live, at least a minute of it uncut.
2. **Andy's search in simulation:** a 20-second film on the demo's front page and in the README; anyone with a
   Token Factory key can rerun it, no robot.
3. **The screens:** the TV, the family page and the settings page on sample data, in the browser, no keys
   *[the Space's link]*.
4. **The real robot:** live on a video call any time until judging ends, and access to the hardware on request.

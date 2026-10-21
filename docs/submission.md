# Devpost submission

The text for the Devpost form, field by field. Every sentence is true and checkable in the repository; each number
comes from the scorecard or measurement named in the README. Rewritten 2026-10-21 to the length and shape of
recent winning entries (about 1,600 words, Devpost's own headings, each number said once); re-read against
[rules-compliance.md](rules-compliance.md) before submitting. The fuller story is in the [README](../README.md).

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
  nvidia-parakeet, nemotron-nano-vl, vllm, tavily, reachy-mini, pollen-robotics, mujoco, qwen3-tts, hugging-face,
  python, opencv, tesseract, vosk, wikipedia
- **Feedback** (mandatory; the ten best win a prize): [feedback.md](feedback.md), product by product.
- **Prior work:** Built during the submission period, from 2026-10-13. It reuses general-purpose robot behaviour
  code its author wrote earlier in the same period (from 2026-10-05), rewritten for this project.
- **Gallery** (captioned, the real robot first): see [submission-checklist.md](submission-checklist.md).

## The story ("About the project")

### For the judges

A small home robot that reads the letter in your hand, looks around the room for your glasses, and turns to whoever
is speaking. Entered in the **Physical AI track**.
- **Technology:** NVIDIA Nemotron models on Nebius Token Factory talk, see and judge; a vision model's answers move
  the robot's head; Nebius Serverless Jobs test it all, including Andy's search in simulation.
- **Design:** one household, three screens: the TV beside Andy, the family's phone page, a helper's settings page.
- **Impact:** older adults who live at home, and the family who help, at the letter and the phone call where scams
  reach them.
- **Idea:** a robot, not a speaker, honest about being one, keeping only what you ask it to.

### Inspiration

Three in four US adults aged 50 and over want to keep living in their own homes (AARP, December 2024), and their
families want to help without taking over. Scams reach them there: adults 60 and over reported $2.4 billion lost to
fraud in 2024, four times 2020's figure (FTC, December 2025). Voice assistants answer questions, but they don't look
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
  leaves the house; only words do. On the robot, a median of 1.06 s from your words to Andy's first sound (54 real
  turns).
- **Thinking on Nebius Token Factory:** NVIDIA Nemotron 3.5 Lightning talks and calls 38 tools; NVIDIA Nemotron 3
  Ultra takes hard questions and judges the tests. Zero data retention is on.
- **Seeing:** NVIDIA Nemotron 3.5 Super VL on Token Factory reads each of four views as six zoomed tiles, all 24
  at once in about 1.8 s, each a structured answer, then a strict yes or no about the close-up. On one room photo, zooming
  in took the search from 0 of 9 to 9 of 9.
- **The body:** Pollen's Reachy Mini conversation app is the agent runtime; Andy's profile, tools and body
  behaviours plug into it without forking it. Rules that must hold are in code, under the model: the scam warning,
  consent before anything is kept, and the 911 or 988 line when someone says urgent words.
- **Measured as Nebius Serverless Jobs:** a suite of 94 spoken situations judged by Nemotron 3 Ultra (92, 91 and 94
  of 94 in three runs, every failure published); and Andy's own search in Pollen's MuJoCo simulation, scored against
  the scene's truth: with the closer look, no false find in 7 trials without the object, against 3 in 7 the old way.
- **A second look** at the person's words, NVIDIA Nemotron 3.5 Content Safety on a Nebius Serverless Endpoint, caught
  7 of 8 urgent phrasings our word list missed.

### How Andy uses Tavily

Five of Tavily's APIs, each where it fits: **search** for local news and for scam warnings on consumer-protection
sites; **extract** for links family send; **crawl** for what's on this week; **map** to find the town's events page at
setup; and **research**, streamed step by step to the TV for "look into it for me".

What Tavily adds, measured on 120 messages read aloud, three runs as Nebius Serverless Jobs: Tavily's warnings,
matched by Nemotron 3 Ultra, caught **58 of 60 scams and flagged none of 60 ordinary messages**, naming a source in
170 of 174 verdicts. Each model alone caught about as many, so the gain is a named source and no false alarms;
matched by the smaller model, the same warnings flagged 24 ordinary messages. About $17 per 1,000 checks.

### Challenges we ran into

- **A topic is not a trick.** A grandchild's recital invitation and a "grandchild in trouble" scam share their
  words. One broad question flagged 11 of 40 ordinary messages; two narrow questions, the second asked of a stronger
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

### What doesn't work yet

- **Finding things at home misses more than it finds.** In 9 tries on the robot, Andy pointed at the hidden glasses
  3 times and never at the wrong place; all 6 misses were a pair on a chair beyond the head's reach, which the sweep
  saw but the closer look didn't confirm. That closer look is the next fix.
- No study with older adults yet; a pilot with an ethics review comes next.
- Turning to a voice, waving back and moves taught by hand are tested in code; on camera with two people, not yet.
- It needs a computer with an NVIDIA GPU beside the robot, not yet a Jetson; English and Spanish only.

### What's next

A pilot with older adults and their families; more languages (Parakeet already hears 25); an NVIDIA Jetson beside
the robot with the big models staying on Token Factory; the closer look fixed for things beyond the head's reach;
and Andy published as a one-click Reachy Mini app on Hugging Face. It costs about $2.30 a month for one household's
conversation and web lookups today.

### How to test it without a robot

1. **The video:** the real robot, live, at least a minute of it uncut.
2. **Andy's search in simulation:** a 20-second film on the demo's front page and in the README; anyone with a
   Token Factory key can rerun it, no robot.
3. **The screens:** the TV, the family page and the settings page on sample data, in the browser, no keys
   *[the Space's link]*.
4. **The real robot:** live on a video call any time until judging ends, and access to the hardware on request.

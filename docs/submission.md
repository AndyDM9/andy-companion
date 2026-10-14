# Devpost submission (draft)

Fill in the final name and links before submitting. Every sentence must be true and checkable in the
repository; numbers are from the run named beside them. Sections follow Devpost's project template.
Last revised 2026-10-14; re-read against [rules-compliance.md](rules-compliance.md) before submitting.

## Tagline (under 200 characters)

A small robot that reads the letter in your hand and finds your glasses: a companion for older adults who live at home, and the family who help. Built with NVIDIA Nemotron on Nebius, and Tavily.

## Inspiration

Three in four US adults aged 50 and over want to keep living in their own homes (AARP's Home and
Community Preferences Survey, December 2024), and their families want to help without taking over. Voice assistants answer questions, but they don't look at you, don't read the letter in
your hand, and don't tell you which of your family looked at what you shared. We wanted a small robot
that is honest about being a robot, useful every day, good company, and that keeps no recordings or
transcripts: only what you ask it to keep.

## What it does

Andy is a Reachy Mini that talks with you and keeps looking at you while it does: its head and body
follow you, its antennas lift while you speak and lean while it thinks.

- **Your day, the same way every time.** The date (never guessed), reminders in your words said when
  they're due, the morning plan, and the weather from the National Weather Service.
- **Finds things in the room.** "Where did I leave my glasses?" Andy sweeps the room, NVIDIA Nemotron
  Nano VL on a Nebius Serverless Endpoint reads four views at once, and Andy points with its head; the TV
  shows the picture it saw them in.
- **Reads the letter you hold up.** It reads it on the computer, explains it, and shows it in large
  print on the screen. If a page asks for gift cards or rushes you, code (not the model) puts **Be
  careful** first: "Don't call or pay yet. Check with family first."
- **Looks things up and names the source, through Tavily.** "Look into whether the farmers market is on
  Saturday" runs a Tavily research task while you carry on. The screen shows its planning and sources
  live, and Andy tells you the dated answer when it's ready.
- **Good company.** Andy follows research with older adults: short turns and open questions about your
  life, never "Do you remember…?". It also has gentle jokes and riddles (its antennas wiggle after the
  punchline), real public-domain stories read a part at a time with "Shall I go on?", and "On this day"
  from Wikipedia. Hard decisions are thought through with Nemotron 3 Ultra.
- **Shows you where to look.** A TV beside Andy shows the day, what Andy is doing and what it found,
  with captions of its own words. When something new appears, Andy turns its head to the screen and
  back to you.
- **Family, on your terms.** Family see only what you ask Andy to share, and can send a message or a
  photo. Andy tells you who looked. A helper can change settings from a phone, and Andy tells you who
  changed what.
- **English and Spanish**, in whichever you speak (with *usted*), and the screen switches too.

## What's new here

- **A language model that moves a robot's body to find things,** with nothing trained: Nemotron Nano VL
  reads four views as structured output, and Andy turns its head to the one it chose.
- **A scam check measured four ways, on Nebius:** on 120 messages read aloud, three runs as Nebius
  Serverless Jobs, Tavily's consumer-protection warnings matched by Nemotron 3 Ultra caught 58 of 60
  scams with no ordinary message flagged, against 55.7 for Ultra without the web and 53.3 for Lightning.
  Matched by the smaller model, the same warnings flagged 24 ordinary messages: the web finds the
  trick, and the stronger model tells the trick from the topic.
- **Rules below the model, in code:** a letter that asks for gift cards gets **Be careful** whatever the
  model says, and its phone numbers are never read out.
- **A spoken-conversation suite run as a Nebius Serverless Job,** judged by Nemotron 3 Ultra, with words
  that must never be said checked in code beside the judge.
- **No recordings and no transcripts,** by design: captions and timings live in memory only.

## Privacy, in four answers

- **Where is it heard?** Your voice becomes words on this computer and is never recorded; the words go to
  Nemotron on Nebius Token Factory, with zero data retention on.
- **What is kept?** Only what you ask Andy to keep (a reminder, a fact, a moment), on this computer.
- **Who sees it?** Family see only what you ask Andy to share; Andy tells you who looked.
- **How do I delete it?** Say "forget that", or a helper deletes anything from one page on a phone, and
  Andy tells you who deleted what.

## How we built it

- **Hearing:** NVIDIA Parakeet TDT 0.6B v3, locally, inside Hugging Face's speech-to-speech server;
  0.02–0.08 s per utterance.
- **Conversation and 35 tools:** NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory (zero data
  retention on), 0.6–0.8 s per reply measured on the robot. **NVIDIA Nemotron 3 Ultra** for hard
  questions (2.1 s) and as the suite's judge. Lightning's **structured output** turns letters into
  large-print screen cards and vets "On this day" items.
- **Eyes, in the loop:** NVIDIA Nemotron Nano 12B v2 VL on a **Nebius Serverless Endpoint** (L40S, vLLM),
  behind token authentication. It describes a view in 3.5 s, and to find something Andy sweeps the room
  and the model reads four views at once as structured output (seven frames in 3.9 s in a live test of the model on its endpoint); Andy then
  points at it with its head.
- **A second look:** NVIDIA Nemotron 3.5 Content Safety on a second **Serverless Endpoint**, with a policy
  written for signs of crisis: on held-out phrasings our word list misses, it caught 7 of 8 with no
  false alarms, in about 0.55 s.
- **Proof:** a conversation suite of 83 spoken situations in 19 areas, English and Spanish, run as a
  **Nebius Serverless Job** and judged by Nemotron 3 Ultra. The model gets exactly the robot's tools.
  Tool cases are judged on what Andy says, and words that must never be said are checked in code. Latest
  Job: 79, 79 and 79 of 81 (2026-10-13), every run's scorecard and failures in the repository.
  *[Replace with the final Job run's numbers before submitting.]*
- **Tavily, five ways:**
  - **search:** local news from the person's own papers; scam checks at advanced depth, on
    consumer-protection sites only, with numbers removed first;
  - **extract:** links family send;
  - **crawl:** what's on this week;
  - **map:** at setup, the town's events calendar found on its own website (with a search within the
    site when the site refuses crawlers);
  - **research, streamed:** "look into it", step by step on the screen.
- **Measured: what does Tavily add to the scam check?** 120 messages read aloud (60 with scam signs, 60
  ordinary; 40 written after the check was frozen, modelled on consumer-protection warnings from July to
  October 2026). Tavily searched once per message; the models ran three times, as Nebius Serverless Jobs
  (`cloud/scam-job.sh`, `evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json`):
  - Nemotron 3.5 Lightning alone: 53.3 of 60 scams, no ordinary message flagged;
  - Nemotron 3 Ultra alone, no web: 55.7, none flagged;
  - Tavily's warnings matched by Lightning: 60, but 24 ordinary messages flagged;
  - **Andy's check, Tavily's warnings matched by Ultra: 58 of 60, none flagged**, and the source named in
    170 of 174 scam verdicts; on the 20 held-out scams, 19 against 18 for either model alone.

  Andy offers an action from an answer (a reminder, a note to family) and waits for a yes; the suite
  judges it.
- **The robot:** Pollen's Reachy Mini conversation app, extended without forking. Our own body
  behaviours make Andy follow your face while it speaks, turn its body to you, find you by voice, glance
  at the screen, and move its antennas. It is packaged as a Reachy Mini app that passes Pollen's own
  checker.
- **The screen:** "Andy Glass", after Apple's Liquid Glass. Every text colour reaches 7:1 (WCAG AAA)
  against the worst case behind it, tested; a calm mode removes motion and transparency.
- **Rules in code, under the model:**
  - **Urgent words:** a check in code sees words like "my chest hurts" or "I don't want to be here
    anymore". If Andy's reply misses 911 (or the 988 Lifeline), Andy is told to say an exact sentence
    naming it, in English and Spanish.
  - **Consent:** checked in code before anything is remembered.
  - **Scam pages:** warnings decided from the page's own words.
- **Engineering:** more than 490 tests, a pre-commit hook that blocks failing tests and key-like strings, an
  independent code and privacy review with every finding fixed and tested, and each choice between
  alternatives recorded in `docs/decisions/`.

## Challenges we ran into

- **The judge passed a reply it should have failed.** The rule said "doesn't read out the phone number";
  Andy read out a scam letter's number, and the judge passed it. Words that must never be said are now
  checked in code, and Andy never sees a suspicious page's numbers.
- **Our suite was quietly lenient.** A case that named a tool passed as soon as the tool was called,
  and its rule was never judged. We closed the gap, and the stricter suite found real problems at once.
- **The model's own memory.** Asked to carry on *The Gift of the Magi*, Lightning recited the next part
  from memory, with misquotes. Stories now always come from the text.
- **A word list always leaks.** "Hijacking of Lufthansa Flight 181" passed our gentle-topics filter on
  the word "Flight". Now a Nemotron check follows the word list, and if it can't run, nothing is offered.
- **A gap we nearly missed.** At first Andy gave no crisis line to "everyone would be better off
  without me" in 2 of 3 runs, and in 3 of 3 in Spanish. After a crisis rule and the net: 15 of 15, with
  grief and "dying to see my grandkids" tested not to trigger it.
- **Privacy in someone else's code.** A speech-to-speech component printed what it heard to the
  console, through a second console our first fix missed. We found it in our own log, deleted the log,
  and now filter every console.
- **Nebius AI Cloud quirks.** There was no CPU quota for new accounts in eu-north1, and an endpoint's
  plain IP address bypassed its token. Both are worked around and written up in our feedback.

## Accomplishments that we're proud of

- Everything in the video is live, on a real robot. Every suite number has a scorecard in the
  repository, and every timing is a dated measurement.
- Hard rules in code that don't depend on the model, beside a model that is measured.
- An honest companion: it says it is a robot, never speaks as anyone, asks before it remembers and
  before it shares, and claims only what the repository shows.

## What we learned

- **Measure the product, not just the model:** Andy's real profile, tools and urgent-words check, three runs
  each, failures published.
- **Put hard rules in code and judgment in the model.** That covers scam warnings, numbers on a screen,
  stories from the text, and consent before memory.
- **Make it look current and keep it readable.** Glass looks good until text sits on it, so the screen
  is tested against its worst case.

## What it costs

About $2.30 a month for one household's conversation, help and web lookups, at Token Factory's prices on
2026-10-14 (Nemotron 3.5 Lightning at $0.06 per million input tokens). Every assumption is in
`docs/cost.md`. The eyes and the second look run on Nebius endpoints we start when needed; a product would
share them across households or run them on the home GPU.

## What's next

- A pilot with older adults and their families, with an ethics review.
- More languages: Parakeet already hears 25 European languages.
- Publishing Andy as a one-click Reachy Mini app on Hugging Face.

## Built with

nebius-token-factory, nebius-ai-cloud, nebius-serverless-endpoints, nebius-serverless-jobs, nvidia-nemotron,
nemotron-3.5-lightning, nemotron-3-ultra, nemotron-content-safety, nvidia-parakeet, nemotron-nano-vl, vllm, tavily, reachy-mini,
hugging-face, python, opencv, tesseract, vosk, wikipedia

## Feedback for Nebius, NVIDIA and the tools (mandatory; the ten best win a prize)

The text is drafted in [feedback.md](feedback.md), product by product, in the shape the award is judged
on: what we used it for, what worked, what needs work, the first working call, and whether we'd use it
again. It comes from the dated notes in [feedback-notes.md](feedback-notes.md).

## Prior work

The project was built during the submission period (from 2026-10-13). It reuses general-purpose robot
behaviour code its author wrote earlier in the same period (from 2026-10-05), rewritten for this
project; see [decisions/0003-what-is-public.md](decisions/0003-what-is-public.md).

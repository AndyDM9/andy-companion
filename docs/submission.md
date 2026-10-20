# Devpost submission (draft)

Fill in the final name and links before submitting. Every sentence must be true and checkable in the
repository; numbers are from the run named beside them. Sections follow Devpost's project template.
Last revised 2026-10-20 (rounds 4 to 9: Devpost's judging session, the gap research, zooming in, the Physical AI moments and judging without a robot); re-read against [rules-compliance.md](rules-compliance.md) before submitting.

## Tagline (under 200 characters)

A small robot that reads the letter in your hand and finds your glasses: a companion for older adults who live at home, and the family who help. Built with NVIDIA Nemotron on Nebius, and Tavily.

## Inspiration

Three in four US adults aged 50 and over want to keep living in their own homes (AARP's Home and
Community Preferences Survey, December 2024), and their families want to help without taking over. Scams
reach them at home: adults 60 and over reported $2.4 billion lost to fraud in 2024, against about $600
million in 2020 (FTC, *Protecting Older Consumers 2024–2025*, December 2025). Voice assistants answer questions, but they don't look at you, don't read the letter in
your hand, and don't tell you which of your family looked at what you shared. We wanted a small robot
that is honest about being a robot, useful every day, good company, and that keeps no recordings or
transcripts: only what you ask it to keep.

## What it does

Andy is a Reachy Mini that talks with you and keeps looking at you while it does. Three moments show what
a robot can do that a phone can't:

- **"Can you read this for me?"** You hold up a letter. Andy reads it on this computer, explains it, and the
  TV shows it in large print. If the page asks for gift cards or rushes you, code (not the model) puts
  **Be careful** first: "Don't call or pay yet. Check with family first."
- **"Where did I leave my glasses?"** Andy sweeps the room, NVIDIA Nemotron 3.5 Super VL on Nebius Token
  Factory reads the four views zoomed in (six tiles each at full resolution, all at once), then Andy turns its head
  straight at what it saw, checks a close-up, and points. The TV shows the four views in the order it turned, the
  close-up in place of the one it chose. Zooming in took our desk test from 0 of 9 to 9 of 9.
- **"A man called saying my grandson is in jail and needs gift cards."** You don't paste anything: you say
  it. Andy checks it against consumer-protection warnings found with Tavily, and the TV says what to do
  first ("Don't reply, pay or give any details. Check with family first."), then why: the sign in the
  message's own words, the warning and its site, and why Nemotron 3 Ultra judged it the same trick.

Also: Andy notices the room by itself (it turns to whoever speaks, and waves back with its antennas when you wave);
it remembers where you put your keys if you ask it to, and looks there first; a grandchild can teach it a move by
moving its antennas by hand. And: your day the same way every time (the date, reminders in your words, the weather); "look into it for
me", a Tavily research task shown step by step on the TV while you carry on talking; good company (open
questions about your life, jokes, real stories read a part at a time); a family photo that becomes a story,
with Andy asking about it and keeping the story only after a yes; family who see only what you share, with
Andy telling you who looked; and English and Spanish.

## What's new here

- **A scam check where scams reach people at home.** Phone filters and paste-in checkers see a text or an
  email; Andy hears about the phone call and reads the letter in your hand, and its spoken suite tests that
  it recognises the trick when you just mention it.
- **A language model that moves a robot's body to find things,** with nothing trained: Nemotron 3.5 Super
  VL reads four views, each as six zoomed tiles, as structured output; Andy turns its head to the best sighting,
  asks a strict yes-or-no question about a close-up, and points only on a yes.
- **A scam check measured five ways, with its uncertainty:** on 120 messages read aloud, three runs as
  Nebius Serverless Jobs, Tavily's consumer-protection warnings matched by Nemotron 3 Ultra caught 58 of
  60 scams (95% interval 89–99%) and flagged none of 60 ordinary messages (0–6%). Word rules alone caught
  28; each model alone caught 53 to 56, which overlaps Andy, so we don't claim more catches. What the web
  plus a strong second question buys is a named source and no false alarms: matched by the smaller
  model, the same warnings flagged 24 ordinary messages (29–53%). About $17 per 1,000 checks.
- **A robot search tested in simulation, as Nebius Serverless Jobs:** Andy's own finder in Pollen's MuJoCo scene,
  things placed at random, scored against the scene's truth: with its closer look, no false find in 7 trials without
  the object (the old way: 3 in 7) and pointing within 0.76 degrees (median), over 30 trials each.
- **Measured on the robot, not only at the desk:** 54 real turns on the Reachy Mini, a median of 1.06 s
  from the person's words being understood to Andy's first sound (95% of turns under 3.2 s, the slow
  ones with a web search).
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

## Accessibility

- Nothing to read, tap or install for the person: everything is said, and the TV shows what Andy says.
- All of Andy's words as captions, on by default; large type in Atkinson Hyperlegible (made by the Braille
  Institute for low-vision readers); every text colour at 7:1 (WCAG AAA) against the worst case behind it,
  tested.
- A calm screen with no movement or see-through panels; the TV's remote reaches every control.
- Letters in large print; pace and volume set by voice; talk over Andy and it stops.
- English and Spanish, with *usted*; the family and settings pages for helpers in the same look, 7:1, with
  48 px targets.

## How we built it

- **On this computer, beside the robot:** hearing with NVIDIA Parakeet TDT 0.6B v3 (0.02–0.08 s an
  utterance) and speaking with Qwen3-TTS, together about 7.1 GB of GPU memory; the wake phrase offline
  (Vosk); letters read with Tesseract, so only the text leaves; face following and every body behaviour.
  The finder takes each frame only once the head has stopped and settled.
- **Conversation and 35 tools:** NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory (zero data
  retention on), 0.6–0.8 s per reply measured on the robot. **NVIDIA Nemotron 3 Ultra** for hard
  questions (2.1 s) and as the suite's judge. Lightning's **structured output** turns letters into
  large-print screen cards and vets "On this day" items.
- **Eyes, in the loop:** NVIDIA **Nemotron 3.5 Super VL on Nebius Token Factory**, reasoning off. To find
  something Andy sweeps the room, the model reads four views at once as structured output, and Andy points at
  it with its head. Side by side at the desk with NVIDIA Nemotron Nano 12B v2 VL on our own **Nebius
  Serverless Endpoint** (L40S, vLLM), which Andy used until Super VL reached Token Factory this October: a
  description in 1.35 s against 3.45 s, four views in 2.08 s against 2.28 s, both right on every view, and
  nothing to start (the endpoint takes about 15 minutes). The endpoint stays one setting away.
- **A second look:** NVIDIA Nemotron 3.5 Content Safety on a second **Serverless Endpoint**, with a policy
  written for signs of crisis: on held-out phrasings our word list misses, it caught 7 of 8 with no
  false alarms, in about 0.55 s.
- **Proof:** a conversation suite of 89 spoken situations in 20 areas, English and Spanish, run as a
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
  - Every request carries `X-Project-ID`, and one conversation's requests share an `X-Session-Id`.
- **Measured: what does Tavily add to the scam check?** 120 messages read aloud (60 with scam signs, 60
  ordinary; 40 written after the check was frozen, modelled on consumer-protection warnings from July to
  October 2026). Tavily searched once per message; the models ran three times, as Nebius Serverless Jobs
  (`cloud/scam-job.sh`, `evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json`):
  - Nemotron 3.5 Lightning alone: 53.3 of 60 scams, no ordinary message flagged;
  - Nemotron 3 Ultra alone, no web: 55.7, none flagged (17 of its answers failed and are left out of its totals);
  - Tavily's warnings matched by Lightning: 60, but 24 ordinary messages flagged;
  - **Andy's check, Tavily's warnings matched by Ultra: 58 of 60, none flagged**, and the source named in
    170 of 174 scam verdicts; on the 20 held-out scams, 19 against 18 for either model alone;
  - and the baseline, Andy's own word rules for letters with no model and no web: 28 of 60, 3 flagged.

  With 95% intervals over the 60 messages (Andy 89–99% caught, 0–6% flagged), the gain over the models
  alone is in false alarms, not catches. One check costs about $0.017, almost all of it the advanced
  Tavily search: about $17 per 1,000.

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
- **Engineering:** over 800 tests (805 on 2026-10-20), a pre-commit hook that blocks failing tests and key-like strings, an
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
  plain IP address bypassed its token. A job's request holds 64 KB, a new account runs two VMs at once,
  and a job's log cuts long lines, so the scam evaluation runs as four jobs, two at a time, and prints
  its scorecard in numbered pieces. All worked around and written up in our feedback.
- **A topic is not a trick.** Asked one broad question with the scam warnings in hand, the model flagged a
  grandchild's recital invitation as "computer access": 11 of 40 ordinary messages. Two narrow questions,
  and a stronger model for the second, brought it to none of 60, and we measured why: with the smaller
  model matching, the same warnings flagged 24.

## Accomplishments that we're proud of

- Everything in the video is live, on a real robot. Every suite number has a scorecard in the
  repository, and every timing is a dated measurement.
- Hard rules in code that don't depend on the model, beside a model that is measured.
- An honest companion: it says it is a robot, never speaks as anyone, asks before it remembers and
  before it shares, and claims only what the repository shows.

## What we learned

About the problem:
- **A topic is not a trick.** A grandchild's recital invitation and a "grandchild in trouble" scam share
  their words. A warning about the topic flagged 24 ordinary messages; asking whether it is the same trick,
  with a stronger model, flagged none.
- **The action has to come first.** Someone worried about a letter needs "don't pay yet" before the
  reasons, so the TV puts it first and the evidence under it.
- **Questions can feel like tests.** Research with older adults steers away from "Do you remember…?", so
  Andy asks open questions about a person's life instead.

About building it:
- **Measure the product, not just the model:** Andy's real profile, tools and urgent-words check, three runs
  each, failures published.
- **Put hard rules in code and judgment in the model.** That covers scam warnings, numbers on a screen,
  stories from the text, and consent before memory.
- **The web finds; a strong model judges.** Tavily's warnings let every scam be caught, but only Nemotron
  3 Ultra could tell the same trick from the same topic; a bigger model without the web caught fewer.
- **Make it look current and keep it readable.** Glass looks good until text sits on it, so the screen
  is tested against its worst case.

## What doesn't work yet

- No study with older adults yet; a pilot with an ethics review comes next.
- The finder has no rate at home yet. In a dozen tries during development (2026-10-19 and 20, the code changing
  between them) it found the glasses on a table and on the floor, and on a dark chair it said several times that it
  couldn't see them, rather than guessing. The tries are scored by `evals/finder_eval.py`. Zooming in is measured at
  the desk on one room and one pair of glasses (0 of 9 before, 9 of 9 after): a direction, not a rate.
- Turning to a second voice, waving back, remembered places and moves taught by hand are tested in code; on the
  robot they wait on the founder's live test, and the TV's sound can mislead the turn to a voice.
- The scam check missed 2 of 60 scams. It never calls a message safe. On catches, it is not measurably
  better than a strong model alone; its gain is no false alarms and a named source.
- About one different suite case fails each run; every failure is in the scorecards.
- Body language while thinking is built but off until tested on the robot.
- It needs a computer with an NVIDIA GPU beside the robot, not yet a Jetson; English and Spanish only.

## What it costs

About $2.30 a month for one household's conversation, help and web lookups, at Token Factory's prices on
2026-10-14 (Nemotron 3.5 Lightning at $0.06 per million input tokens). Every assumption is in
`docs/cost.md`. The eyes are on Token Factory too, paid per picture (about 1,000 tokens a view), so nothing runs
while idle. The second look runs on a Nebius endpoint we start when needed; a product would share it across
households or run it on the home GPU. A scam check costs about $0.017.

## What's next

- A pilot with older adults and their families, with an ethics review.
- More languages: Parakeet already hears 25 European languages; Andy wakes and talks in English and
  Spanish today.
- Hearing and speaking already run on the home GPU; next, an NVIDIA Jetson beside the robot, with a smaller
  voice, the big models staying on Token Factory, and a small local model such as Cosmos Reason 2 so "where are my
  glasses?" still works offline (a plan, not tried; the README compares Andy with NVIDIA's Reachy Mini Jetson
  assistant).
- The finder measured from real tries at home, and a stronger room search where it misses.
- Publishing Andy as a one-click Reachy Mini app on Hugging Face.

## How to test it (for the judges)

You won't have a Reachy Mini, so everything physical is shown three ways:
1. **The video:** everything live on the robot, with no cuts in the pauses (at least a minute of the robot working).
2. **Andy's search in simulation** (`docs/images/sim-search.gif`, 20 s, on the demo's front page too): Pollen's own
   MuJoCo scene, Andy's own search code, live Nemotron 3.5 Super VL calls, from looking around to pointing. Measured
   over 30 trials as Nebius Serverless Jobs; anyone with a Token Factory key can run it, no robot
   (`sim/finder_sim.py`, the README says how).
3. **The real robot, live on a video call,** any time until judging ends: ask, and we'll show it.

And with no robot, GPU or keys: the screens on sample data, `uv sync && uv run python scripts/demo_screen.py`, then
`http://127.0.0.1:8093/`. *[Add the Hugging Face Space's link here once it is up: the same pages, read-only, with the
simulation's film on its front page.]* The scorecards are in `evals/results/` (its README says which is which).

## Built with

nebius-token-factory, nebius-ai-cloud, nebius-serverless-endpoints, nebius-serverless-jobs, nvidia-nemotron,
nemotron-3.5-lightning, nemotron-3-ultra, nemotron-3.5-super-vl, nemotron-content-safety, nvidia-parakeet, nemotron-nano-vl, vllm, tavily, reachy-mini,
mujoco, hugging-face, python, opencv, tesseract, vosk, wikipedia

## Feedback for Nebius, NVIDIA and the tools (mandatory; the ten best win a prize)

The text is drafted in [feedback.md](feedback.md), product by product, in the shape the award is judged
on: what we used it for, what worked, what needs work, the first working call, and whether we'd use it
again. It comes from the dated notes in [feedback-notes.md](feedback-notes.md).

## Prior work

The project was built during the submission period (from 2026-10-13). It reuses general-purpose robot
behaviour code its author wrote earlier in the same period (from 2026-10-05), rewritten for this
project; see [decisions/0003-what-is-public.md](decisions/0003-what-is-public.md).

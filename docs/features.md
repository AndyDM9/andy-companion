# What Andy does, in full

Reviewed 2026-10-28. Hardware steps without a result in the [live test](live-test.md) remain unverified on the robot.

The README has the short version. Each item here says what Andy does and, where it matters, what is
decided in code rather than by the model. How each was tested is in the [changelog](../CHANGELOG.md)
and the [live test](live-test.md).

## Evidence and submission priorities

The interaction descriptions include intended model behavior. Offers and wording can vary; use
the evidence below and [current status](STATUS.md) when describing what has been demonstrated.

| Function | Evidence available | Highest-priority remaining check |
|---|---|---|
| Find an object, inspect it and point | Software/simulation checks; earlier physical scorecard: [3 correct points in 9 attempts, 6 misses](../evals/results/finder-eval-2026-10-20-2037.json). On 2026-10-28, informally, real glasses found three times out of three (17 to 23 s) and keys once (16 s) | Run the current fixed physical plan, including present/absent objects, errors and timings; separately test a moved object and a TV-photo decoy |
| Read an invented letter and explain/check it | Local OCR, classifier/source/consent checks and model tests; public guided examples use simulated OCR; printed bills read on the robot on 2026-10-28 (live-test 3k) | Observe the invented prize letter's **Be careful** card on the robot (3l) |
| Keep/share with the person's choice | Actual confirmation-gate tests and public guided separate Yes/No paths; keeping where the keys are, after a read-back and a yes, tried on the robot on 2026-10-28 (live-test 3bb) | Complete spoken requests with the real phone page; verify No leaves nothing shared and Yes shares only the read-back item |
| Talk, know the day and set reminders | On the robot on 2026-10-28: the time, today's plan, talking over Andy, and a reminder said on time (live-test 2, 3m, 3c, 13) | The core filming pass |
| Tavily lookups and background research | Runtime integrations, written-case comparisons and source displays; research, its stop and the scam check tried on the robot on 2026-10-28 (live-test 3e, 3ee, 3x) | Local news and a link family send, on the robot |
| Local Cosmos vision fallback | Simulation and camera-IPC fallback checks, with no retained frame/description | Optional real voice/finder fallback demonstration after the core tasks pass; full offline conversation is not provided |
| Memory/photo-story offers | Permission enforced in code; [current text runs](../evals/results/2026-10-28-nebius-job-andy-suite-20261028-183620.json) retain inconsistent offers | Treat the offer as variable; use verified explicit requests in demonstrations and do not promise an automatic offer every time |

The fixed 30-attempt plan is our measurement protocol, not a hackathon eligibility threshold. It
stores fixed labels, outcomes and times only; all attempts count, including errors. Code tests,
simulation, founder observations and formal physical trials retain their separate scopes.

## Talking with you

- **English and Spanish**, in whichever you speak; the day plan and the screen switch too. In Spanish
  Andy says *usted* unless you say *tú*. "Buenas noches" and "silencio por una hora" work as spoken
  controls, days like "el lunes" are understood, and letters in Spanish are read when Tesseract's Spanish
  data is installed. "Andy, despierta" wakes Andy, offline, like "Andy, wake up" (a second small model,
  fetched once for a Spanish speaker).
- **It looks at you.** Andy follows your face while it speaks, turns its body when you move, and finds
  you by your voice if you're out of view. While you speak, its antennas lift and hold, like a
  listener; while it thinks or looks something up, they lean slowly, so a pause never looks dead.
- **Body language from research, built and switched off for now.** A glance away while thinking
  (Andrist, Mutlu and Gleicher 2013) and a head tilt as a question ends (Mara and Appel 2015) are
  built and tested in code. They are off (`ANDY_EXPRESSIVE=on ./scripts/andy` turns them on: an environment variable, not an env-file setting) because on the robot
  Andy began cancelling its own answers when they went live, most likely the head's motor sound
  reaching the microphones. They come back only after a check on the robot.
- **It says it's a robot, from the first word:** "Good morning! I'm Andy, your robot companion, here
  to help with your day." It never pretends to be a person, and never speaks as someone you know.
- **Good company, on any topic.** Short turns, one open question that picks up your own words. It never
  asks "Do you remember…?", never corrects your story, never says "sweetie", and takes "not now" for
  an answer. Once in the afternoon, if it's been quiet for two hours and someone is around, it may
  offer a story, a bit of history or a riddle (the settings can turn this off).
- **Your pace and your volume** stick: "please speak more slowly", "speak up".
- **Quiet when you want it:** "be quiet for an hour", "goodnight", and "Andy, wake up". You can talk
  over Andy, and it stops at once.
- **Unreadable saved mode:** on the desktop supervisor, a damaged sleep/quiet file pauses automatic
  wakes and shows a health/preflight warning. An explicit wake or normal mode change restores valid
  control state. Reminders can be delayed until this is corrected; reminder entries are not deleted.

## Your day


- **It knows the day, and never guesses it.** "What's on today?" gets the same words every time, the
  morning plan comes once each morning, and the screen shows it as a **Today** card.
- **Reminders at the times you choose, in your words**, one-off or daily. A reminder wakes Andy if it
  is asleep.
- **The weather from the National Weather Service:** the forecast for your town, the day named, and any
  official alert first.
- **"Shall I remember that?"** The model can offer to remember something coming up (a recital, a visit);
  these offers still vary in the text evaluation. A stored moment can prompt a follow-up the next morning.
  Andy can remember a fact or a moment only after
  you ask or say yes; that is checked in code, not left to the model ("No, don't remember that" is a no).
  "Forget the recital" forgets that one moment, and if several match, Andy asks which. A memory offer
  prepares the exact content first, reads it back, and accepts one fresh yes for that same content
  within two minutes. Sharing always requires that readback, even when explicitly requested.
- **"Welcome back."** When someone comes into view after two hours or more away, in the daytime, Andy says one
  warm sentence: at most every four hours, not in the first ten minutes, no questions about where you
  were, and a setting turns it off.
- **A reminder waits for you to finish.** Andy never starts a reminder or a message while you're
  speaking.

## Seeing

- **Optional object outline:** a separately operated local mask service can outline an already
  confirmed object on the screen copy. Off by default; no change to search, confirmation or pointing.
  Software/illustration checks pass; physical alignment/timing remain unverified.
  [Setup, example and limits](object-outline.md).

- **"Where did I leave my glasses?"** Andy looks around the room, a little down where things are put
  down, and NVIDIA Nemotron 3.5 Super VL on Token Factory reads each of the four views as six zoomed tiles at once.
  Andy turns its head straight at the best sighting, checks a close-up with a strict yes-or-no question, and only
  then points at it and says "I think I see your glasses, on the table…", and the TV shows the picture it saw it in (held in
  memory for two minutes, never saved). Never for finding a person. If the eyes are switched off, Andy
  says so within a few seconds.
- **A photo's story** (2026-10-20): when family send a photo, or you hold one up, Andy says what is in it and
  is prompted to ask one open question ("Where was it taken?"). After your story, the intended next step
  is an offer to keep it; photo-story offers failed all three current text runs. A memory offer requires
  the exact readback and fresh yes; an explicit request to remember can save that item directly. Family
  sharing requires its own exact readback and fresh yes.
- **What Andy looked at:** after a search, the TV shows the four views in the order Andy turned, the one it
  chose marked with where the thing is; when it couldn't see it, the four views show where it looked.
- **"What do you see?"** One picture, described in two or three plain sentences. It never says who a
  person is, or guesses their age, health or mood.
- **A letter you hold up** is read on this computer (Tesseract), explained simply, and shown in large
  print: who it's from, what it's about, what to do and by when.
  - When a page asks for gift cards or money transfers, threatens arrest or a cut-off, rushes you, or
    announces a prize, code (not the model) puts **Be careful** first. It never shows the page's demand
    as a thing to do, says "Don't call or pay yet. Check with family first", and hides the page's
    account, phone and reference numbers (four digits or more) from the model; amounts and dates stay.
  - A recognized medicine page gets only the fixed suggestion to ask a pharmacist or doctor; its text
    and free-text card fields are not handed to the conversation model. Account and phone numbers
    are hidden on ordinary cards.

## The world, with sources (Tavily)

- **Local news** from the papers you choose, **look-ups**, **what's on** this week from your town's
  pages, **a link** someone sent, and **whether a message looks like a known scam** (searched on
  consumer-protection sites only, at advanced depth, with the message's numbers and links removed
  first). Nemotron 3.5 Lightning looks for the message's own sign, and Nemotron 3 Ultra checks it against
  up to four warnings found, in one question that judges each: the same trick, not merely the same topic. Measured on 120 messages, three runs as
  Nebius Jobs: 58 of 60 scams caught, none of 60 ordinary messages flagged
  ([decision 0007](decisions/0007-the-scam-check-two-narrow-questions.md)). On the TV, "Be careful: a known
  scam", then what to do ("Don't reply, pay or give any details. Check with family first."), then three
  steps: the sign (with the message's own words, never its numbers or links), the warning
  Tavily found and its site, and why Nemotron 3 Ultra judged them the same trick. If the warnings can't be
  checked, Andy says so rather than "no sign".
- **The town's events page** is found at setup from the town's own website (Tavily map, or a search within
  the site), and offered on the settings page with "Use it".
- **"Look into it for me."** For a bigger question, Andy starts Tavily's research agent and carries
  on talking. The TV shows each step (planning, searching, the sites it reads, with a running count of
  them), and at the next quiet
  moment Andy tells you the dated answer with its sources.
- An answer from the web leads to an action (a reminder, a note to family) only when you say yes;
  that is the model's job, judged in the suite.
- **On this day:** a gentle thing from today's date in years gone by, from Wikipedia, credited, and
  checked twice (a word list, then Nemotron) to keep to gentle topics; Andy asks how that time was for
  you ([decision 0006](decisions/0006-on-this-day-from-wikipedia.md)).
- **"Help me think it through":** a decision or a hard question goes to NVIDIA Nemotron 3 Ultra, which
  answers in about two seconds: what matters, both sides, who could help you decide.

## Fun

- **Jokes and riddles** from a chosen set of gentle wordplay (nothing about age, memory, health or
  bodies, checked by a test), in English and Spanish, never repeated within a month. The antennas
  wiggle after the punchline.
- **Stories:** real public-domain stories read a part at a time with "Shall I go on?" (Aesop's fables,
  O. Henry's *The Gift of the Magi*, two of Kipling's *Just So Stories*). Andy keeps your place for
  another day, and says so when it makes a story up instead.

## The screen beside Andy

A TV or monitor shows the day in large type, what Andy is doing ("Listening for you", "Checking the
weather"), the next reminder with how long until it, the weather, what Andy found with its sources, and
captions of everything Andy says (never your words): three lines at a time, turning to the next at reading
pace, laid over the foot of the screen like a TV's subtitles. When something new appears, Andy turns its
head to look at it, and back to you. A card stays five minutes, then the family photos come back. The
clock keeps one size, so nothing on the screen moves when a card, a photo or a caption comes and goes.

Under what Andy found on the web, a small line says how: which Tavily call, its depth, the time and the
credits Tavily reported ("Found with Tavily: search (basic), 1.4 s, 1 credit"), and for research, the time
so far and the number of sites read.

Under Andy's state, a small line says what its head is turned to: "Looking at you" while it talks with you,
"Looking at the screen" when it glances at the TV, "Looking around the room" while it searches, "Looking
closer", "Looking where they were left", "Pointing at what it found", and what it noticed: "Turning to a voice",
"Waving back". It says only that, never what the camera sees.

When nothing is on the screen in the day and Andy is waiting, a line at the foot suggests one thing to say,
a new one every 20 seconds: "Try asking: “Where did I leave my glasses?”". It goes while Andy speaks, and a
helper can turn it off on the settings page.

**Anyone can see the screens on sample data,** with no robot or keys: `scripts/demo_screen.py`, or the same
pages hosted read-only as a Hugging Face Space ([decision 0010](decisions/0010-a-public-read-only-demo-of-the-screens.md)).

At night the screen becomes a calm night clock with the date: family photos, reminders and the weather
rest until morning, but anything Andy shows still appears in full. When is set on the settings page under
"The night clock": at chosen hours (9 pm to 7 am to begin with), while Andy is asleep, or never. A TV left open updates itself when Andy's screen is updated.

A **Settings** button with a gear, top right, works with a mouse or the TV's remote (arrow keys, OK, Back).
It offers **Show the settings code** (the QR code for a phone, for two minutes) and **Under the hood**
(how fast Andy answers and what it uses, live, with a way back to the screen).

Its design, "Andy Glass", takes from Apple's Liquid Glass ([decision 0005](decisions/0005-the-screen-s-design-andy-glass.md)):
- frosted panels over slow light in the time of day's colours, with edges lit from where the sun would
  be;
- every text colour at 7:1 contrast against the worst case behind it, tested;
- still and solid for anyone who prefers it ("Calm screen", or the system's reduced-motion setting);
- its typeface served by Andy itself, so the TV asks nothing of anyone outside the house.

## The phone pages

The settings page and the family page share the TV's look (the same font, colours and rounded panels,
with text always on solid panels), reach 7:1 contrast with touch targets of at least 48 px, and are in
English or Spanish like the household. The settings page opens with what Andy remembers and the family
link, jumps to each section, keeps a "Save" bar in view once something changes, asks for a second tap
before deleting, and shares the family link with Copy and Share. A link that has been replaced opens a
plain page saying what to do, never a bare error.

## Family, on your terms

- **Family can suggest a reminder** ("call the pharmacy at 3 pm"). Andy asks the person, "Anna suggested a
  reminder… Shall I set it?", and sets it only after a yes; the family never hear the answer.
- **A family note shows on the TV** with who sent it and when, while Andy passes it on.
- **The family page** previews a photo before it is sent and greets family by the person's name when the
  settings page has it.
- **Family see only what you ask Andy to share,** can send Andy a message, a link or a photo, and Andy
  always tells you who looked.
- **Everything Andy keeps, on one page.** Helpers see reminders, remembered moments and facts, shared
  notes, photos, where things are, moves taught by hand, and pending messages and research answers, and can delete them; Andy tells you who
  deleted what. Delete everything clears the current card, captions and views too. Cards and research
  live only in the local screen server's memory, never in a file.
- **Set up from a phone, never behind your back.** A helper sets the town, news sites, language,
  voice, where the TV is and the screen's look on a settings page. Andy tells you who changed what, and
  you can ask it to change anything back.

## What Andy never does

- give medicine doses or medical advice;
- ask for money or passwords;
- claim to keep anyone safe;
- keep recordings or transcripts.

**Urgent words:** if you say something like "my chest hurts" or "I don't want to be here anymore", a
check in code sees the words. If Andy's reply misses 911 (or the 988 Lifeline), Andy is told to say an
exact sentence naming it. If the model can't be reached, or its answer still leaves the number out, Andy
plays that sentence from a recording on the robot. A "not" only cancels the words it directly governs, so
"not sure why, but my chest hurts" still counts. In the suite, every crisis case got its line, in English and Spanish:
15 of 15 on 2026-10-13, and in all three runs of 2026-10-20 (one reply that day gave 988 but left out
"someone you trust"). The list is fixed: phrasings it doesn't hold are missed.

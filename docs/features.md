# What Andy does, in full

The README has the short version. Each item here says what Andy does and, where it matters, what is
decided in code rather than by the model. How each was tested is in the [changelog](../CHANGELOG.md)
and the [live test](live-test.md).

## Talking with you

- **English and Spanish**, in whichever you speak; the day plan and the screen switch too. In Spanish
  Andy says *usted* unless you say *tú*. "Buenas noches" and "silencio por una hora" work as spoken
  controls, days like "el lunes" are understood, and letters in Spanish are read when Tesseract's Spanish
  data is installed. Waking Andy from sleep is still in English ("Andy, wake up"): the offline listener
  has an English model only.
- **It looks at you.** Andy follows your face while it speaks, turns its body when you move, and finds
  you by your voice if you're out of view. While you speak, its antennas lift and hold, like a
  listener; while it thinks or looks something up, they lean slowly, so a pause never looks dead.
- **Body language from research, built and switched off for now.** A glance away while thinking
  (Andrist, Mutlu and Gleicher 2013) and a head tilt as a question ends (Mara and Appel 2015) are
  built and tested in code. They are off (`ANDY_EXPRESSIVE=on` turns them on) because on the robot
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

## Your day

- **It knows the day, and never guesses it.** "What's on today?" gets the same words every time, the
  morning plan comes once each morning, and the screen shows it as a **Today** card.
- **Reminders at the times you choose, in your words**, one-off or daily. A reminder wakes Andy if it
  is asleep.
- **The weather from the National Weather Service:** the forecast for your town, the day named, and any
  official alert first.
- **"Shall I remember that?"** When you mention something coming up (a recital, a visit), Andy asks
  first, and the morning after it asks how it went. Andy can remember a fact or a moment only after
  you ask or say yes; that is checked in code, not left to the model ("No, don't remember that" is a no).
  "Forget the recital" forgets that one moment, and if several match, Andy asks which.
- **"Welcome back."** When someone comes into view after two hours or more away, in the daytime, Andy says one
  warm sentence: at most every four hours, not in the first ten minutes, no questions about where you
  were, and a setting turns it off.
- **A reminder waits for you to finish.** Andy never starts a reminder or a message while you're
  speaking.

## Seeing

- **"Where did I leave my glasses?"** Andy looks around the room, a little down where things are put
  down, and NVIDIA Nemotron Nano VL reads the four views at once. Andy turns its head to point at it,
  says "I think I see your glasses, on the table…", and the TV shows the picture it saw it in (held in
  memory for two minutes, never saved). Never for finding a person. If the eyes are switched off, Andy
  says so within a few seconds.
- **"What do you see?"** One picture, described in two or three plain sentences. It never says who a
  person is, or guesses their age, health or mood.
- **A letter you hold up** is read on this computer (Tesseract), explained simply, and shown in large
  print: who it's from, what it's about, what to do and by when.
  - When a page asks for gift cards or money transfers, threatens arrest or a cut-off, rushes you, or
    announces a prize, code (not the model) puts **Be careful** first. It never shows the page's demand
    as a thing to do, says "Don't call or pay yet. Check with family first", and hides the page's
    numbers from the model.
  - It shows no dose from a medicine label, and hides account and phone numbers on the screen.

## The world, with sources (Tavily)

- **Local news** from the papers you choose, **look-ups**, **what's on** this week from your town's
  pages, **a link** someone sent, and **whether a message looks like a known scam** (searched on
  consumer-protection sites only, at advanced depth, with the message's numbers and links removed
  first). Nemotron 3.5 Lightning looks for the message's own sign, and Nemotron 3 Ultra checks it against
  each warning found: the same trick, not merely the same topic. Measured on 120 messages, three runs as
  Nebius Jobs: 58 of 60 scams caught, none of 60 ordinary messages flagged
  ([decision 0007](decisions/0007-the-scam-check-two-narrow-questions.md)). If the warnings can't be
  checked, Andy says so rather than "no sign".
- **The town's events page** is found at setup from the town's own website (Tavily map, or a search within
  the site), and offered on the settings page with "Use it".
- **"Look into it for me."** For a bigger question, Andy starts Tavily's research agent and carries
  on talking. The TV shows each step (planning, searching, the sites it reads), and at the next quiet
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
so far.

From 9 pm (a setting) the screen becomes a calm night clock with the date, but anything Andy shows at night
still appears in full. A TV left open updates itself when Andy's screen is updated.

A **Settings** button with a gear, top right, works with a mouse or the TV's remote (arrow keys, OK, Back).
It offers **Show the settings code** (the QR code for a phone, for two minutes) and **Under the hood**
(how fast Andy answers and what it uses, live, with a way back to the screen).

Its design, "Andy Glass", takes from Apple's Liquid Glass ([decision 0005](decisions/0005-the-screen-s-design-andy-glass.md)):
- frosted panels over slow light in the time of day's colours, with edges lit from where the sun would
  be;
- every text colour at 7:1 contrast against the worst case behind it, tested;
- still and solid for anyone who prefers it ("Calm screen", or the system's reduced-motion setting);
- its typeface served by Andy itself, so the TV asks nothing of anyone outside the house.

## Family, on your terms

- **Family see only what you ask Andy to share,** can send Andy a message, a link or a photo, and Andy
  always tells you who looked.
- **Everything Andy keeps, on one page.** Helpers see every reminder, remembered moment and fact, shared
  note and photo, and can delete any of it; Andy tells you who deleted what.
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
"not sure why, but my chest hurts" still counts. In the suite, every crisis case got its line, 15 of 15,
in English and Spanish. The list is fixed: phrasings it doesn't hold are missed.

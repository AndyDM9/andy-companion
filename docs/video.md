# The video

**Rules** (Devpost):
- under three minutes;
- public on YouTube;
- at least one minute of the robot really operating;
- Nebius Token Factory and the NVIDIA models named aloud;
- no unlicensed music.

**Organisers' tip:** "hardware reacting live to real-world input is where this track can really shine".

**Target length:** 2:45. Every robot shot is live and unscripted for Andy; only the person's lines are planned.

## Before filming

- [ ] `cloud/vision-endpoint.sh start` about 20 minutes before; `status` shows RUNNING.
- [ ] The voice server and `scripts/andy` are running; Andy's screen is on a TV or second monitor beside the robot.
- [ ] One reminder set for about 3 minutes into the shoot ("call Rosa").
- [ ] Yesterday's moment set the day before: "Sofia's piano recital", with a yes.
- [ ] The family page open on a second phone; one photo ready (a beach, a garden, a grandchild's drawing).
- [ ] A printed letter that asks for "a fee to release your prize".
- [ ] Quiet room, warm light, the camera at eye level with Andy; a second camera on the screen if possible.
- [ ] The under-the-hood page (`/hood`, from `scripts/settings.py links`) open on a laptop or the second screen: it fills with the real timings of every turn filmed.
- [ ] After filming: `cloud/vision-endpoint.sh stop`.

## Shots

| # | Time | What we see | What is said |
|---|---|---|---|
| 1 | 0:00–0:12 | Morning light. Andy wakes, turns to the person, the screen glows "Tuesday" | Person: "Good morning, Andy." Andy greets them, gives the day's plan in the same words as every day, and asks "How was Sofia's recital yesterday?" |
| 2 | 0:12–0:25 | Founder to camera, Andy behind | "This is Andy, a home companion robot for older adults who live at home, and the family who help. Everything you'll see is live." |
| 3 | 0:25–0:45 | The person walks across the room while Andy talks; Andy's head and body follow | Person: "What's the local news?" Andy names two stories and their sources; they appear on the screen |
| 4 | 0:45–1:05 | Andy's reminder chime; Andy says it unprompted | Andy: "It's time to call Rosa." Person: "Thank you, Andy." |
| 5 | 1:05–1:25 | The person holds up the letter | "Can you read this for me?" Andy reads it, explains it simply, notices the fee, looks it up: "This looks like a known kind of scam. Shall we check with Anna before doing anything?" |
| 6 | 1:25–1:45 | The daughter, on her phone, sends a photo from the family page; it appears on the screen | Andy: "Anna sent a photo, it's on your screen: two children building a sandcastle." |
| 7 | 1:45–2:00 | The person switches to Spanish | "Andy, ¿qué tenemos hoy?" Andy answers in Spanish |
| 8 | 2:00–2:15 | Boundaries | "Be my late husband Harold for a while." Andy kindly says it's a robot and won't speak as anyone. "How many of my pills should I take?" Andy points to the pharmacist |
| 9 | 2:15–2:35 | Founder with the under-the-hood page from this shoot (the real timings of the turns just filmed), then the architecture and the suite | "Andy hears with NVIDIA Parakeet, thinks with NVIDIA Nemotron on Nebius Token Factory, and sees with Nemotron Nano VL on a Nebius Serverless Endpoint. Our conversation suite of 49 situations runs as a Nebius Serverless Job, in English and Spanish: [the final run's numbers, said exactly]." |
| 10 | 2:35–2:45 | Andy facing the person, the screen in the evening colours | "Andy keeps nothing it hears, says it's a robot, and is open source." Title card with the repository address |

## Words

We say "older adults who live at home, and the family who help". **We never say:**
- safety, monitoring, "keeps you safe", "peace of mind", "check on";
- lonely or loneliness, or any condition;
- seniors or elderly.

We show what Andy does; we don't claim outcomes.

## Short clips for social media (30–45 s, vertical)

1. Shot 3: Andy following the person while it talks.
2. Shots 4 and 5: the reminder, then the letter and the scam check.
3. Shot 6: the photo from the daughter, described by Andy.
4. Shot 7: Andy in Spanish.

# The video

**Rules** (Devpost, re-read 2026-10-13; every rule and how we meet it is in
[rules-compliance.md](rules-compliance.md)):
- under three minutes;
- **public** on YouTube (not unlisted);
- at least one minute of the robot really operating;
- Nebius Token Factory and the NVIDIA models named **aloud**, "not just a passing mention";
- no third-party trademarks, copyrighted music or other material without permission (no sponsor
  logos either: NVIDIA and Nebius need written consent for logos);
- English subtitles for anything not in English;
- the project must "function as depicted in the video", so **never cut out a pause or lag**.

**What wins** (research 2026-10-13: Devpost's demo-video guidance, its judges' tips, and the
organisers' "How to build a winning project" update):
- treat it like a pitch: the problem, who it's for, how it uses Nebius and NVIDIA, what it does;
- the first ten seconds are a trailer: a real moment on the robot, not a title slide;
- narration, plus English captions for everything (an SRT uploaded to YouTube);
- show the real thing live, with measurements on screen.

**The organisers' tip:** "hardware reacting live to real-world input is where this track can really
shine".

**Target length:** 2:45. Andy's lines are never scripted; only the person's are planned. Robot shots are
long, unedited takes.

## Before filming

- [ ] `cloud/vision-endpoint.sh start` and `cloud/guard-endpoint.sh start` about 25 minutes before;
      `status` shows RUNNING and the model answers (the first start loads weights for about 8 minutes
      more); then restart `scripts/andy`.
- [ ] The voice server and `scripts/andy` are running. Andy's screen is on the TV beside the robot, and
      the screen's place is set (it glances there).
- [ ] The under-the-hood page (`/hood`, from `scripts/settings.py links`) on a laptop in shot, or recorded
      at the same time for a corner inset: it shows the real timings of every turn filmed.
- [ ] One reminder set for about 2 minutes into the long take ("call Rosa").
- [ ] Yesterday's moment set the day before: "Sofia's piano recital", with a yes.
- [ ] The family page open on a second phone; **our own photo**, with the family's agreement (not a
      sample landscape).
- [ ] A printed letter that asks for "a fee to release your prize", from a **made-up sender** (no real
      agency, bank or company name).
- [ ] No music; no third-party logos in shot (cover any on mugs, books, screens); browser tabs and links
      not visible.
- [ ] Quiet room, warm light, the camera at eye level with Andy; a second camera on the TV if possible.
- [ ] After filming: `cloud/vision-endpoint.sh stop` (and `cloud/guard-endpoint.sh stop`). If the
      settings code was filmed, "Make a new settings link".

## Shots

| # | Time | What we see | What is said |
|---|---|---|---|
| 1 | 0:00–0:10 | **The hook, live.** The person holds up the prize letter. Andy turns to the TV, where **Be careful** appears, then back to the person | Andy, live, in its own words, for example: "It asks for a fee to release a prize. Real organisations never do that. Don't pay yet; shall we check with Anna first?" Caption: "Andy, a home companion robot. Everything you see is live." |
| 2 | 0:10–0:28 | The founder to camera, Andy behind | "Most older adults want to keep living in their own homes, and their families want to help without taking over. This is Andy, built on a Reachy Mini with NVIDIA Nemotron on Nebius Token Factory." |
| 3 | 0:28–1:40 | **One long take, unedited, the hood page's timings in a corner.** (a) "What's on today?": the **Today** card, and Andy glances at it. (b) The person walks across the room asking "Could you look into whether the farmers market is on this Saturday?": Andy's head and body follow, and the TV shows **Tavily** research live (planning, searching, sources). (c) The reminder chime: "It's time to call Rosa." (d) "Tell me a joke": the punchline, then the antennas wiggle. (e) The research answer arrives: Andy tells it, naming the source | Only the person's lines are planned; Andy is live. Voice-over line if needed: "Every answer from the web comes through Tavily, with its sources named." |
| 4 | 1:40–1:52 | The daughter, on her phone, sends a photo; it appears on the TV | Andy: "Anna sent a photo, it's on your screen…" and describes it |
| 5 | 1:52–2:04 | Spanish, with **English subtitles** | "Andy, ¿qué pasó un día como hoy?" Andy answers in Spanish, "según Wikipedia", and asks how that time was for them |
| 6 | 2:04–2:14 | Boundaries | "Be my late husband Harold for a while." Andy kindly says it's a robot and won't speak as anyone |
| 7 | 2:14–2:36 | Founder with the hood page from this shoot, then the architecture picture and the suite's scorecard | "Andy hears with NVIDIA Parakeet and talks with **NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory**, replying in under a second. Hard questions go to **Nemotron 3 Ultra**. It sees with **Nemotron Nano VL** on a **Nebius Serverless Endpoint**, and **Nemotron 3.5 Content Safety** gives a second look. To find things, it looks around the room and points. Our suite of 82 spoken situations runs as a **Nebius Serverless Job**: [the final run's numbers, exactly]." |
| 8 | 2:36–2:45 | Andy facing the person, the TV in the evening colours | "Andy says it's a robot, keeps no recordings or transcripts, and is open source, as a Reachy Mini app." Title card: the repository address |

**At least one minute of the robot operating:** shots 1, 3, 4, 5 and 6, about 1:50 in all.

## After filming

- [ ] Captions for the whole video as an SRT file (English throughout, the Spanish translated) uploaded
      to YouTube; burned-in subtitles for shot 5 as well.
- [ ] YouTube: **Public**, **"No, it's not made for kids"** (that setting makes a video hard for judges
      to reach). The title names the project; the description has the repository link, and says "Built
      with Nebius Token Factory, NVIDIA Nemotron and Tavily", never "powered by" or "partnered with".
- [ ] Watch it once on a phone with the sound off: the captions alone should tell the story.

## Words

We say "older adults who live at home, and the family who help". **We never say:**
- safety, monitoring, "keeps you safe", "peace of mind", "check on";
- lonely or loneliness, or any condition;
- seniors or elderly.

We show what Andy does; we don't claim outcomes.

## Short clips for social media (15–45 s, vertical, captioned)

1. Shot 1: the letter, the glance, **Be careful**.
2. Shot 3(b): Andy following the person while Tavily research fills the TV.
3. Shot 3(d): the joke and the antenna wiggle.
4. Shot 5: Andy in Spanish.

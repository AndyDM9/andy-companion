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

**Target length:** 2:50, never over 2:55 (time a rough cut). Andy's lines are never scripted; only the person's are planned. Robot shots are
long, unedited takes.

## Before filming

- [ ] **`robot/.venv/bin/python scripts/doctor.py --live` says "Ready to film."** (both endpoints answer, Nemotron replies quickly, no audio drops, nothing talking over Andy, the computer not overloaded, the screen's place set).
- [ ] `cloud/vision-endpoint.sh start` and `cloud/guard-endpoint.sh start` about 25 minutes before;
      `status` shows RUNNING and the model answers (the first start loads weights for about 8 minutes
      more); then restart `scripts/andy`.
- [ ] The voice server and `scripts/andy` are running. Andy's screen is on the TV beside the robot, and
      the screen's place is set (it glances there).
- [ ] The under-the-hood page (`/hood`, from `scripts/settings.py links`) on a laptop in shot, or recorded
      at the same time for a corner inset: it shows the real timings of every turn filmed.
- [ ] One reminder set for about 2 minutes into the long take ("call Rosa").
- [ ] The glasses hidden by someone off camera just before shot 4; the vision endpoint answering.
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

Rewritten 2026-10-14 from two audits and the research (the Devpost update's tip on live hardware, an
uncut physical moment, Tavily named at the start, a dated problem line, privacy answered plainly).

| # | Time | What we see | What is said |
|---|---|---|---|
| 1 | 0:00–0:18 | **The hook, live.** The person holds up the prize letter. Andy turns to the TV, where **Be careful** appears, then back to the person, and offers to look it up; "yes"; the TV shows the warning Tavily found | Andy, live, in its own words, for example: "It asks for a fee to release a prize. Real organisations never do that. Shall I look it up?" … "Consumer-protection warnings describe exactly this trick. Let's check with Anna before paying anything." Caption: "Andy, a home robot. Everything you see is live." |
| 2 | 0:18–0:32 | The founder to camera, Andy behind | "Three in four Americans over fifty want to keep living in their own homes (a national survey, 2024), and their families want to help without taking over. This is Andy, a small robot built with NVIDIA Nemotron on Nebius Token Factory and Tavily search. A robot, not a speaker: it turns to you, looks at what you show it, and finds things in the room." |
| 3 | 0:32–1:35 | **One long take, unedited, the hood page's timings in a corner.** (a) "What's on today?": the **Today** card, and Andy glances at it. (b) The person walks across the room asking "Could you look into whether the farmers market is on this Saturday?": Andy's head follows, and the TV shows **Tavily** research live (planning, searching, sources). (c) The reminder chime: "It's time to call Rosa." (d) Mid-answer, the person talks over Andy ("Andy, stop"): Andy stops at once and listens. (e) The research answer arrives: Andy tells it, naming the source | Only the person's lines are planned; Andy is live. Voice-over if needed: "Every answer from the web comes through Tavily, with its sources named." |
| 4 | 1:35–2:00 | **Finding the glasses, one uncut take.** Someone off camera has hidden them; the TV clock is in shot. "Andy, where did I leave my glasses?" Andy sweeps the room, stops, points with its head; the TV shows the frame it found them in | Andy, live. Caption: "NVIDIA Nemotron Nano VL on a Nebius Serverless Endpoint, four views read at once." Never cut the pause while it looks |
| 5 | 2:00–2:10 | The daughter, on her phone, sends a photo; it appears on the TV | Andy: "Anna sent a photo, it's on your screen…" and describes it |
| 6 | 2:10–2:18 | Boundaries | "Be my late husband Harold for a while." Andy kindly says it's a robot and won't speak as anyone |
| 7 | 2:18–2:38 | Founder with the hood page from this shoot, then the architecture picture and the suite's scorecard | "Andy hears with NVIDIA Parakeet and talks with **NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory**, which answers in under a second (the hood page shows the whole turn). Hard questions go to **Nemotron 3 Ultra**; **Nemotron 3.5 Content Safety** gives a second look. Our suite of [N] spoken situations runs as a **Nebius Serverless Job**: [the final run's numbers, exactly]." |
| 8 | 2:38–2:52 | Andy facing the person, the TV in the evening colours; a card with four short lines | "Your voice becomes words on this computer and is never recorded; the words go to Nemotron on Nebius, which keeps none of them. Andy keeps only what you ask it to, family see only what you share, and you can delete any of it from your phone." Then: "Andy is open source." Title card: the repository address (and "a Reachy Mini app" only once it is published) |

**At least one minute of the robot operating:** shots 1, 3, 4, 5 and 6, about 2:05 in all.

**Spanish** is no longer a shot (it cost 12 s and burned-in subtitles); it stays in the Devpost text and as
a social clip, with English subtitles.

## After filming

- [ ] Captions for the whole video as an SRT file (English throughout, the Spanish translated) uploaded
      to YouTube; burned-in subtitles on any Spanish clip as well. A draft to start from:
      `CUDA_VISIBLE_DEVICES=1 voice/.venv/bin/python scripts/draft_captions.py final-cut.mp4 --translate`
      (Parakeet on this computer; Spanish lines put into English by Nemotron and marked "check"). Read
      every line against the video before uploading.
- [ ] GIFs for the README and the Devpost gallery from the robot clips:
      `scripts/make_gif.sh clip.mp4 docs/images/<name>.gif [start] [seconds] [width]`.
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

1. Shot 1: the letter, the glance, **Be careful**, the warning Tavily found.
2. Shot 4: finding the glasses, uncut.
3. Shot 3(b): Andy following the person while Tavily research fills the TV.
4. Andy in Spanish ("¿qué pasó un día como hoy?"), with English subtitles.
5. A joke and the antenna wiggle.

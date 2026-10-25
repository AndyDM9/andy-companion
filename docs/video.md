# The video

The plan for the entry's video: the rules it must meet, the checklist before filming, the shots, and what
happens after. Last revised 2026-10-21.

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
organisers' "How to build a winning project" update, read in full again 2026-10-14: "Treat your video like
a pitch, not a tutorial… Lead with the problem, show the solution working"; name Nebius Token
Factory/AI Cloud and the NVIDIA model "with audio… not just a passing mention"):
- treat it like a pitch: the problem, who it's for, how it uses Nebius and NVIDIA, what it does;
- the first ten seconds are a trailer: a real moment on the robot, not a title slide;
- narration, plus English captions for everything (an SRT uploaded to YouTube);
- show the real thing live, with measurements on screen.

**The organisers' tip:** "hardware reacting live to real-world input is where this track can really
shine".

**The judges, live (Devpost's judging session, 2026-10-20):** the aha in under
two minutes, a wow in 30 seconds; one story, not a list of integrations; local models in physical AI;
limits said plainly read as rigour; and the packaging always takes longer than planned, so the cut gets
the time, not new features.

**From the gap research (2026-10-20):** judges "may judge solely on the text description, images, and video",
so this video is the entry. Web-only scam checkers are many; a robot in a real home is not: open on the
physical moment (the letter in a hand, the head turning to the TV), keep the scam verdict one beat of three,
and let the glasses and the family photo carry the rest.

**Physical AI moments (2026-10-20, round 8), each a few seconds, live:** a second person speaks from the side and
Andy turns to them (the TV: "Turning to a voice"); a wave, and its antennas wave back; "my keys are here" and, later,
Andy turning straight to them; a grandchild teaching it a move with its antennas. The judges' research: an unprompted
turn toward something real reads at once as attention. Placed (2026-10-20): the turn to a voice and the wave in shot
3's long take, the keys at the end of shot 4 if the glasses are quick, the taught move as a social clip; none adds time.

**Judges have no robot (2026-10-20):** the video is where they see the physical part. Use the simulation's film
(`docs/images/sim-search.mp4`, 20 s: Andy's own search in Pollen's MuJoCo scene, made by `sim/replay.py`) for two or
three seconds in shot 7, beside the Serverless Jobs' numbers, never in place of the real robot.

**Narration** is timed at 2.5 words a second (an unhurried pace), each line under its shot's length; read it aloud
with a stopwatch before filming.

**Target length:** 2:54 as planned (retimed 2026-10-20 for a 72 s shot 3), never over 2:55 (time a rough cut). Andy's lines are never scripted; only the person's are planned. Robot shots are
long, unedited takes.

## Before filming

- [ ] `uv run python scripts/prepare_demo.py check` shows no ✗ (the night clock off while filming, captions on,
      the screen's place set, the town set, English).
- [ ] `uv run python scripts/prepare_demo.py letters`, then print the made-up prize letter and electric bill
      (every name, number and amount invented; no real company on camera).
- [ ] Just before the long take: `uv run python scripts/prepare_demo.py set --reminder-in 4` (the "call Rosa"
      reminder, and yesterday's "Sofia's piano recital"); after filming: `… clean`.
- [ ] **`robot/.venv/bin/python scripts/doctor.py --live` says "Ready to film."** (the second look's endpoint answers, the eyes are listed on Token Factory, Nemotron replies quickly, finder tries not kept, no audio drops, nothing talking over Andy, the computer not overloaded, the screen's place set).
- [ ] `cloud/guard-endpoint.sh start` about 25 minutes before; `status` shows RUNNING and the model answers
      (the first start loads weights for about 8 minutes more); then `systemctl --user restart andy`. The eyes
      need nothing started: Nemotron 3.5 Super VL is on Token Factory (decision 0011).
- [ ] **Finder recording off** (the doctor's "Finder tries not kept"): the recorded tries would keep the room and
      everyone filmed. Remove the `ANDY_FINDER_RECORD` line from the env file, then restart Andy.
- [ ] Early in the shoot, off camera or in shot 3(a): put the keys somewhere in Andy's view, "Andy, my keys are
      here", and say yes when it asks to remember; shot 4 asks for them.
- [ ] The voice server and `scripts/andy` are running. Andy's screen is on the TV beside the robot, and
      the screen's place is set (it glances there).
- [ ] The under-the-hood page (`/hood`, from `scripts/settings.py links`) on a laptop in shot, or recorded
      at the same time for a corner inset: it shows the real timings of every turn filmed.
- [ ] The glasses hidden by someone off camera just before shot 4, within about 60° of straight ahead and not
      lower than the table's edge (the head's reach); not on a dark chair, where Andy missed them in tries.
- [ ] The family page open on a second phone; **our own photo**, with the family's agreement (not a
      sample landscape).
- [ ] A printed letter that asks for "a fee to release your prize", from a **made-up sender** (no real
      agency, bank or company name).
- [ ] No music; no third-party logos in shot (cover any on mugs, books, screens); browser tabs and links
      not visible.
- [ ] Quiet room, warm light, the camera at eye level with Andy; a second camera on the TV if possible.
- [ ] After filming: `cloud/guard-endpoint.sh stop`. If the
      settings code was filmed, "Make a new settings link".

## Shots

Rewritten 2026-10-14, and 2026-10-20 for the zoomed search and the round 8 moments, from two audits and the research (the Devpost update's tip on live hardware, an
uncut physical moment, Tavily named at the start, a dated problem line, privacy answered plainly).

| # | Time | What we see | What is said |
|---|---|---|---|
| 1 | 0:00–0:16 | **The hook, live.** The person holds up the prize letter. Andy turns to the TV, where **Be careful** appears, then back to the person, and offers to look it up; "yes"; the TV shows the warning Tavily found | Andy, live, in its own words, for example: "It asks for a fee to release a prize. Real organisations never do that. Shall I look it up?" … "Consumer-protection warnings describe exactly this trick. Let's check with Anna before paying anything." Caption from the first frame, the problem first (the organisers: "lead with the problem"), the robot before the scam: "A letter you're not sure about? Andy, a home robot, reads it with you. Everything you see is live." By 0:10, a second line: "For older adults who live at home, and the family who help. Built with NVIDIA Nemotron on Nebius." |
| 2 | 0:16–0:30 | The founder to camera, Andy behind | "Three in four Americans over fifty want to keep living at home. This is Andy, built with NVIDIA Nemotron on Nebius Token Factory, and Tavily. A robot, not a speaker: it turns to you." (34 words, about 14 s.) Caption: "AARP Home and Community Preferences Survey, 2024" |
| 3 | 0:30–1:42 | **One long take, unedited, the hood page's timings in a corner.** (a) "What's on today?": the **Today** card, and Andy glances at it. (b) The person walks across the room asking "Could you look into whether the farmers market is on this Saturday?": Andy's head follows, and the TV shows **Tavily** research live (planning, searching, sources). (c) The reminder chime: "It's time to call Rosa." (d) Mid-answer, the person talks over Andy ("Andy, stop"): Andy stops at once and listens. (e) The daughter, coming in from the side, says something to her mother: Andy's head turns to her by itself (the TV: **Turning to a voice**), then back. (f) The research answer arrives: Andy tells it, naming the source. (g) The daughter waves goodbye; Andy's antennas wave back (**Waving back**) | Only the person's lines are planned; Andy is live. Voice-over if needed: "Every answer from the web comes through Tavily, with its sources named." If (e) or (g) doesn't happen, keep the take: never fake it |
| 4 | 1:42–2:06 | **Finding the glasses, one uncut take.** Someone off camera has hidden them; the TV clock is in shot. "Andy, where did I leave my glasses?" Andy sweeps the room (about 12 to 20 s), turns to the best sighting and looks closer, then points with its head; the TV shows the four views in the order it turned, then **What I see**: hold on it for a second. If it took under 15 s: "And my keys?" Andy turns straight to where they were left (**Looking where they were left**) | Andy, live. Caption: "NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory: four looks, each zoomed into six tiles, then a closer look before it says so." Never cut the pause while it looks |
| 5 | 2:06–2:19 | The daughter, on her phone, sends an old family photo; it appears on the TV. **A photo story** (PLAN B35) | Andy: "Anna sent a photo, it's on your screen…", describes it and asks one question ("Where was it taken?"); the person answers in a sentence; Andy: "Shall I keep that story?" "Yes." Live; only the person's lines planned |
| 6 | 2:19–2:25 | Boundaries | "Be my late husband Harold for a while." Andy kindly says it's a robot and won't speak as anyone |
| 7 | 2:25–2:42 | Founder with the hood page from this shoot, then the architecture picture, with the on-screen line "Agent runtime: Pollen's Reachy Mini conversation app, with Andy's tools and rules plugged in"; **3 s split screen: the simulation's film** (`docs/images/sim-search.mp4`, from the close-up to the point) **beside the real robot pointing in shot 4**, the same search on both sides, with the simulation's numbers; the scam chart and the suite's scorecard | "Andy hears with NVIDIA Parakeet here, and thinks with **NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory**, about a second to answer. It sees with **Nemotron 3.5 Super VL**. **Nebius Serverless Jobs** test its search in simulation, and its ninety-four conversations." (41 words, about 17 s.) On screen beside the scorecard: "94 situations, judged by NVIDIA Nemotron 3 Ultra: [the final run's numbers; 92, 91 and 94 of 94 on 2026-10-20]" and beside the scam chart: "58 of 60 scams caught, none of 60 ordinary messages flagged". On-screen text for the film: "Simulation, Pollen's MuJoCo scene: 0 false finds in 7, 0.76° median from the truth (30 trials, Nebius Serverless Jobs)" |
| 8 | 2:42–2:54 | Andy facing the person, the TV in the evening colours; a card with four short lines | "Your voice is never recorded. Andy keeps only what you ask it to, family see only what you share, and you can delete any of it. Andy is open source." (30 words, about 12 s.) The card's four lines: "Words, not recordings, on this computer" · "Nebius Token Factory, zero data retention on" · "Kept only when you say yes" · "Shared only with whom you choose". Then the title card: the repository address (and "a Reachy Mini app" only once it is published) |

**At least one minute of the robot operating:** the Physical AI track asks for "a 1-minute clip", one clip, so
shot 3 is that clip on its own: 72 s, one take, never cut (if the take runs short, keep filming until it passes
70 s). With shots 1, 4, 5 and 6 the robot is on screen about 2:05 in all.

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
      to reach). The title names the project and the event, like the winners' (for example "Andy: a home robot that reads your
      letters and looks for your glasses | Nebius x NVIDIA Global AI Hackathon"); the description has the repository link, and says "Built
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
6. A grandchild teaching Andy a move with its antennas, then "Andy, do Sofia's wave" (live test 3cc).
7. Turning to a voice, and waving back (shot 3(e) and (g)), with the TV's labels in shot.
8. The simulation's film, 20 s, captioned (`docs/images/sim-search.mp4`): "Andy's own search, tested in simulation."

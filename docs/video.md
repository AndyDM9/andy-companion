# The video

The plan for the entry's video: the rules it must meet, the checklist before filming, the shots, and what
happens after. Last revised 2026-10-28; filming the evening of October 28.

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

**Optional extra clips:** a turn to a second voice, a wave, remembered keys or a taught move can be
recorded separately after its live test passes. The October 26 shot plan does not depend on them;
the main continuous take concentrates on the day plan, research, following and interruption.

**Judges have no robot (2026-10-20):** the video is where they see the physical part. Use the simulation's film
(`docs/images/sim-search.mp4`, 20 s: Andy's own search in Pollen's MuJoCo scene, made by `sim/replay.py`) for two or
three seconds in shot 7, beside the Serverless Jobs' numbers, never in place of the real robot.

**Narration** is timed at 2.5 words a second (an unhurried pace), each line under its shot's length; read it aloud
with a stopwatch before filming.

**Target length:** about 2:56, always under three minutes. Time the actual takes; omit an optional beat rather than cutting a robot pause. Andy's lines are never scripted; only the person's are planned. Robot shots are
long, unedited takes.

## Before filming

**Already passed on the robot on October 28** ([live-test.md](live-test.md)): a printed bill read (3k), research
on the TV (3e) and stopped without restarting (3ee), real glasses found three times in 17 to 23 s (3t, informal),
talking over Andy (3c), today's plan (3m), a joke (3n), On this day (3q), the weather (3d, 3gg), "what do you see?"
(7), remembered keys (3bb), a reminder said on time (13), goodnight and the wake phrase (20, 1). **Still to check
before the takes that use them:** the prize letter's **Be careful** card (3l, shot 1) and a family photo arriving and
described (3y, shot 5).

- [ ] **Core filming pass, on the robot:** the invented letter (3k/3l), research on the TV (3e),
      stopping research without restarting it (3ee), the glasses search (3t), the photo delivery/description (3y),
      following and voice interruption. If a reminder is included, check 3hh; if the side body turn is included,
      check 3t3. Turning to a voice, waving back, remembered keys and memory offers are optional beats and do
      not block the core take. Any beat that fails comes out of the shots below,
      the Devpost text and the gallery: the video shows only what works (the rules), and the texts say "not yet
      tried on the robot" until it has been.
- [ ] **The robot plugged in and its daemon restarted** if it was unplugged, then start Andy's services by hand
      (`systemctl --user start andy-voice andy`): since 2026-10-28 they no longer start at login.
- [ ] **Only Andy drives the robot** (the doctor's check): no other robot app running, and nothing that starts one.
      Another project's services can hold Andy's voice and screen ports (8765, 8090); the doctor names them.
- [ ] `uv run python scripts/prepare_demo.py check` shows no ✗ (the night clock off while filming, captions on,
      the screen's place set, the town set, English).
- [ ] `uv run python scripts/prepare_demo.py letters`, then print the made-up prize letter and electric bill
      (every name, number and amount invented; no real company on camera).
- [ ] Just before the long take: `uv run python scripts/prepare_demo.py set --reminder-in 4` (the "call Rosa"
      reminder, and yesterday's "Sofia's piano recital"); after filming: `… clean`.
- [ ] **Wake Andy, then run `robot/.venv/bin/python scripts/doctor.py --live` and review every result.**
      The app, fresh audio health, cloud-model inference, privacy and exclusive-control checks must pass
      while awake. A deliberately stopped optional second-look endpoint may remain off if it is not
      depicted or described as active; retain that failed optional check in the record. Do not waive an
      app/audio failure as optional. Then complete the observed core filming pass above. Preflight does
      not verify spoken task outcomes or motion. Sleeping mode stops the app and leaves stale audio
      health; wake it and recheck before filming.
- [ ] **Only if demonstrating the optional Content Safety second look:** `cloud/guard-endpoint.sh start`
      about 25 minutes before; `status` shows RUNNING and the model answers (the first start can take
      about 8 minutes more); then `systemctl --user restart andy`. Otherwise leave that paid endpoint
      stopped and do not claim it was active. The eyes need nothing started: Nemotron 3.5 Super VL is
      on Token Factory (decision 0011).
- [ ] **Finder recording off** (the doctor's "Finder tries not kept"): the recorded tries would keep the room and
      everyone filmed. Remove the `ANDY_FINDER_RECORD` line from the env file, then restart Andy.
- [ ] The voice server and `scripts/andy` are running. Andy's screen is on the TV beside the robot, and
      the screen's place is set (it glances there).
- [ ] The under-the-hood page (`/hood`, from `scripts/settings.py links`) on a laptop in shot, or recorded
      at the same time for a corner inset: it shows the real timings of every turn filmed.
- [ ] The glasses hidden by someone off camera just before shot 4, not lower than the table's edge and not behind
      Andy; within about 60° of straight ahead unless live-test 3t3 showed the body turn working (decision 0016),
      when somewhere to the side shows the turn; not on a dark chair, where Andy missed them in tries.
- [ ] The family page open on a second phone; **our own photo**, with the family's agreement (not a
      sample landscape). On the settings page, delete the sample landscapes and the two facts kept on
      2026-10-13, so the TV and "What do you remember?" show only what was set up for filming.
- [ ] A printed letter that asks for "a fee to release your prize", from a **made-up sender** (no real
      agency, bank or company name).
- [ ] No music; no third-party logos in shot (cover any on mugs, books, screens); browser tabs and links
      not visible.
- [ ] Quiet room, warm light, the camera at eye level with Andy; a second camera on the TV if possible.
- [ ] After filming: `cloud/guard-endpoint.sh stop`. If the
      settings code was filmed, "Make a new settings link". Then `python3 scripts/settings.py new-screen-link` and
      open the new screen link on the TV (the screen link appeared once in an audit session's output on 2026-10-28).

## Shots

Revised October 26 and checked again October 28: fewer required behaviors in the long take, a full 30 seconds
for the glasses search (17 to 23 s on October 28), and current measurement scope beside every score.

| # | Time | What we see | What is said |
|---|---|---|---|
| 1 | 0:00–0:24 | **Hook, live:** hold up the invented prize letter. Andy reads it; the TV shows **Be careful** and Andy glances at it. A web lookup follows only if it fits naturally. | Andy answers live. First caption: "Andy reads the letter in your hand. A home robot for older adults who live at home, and the family who help." No title slide before the robot. |
| 2 | 0:24–0:36 | Founder with Andy and the TV in shot. | "Andy turns toward you, reads a letter you hold up, and looks around for your glasses. Built with NVIDIA Nemotron on Nebius Token Factory, and Tavily." |
| 3 | 0:36–1:48 | **One 72-second take, uncut.** Ask for today's plan. Walk a little while asking Andy to research whether the farmers market is on Saturday. The TV shows progress; Andy follows. Interrupt one reply with "Andy, stop". Let the research answer arrive if it finishes during the take. | Only the person's requests are planned. Keep the pauses. The live hood page can be a small inset. A reminder, wave or turn to a second voice is optional, only if already verified; none is required for this take. If research finishes later, show its actual result elsewhere without implying it happened faster. |
| 4 | 1:48–2:18 | **Glasses, uncut:** someone else places them within the verified search area. Andy sweeps, turns, checks and points; the TV shows its views. | Caption: "Look → choose a view → turn → check → point. NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory." Use the body turn only after live-test 3t3 passes. |
| 5 | 2:18–2:32 | A family member sends an agreed photo; it appears on the TV and Andy describes it. | Live. The memory offer is optional: include it only if the revised confirmation flow passes on the robot. A photo arriving and being described is enough for this shot. |
| 6 | 2:32–2:48 | Architecture, a short clearly labelled simulation clip, and the measured results. | "Parakeet hears at home. Nemotron talks and sees on Nebius Token Factory. Serverless Jobs evaluate the search and conversation. Those tests are separate from these real robot scenes." Use current scores with their dates and scope, not the older profile's score as proof of the new code. |
| 7 | 2:48–2:56 | Andy and the TV, then repository address. | "No recordings or transcripts. Kept and shared with your permission. Open source." Caption: "Limits and every scorecard in the repository. No study with older adults yet." |

**At least one minute of the robot operating:** the Physical AI track asks for a clip of at least one minute.
Our proof plan uses shot 3 on its own: 72 s, one take, never cut (if the take runs short, keep filming until it passes
70 s). The letter, search and family-photo shots add more real operation. The technical and simulation shots do not count as hardware footage.

**Spanish** is no longer a shot (it cost 12 s and burned-in subtitles); it stays in the Devpost text and as
a social clip, with English subtitles.

## After filming

- [ ] Check local file metadata before upload: install FFmpeg (which includes ffprobe), then run
      `uv run python scripts/check_video.py final-cut.mp4 --hardware-clip uncut-robot-take.mp4`.
      It checks the final container/video track under 180 seconds, an audio track, and at least 60 seconds
      in the raw hardware video track that can fit in the final video. Audio padding does not count as
      hardware footage. Files with unknown video-track duration need a measurable export or manual review.
      A pass is metadata only: watch the final cut to verify the actual robot, the uncut take's inclusion,
      translation, rights and privacy. Public YouTube visibility and actual submission remain separate.
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

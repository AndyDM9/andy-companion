# Video script: Nebius x NVIDIA Global AI Hackathon

Drafted 2026-10-25. Runs 2:54. Builds on [video.md](video.md), adding the latency, the cost and a limitations beat, and cutting the "late husband" boundaries shot. Only people's lines are scripted; Andy answers live. Never cut a pause.

| # | Time | What we see | What is said |
|---|---|---|---|
| 1 | 0:00–0:16 | **Opening hook, live.** The person holds up a made-up prize letter. Andy turns to the TV, which shows **Be careful**, then turns back and offers to look it up. The TV shows the warning Tavily found, with its source. | Andy, live: "It asks for a fee to release a prize. Real organisations never do that. Shall I look it up?" Caption: "A letter you're not sure about? Andy, a home robot, reads it with you. Everything you see is live." By 0:10: "For older adults who live at home, and the family who help. Built with NVIDIA Nemotron on Nebius." |
| 2 | 0:16–0:30 | Founder to camera, Andy behind. | "Three in four Americans over fifty want to keep living at home. This is Andy, built with NVIDIA Nemotron on Nebius Token Factory, and Tavily. A robot, not a speaker: it turns to you." Caption: "AARP Home and Community Preferences Survey, 2024" |
| 3 | 0:30–1:42 | **The required one-minute clip: one 72 s take, uncut**, with the live timings page in a corner. (a) "What's on today?" brings up the Today card. (b) The person walks across the room asking about the farmers market; Andy's head follows and the TV shows Tavily searching. (c) Reminder chime: "It's time to call Rosa." (d) "Andy, stop": Andy stops at once. (e) The daughter speaks from the side; Andy turns to her. (f) The answer arrives, with its source named. (g) The daughter waves goodbye; Andy's antennas wave back. | Only the people's lines are planned. If (e) or (g) doesn't happen, keep the take; never fake it. |
| 4 | 1:42–2:06 | **Finding the glasses, uncut.** "Andy, where did I leave my glasses?" Andy sweeps the room, takes a closer look, then points with its head. The TV shows the four views and **What I see**. | Caption: "NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory: four looks, then a closer look before it says so." |
| 5 | 2:06–2:16 | The daughter sends a family photo from her phone and it appears on the TV. Andy describes it and asks one question. | Live. Shortened by 3 s to make room for the numbers. |
| 6 | 2:16–2:40 | **The numbers.** Founder with the live timings page from this shoot, the architecture diagram, 3 s of the simulation clip, the scam chart and the cost card. | "Andy hears with NVIDIA Parakeet, running on this computer, and thinks with NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory. Median time from understood words to first sound: 1.06 seconds, over 54 real turns. Nebius Serverless Jobs test it: 58 of 60 scams caught, none of 60 ordinary messages flagged. Estimated cost: about two dollars thirty a month per home." On screen: "1.06 s median, 1.88 s p90 (54 turns, robot log, Oct 20)" · "58/60 scams caught, 0/60 false alarms, 19/20 on held-out" · "≈$2.30/month, estimated from list prices, see docs/cost.md" |
| 7 | 2:40–2:46 | **What isn't done yet.** Founder to camera. | "What it can't do yet: it misses things in dim light, the cost is an estimate rather than a bill, and it's been tested in one home." On screen: "Known limits: README → Limitations" |
| 8 | 2:46–2:54 | **Close.** Andy facing the person, a card of four lines, then the title card. | "Your voice is never recorded. Andy keeps only what you ask it to, and it's open source." Card: "Words, not recordings" · "Token Factory, zero data retention" · "Kept only when you say yes" · "Shared only with whom you choose". Title card: the repository address. |

## What changed from video.md
- The "Be my late husband Harold" boundaries shot is cut, to make room for the limitations beat the judges asked for (Oct 20 session).
- The numbers shot adds the latency, the held-out scam score and the cost, labelled "estimated".
- Each limit in shot 7 must match a line in the README's Limitations section; drop any that aren't true by filming day.

## Rules checklist
- [ ] Under 3:00; shot 3 at least 60 s with no cuts.
- [ ] "Nebius Token Factory" and the NVIDIA models said aloud.
- [ ] No music, no logos, no real company names on the prop letters.
- [ ] English captions as an SRT file.
- [ ] YouTube: **Public**, not made for kids.
- [ ] `scripts/doctor.py --live` says "Ready to film." before filming.

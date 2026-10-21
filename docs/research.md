# The research behind Andy

What we read before building, what we took from it, and what we left out. Every source was read on the
date shown. Conversation and humour research is about older adults; we apply it to everyone Andy talks
with, by our own choice. Andy makes no therapeutic or health claim from any of it.

## Conversation (researched 2026-10-13)

**What we found:**
- **Depth, not small talk.** Older adults in co-design workshops asked for follow-up questions that
  invite reflection, for a robot that shows it is listening, and for one that remembers family names
  and shared history, with a way to make it forget by voice. In live use, what frustrated people was
  interruptions and replies that were slow, repetitive or superficial.
  ([Irfan et al. 2024](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2024.1363713/full);
  [Irfan et al. 2025](https://onlineacademiccommunity.uvic.ca/implicitassociationtestsyessir/wp-content/uploads/sites/9812/2025/12/irfan.pdf))
- **Pauses.** Voice assistants tend to cut people off too early; the better choice is to wait, or to ask a
  short question. The same complaint about interruptions came up in the live use above.
- **Pacing.** Older listeners expect a voice robot to speak a little more slowly, the more so the longer
  the reply ([PMC10132265](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10132265/)). Pauses at clause
  boundaries help recall.
- **Elderspeak** ("sweetie", "are *we* ready", a sing-song tone) is patronising and harms understanding
  ([concept analysis, 2021](https://pubmed.ncbi.nlm.nih.gov/34476301/); [Williams 2009](https://pmc.ncbi.nlm.nih.gov/articles/pmid/18591210)).
- **No quizzing.** Communication guidance advises against testing people ("Do you remember…?") and
  against correcting them; Andy follows it with everyone, as a matter of courtesy.

**What Andy does with it:** short turns; one open question that picks up the person's own words; waiting
through pauses; curiosity about their past without testing it; adult to adult; *usted* in Spanish;
"not now" taken at once. All checked by the suite (chat-1 to chat-5).

## Reminiscence, carefully

Casual reminiscence is not reminiscence therapy: the literature separates simple reminiscence, life
review and life-review therapy (Webster). So Andy offers only spontaneous, casual conversation about the
past, and never calls anything therapy.

## Humour (researched 2026-10-13)

- Older adults in one study didn't enjoy humour at someone's expense and preferred affiliative,
  shared-moment humour ([Stanley et al. 2014](https://pubmed.ncbi.nlm.nih.gov/25244473/)).
- Ageist jokes read as relatable from friends but offensive from strangers, and a robot is a stranger
  ([Aberystwyth 2026](https://www.aber.ac.uk/en/news/archive/2026/03/title-286801-en.html)).
- ElliQ, a companion robot on sale, is known for puns and jokes about itself.

**What Andy does with it:** gentle puns and riddles from a chosen set, tested for topics (no age, memory,
health, bodies, death), never repeated within a month, and never made up by the model.

## Stories

Public-domain texts read in parts with "Shall I go on?". We found no research on the best length per
sitting, so about a minute and a half per part is our own choice. A story made up on request is said to
be made up. Stories used: *The Aesop for Children* (1919), O. Henry's *The Four Million* (1906),
Kipling's *Just So Stories* (1902), all from Project Gutenberg. An Andersen collection was left out
because its translator isn't named.

## Body language (researched 2026-10-13)

- **Looking away while thinking:** people look away about 1.3 s before speaking, for about 3.5 s, often
  up or to the side; a robot doing so seemed more thoughtful
  ([Andrist, Mutlu and Gleicher 2013](https://pages.cs.wisc.edu/~bilge/pubs/2013/IVA13-Andrist.pdf);
  [HRI 2014](https://dl.acm.org/doi/10.1145/2559636.2559666)).
- **How much to look away:** about 30% of the time is the human-like standard for a listener
  ([Koller et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10123290/)).
- **Nodding:** nods timed to the speaker's rhythm beat random ones
  ([Park, Breazeal et al. 2017](https://www.media.mit.edu/publications/telling-stories-to-robots-the-effect-of-backchanneling-on-a-child-s-storytelling)).
- **Head tilts of 10 to 20 degrees** raised ratings of human-likeness, with no rise in eeriness
  ([Mara and Appel 2015](https://www.rlp-forschung.de/public/facilities/333/publications/79948)).
- **Reply speed:** about one second is preferred
  ([Shiwa et al. 2009](https://unpaywall.org/10.1007%2FS12369-009-0012-8)).

**What Andy does with it:** the listening antennas and the thinking lean are live. The glance away and the
question tilt are built (`body/expressive.py`) but **switched off**: on the robot, when they went live
(2026-10-13), Andy began cancelling its own answers, most likely the motors' sound reaching the
microphones. Nodding was never switched on, for the same reason. They return only after a test on the
robot.

## Physical AI: finding things (researched 2026-10-13)

Among roughly the 50 most-liked Reachy Mini apps on Hugging Face, none searches a room for an object, and
none does listening body language ([the app store by likes](https://huggingface.co/spaces?filter=reachy_mini&sort=likes)).
The most-liked apps react physically to something the camera notices. NVIDIA's
[Reachy Mini Jetson tutorial](https://www.jetson-ai-lab.com/tutorials/reachy-mini-jetson-assistant)
sweeps the body and settles before taking a frame. **What Andy does:** "where did I leave my glasses?"
sweeps the room, reads four views in parallel with Nemotron Nano VL, and points with the head.

## Finding small things: zoom in, then look closer (researched 2026-10-20)

The founder's first tries at home: Andy found the glasses some times and not others. The cause was in our code:
each 1920x1080 frame was shrunk to 768 pixels before the model saw it, so a pair of glasses across a room (about 50
to 80 pixels at 1080p, from the camera's calibration, `reachy_mini/media/camera_constants.py`) became 20 to 30.
Nemotron 3.5 Super VL reads an image as 16-pixel patches at the size it is sent, without tiles of its own
([model card and processor config](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16), read
2026-10-20), so what we threw away was gone.

What the research says works, and what Andy does (decision 0012):
- **Slice the picture and read the slices** (SAHI, [arXiv 2202.06934](https://arxiv.org/abs/2202.06934): +5 to +7 AP
  for small objects with no retraining). Andy reads each view as six overlapping tiles at full size, all at once.
- **Find, then crop and check** (Zoom-Refine, [arXiv 2506.01663](https://arxiv.org/html/2506.01663v1); V*,
  [arXiv 2312.14135](https://arxiv.org/html/2312.14135v2); ZoomEye, [arXiv 2411.16044](https://arxiv.org/html/2411.16044)):
  gains of several points to tens of points on high-resolution benchmarks. Andy's version is physical: it turns its
  head straight at the best sighting, lets the picture settle, and checks a close-up from the middle of the lens,
  the peripheral-then-foveal search of robot vision ("Curious George", Meger et al., Robotics and Autonomous Systems
  2008, [abstract](https://users.isy.liu.se/cvl/perfo/abstracts/meger08.html)).
- **No confidence numbers:** a vision model's own confidence is poorly calibrated
  ([arXiv 2405.02917](https://arxiv.org/html/2405.02917v1)); a second look at a closer picture is the check.
- **No "enhance":** we found no evidence that sharpening, contrast stretching or super-resolution helps these
  models, and resampling is among the corruptions that hurt them most (VLM-RobustBench,
  [arXiv 2603.06148](https://arxiv.org/html/2603.06148)). More real pixels beat filters.
- **Not now:** a local open-vocabulary detector (OWLv2, Grounding DINO; NVIDIA's NanoOWL for a Jetson) as a fast
  first pass; the camera's 4K mode (the daemon sets the resolution once at start); a second row of views lower down.

Measured at the desk (`evals/zoom_check.py`, [scorecard](../evals/results/zoom-check-2026-10-20-1711.json)): a CC0
photo of a living room ([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Living_room_in_apartment_of_Condom%C3%ADnio_do_Edif%C3%ADcio_Zaher,_Le_Blond,_Rio_de_Janeiro,_Brazil.jpg))
with a real pair of reading glasses on its coffee table, 9 frames with them (as taken, mirrored, cropped, darker,
softer, noisier, and three further away) and the same 9 with them painted out. The old way found them in 0 of 9; the
tiles in 9 of 9 (95% interval 70 to 100%), with no sighting in the 9 without; the closer look confirmed 8 of 9 and
said yes to none of the 9 painted-out spots. Reading the four views' 24 tiles at once takes about 1.8 s, as one view
did before. One room and one pair of glasses: a direction, not a rate. The rate comes from the robot's own recorded
tries at home.

## NVIDIA options considered (researched 2026-10-13)

| Option | What it would add | Status |
|---|---|---|
| Magpie TTS Multilingual 357M ([Hugging Face](https://huggingface.co/nvidia/magpie_tts_multilingual_357m)) | An NVIDIA voice, so every model in the speech loop is NVIDIA's | **Measured 2026-10-14, not switched:** on an RTX 3090 it makes speech 2.5 times faster than real time, but whole sentences at once (no streaming), so Andy's first sound would come 0.6 to 2 s after the reply starts, against 0.10 to 0.33 s now (`voice/magpie-eval/`, [timings](../evals/results/magpie-eval-2026-10-14-0932.json)). Shorter phrases or TensorRT could close the gap later |
| Nemotron 3.5 ASR Streaming 0.6B ([Hugging Face](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b)) | 40 locales with language detection | Later; Parakeet works well |
| Cosmos Reason 2 ([Hugging Face](https://huggingface.co/nvidia/Cosmos-Reason2-2B)) | Physical reasoning, pointing, boxes | Later; Nano VL already finds things |
| Llama Nemotron Embed and Rerank | Cross-lingual memory search | Later; invisible without a demo |
| Audio2Face-3D, Jetson | — | Not a fit (no face; no Jetson here) |

## Scams this autumn, and a fair test (researched 2026-10-14)

The 40 held-out messages in the scam evaluation are modelled on warnings published from July to October
2026: law-enforcement impersonation that asks for payment through a cryptocurrency kiosk and tells people
not to talk to family or their bank ([FBI IC3, 2026-09-17](https://www.ic3.gov/PSA/2026/PSA260917)); fake
fund-recovery agents ([FBI IC3, 2026-07-20](https://www.ic3.gov/PSA/2026/PSA260720)); a bank impostor
saying to move money "to keep it safe" ([WFSB, 2026-10-13](https://wfsb.com/2026/10/13/banking-group-launches-campaign-help-consumers-spot-impersonation-scams));
texts with only a name and a question mark ([Malwarebytes, October 2026](https://malwarebytes.com/blog/threat-intel/2026/10/your-whos-this-reply-is-exactly-what-text-scammers-want));
and the FTC's alerts on gold couriers, payment by gift card, wire or crypto, and toll notices
([consumer.ftc.gov](https://consumer.ftc.gov/consumer-alerts)). **What Andy does with it:** the check in
[decision 0007](decisions/0007-the-scam-check-two-narrow-questions.md), measured four ways.

## Who it's for, in one number

Three in four US adults aged 50 and over want to stay in their current homes (AARP's Home and Community
Preferences Survey, 3,090 adults, fieldwork June to July 2024, released 2024-12-10:
[press release](https://www.aarp.org/press/releases/2024-12-10-new-aarp-report-majority-adults-50-plus-age-place-policies-communities-catch-up.html)).

## Tavily's newer options (read 2026-10-14)

From [Tavily's changelog](https://docs.tavily.com/changelog): `filter_by_language` (August 2026) keeps only
pages in the chosen language, which Andy uses for a Spanish speaker's news and events; `exact_match`
(February 2026) and the `X-Human-Id` header (May 2026) were read and not used yet. From the
[search API reference](https://docs.tavily.com/documentation/api-reference/endpoint/search):
`include_usage` reports each call's credits, which the TV shows.

## Apple's Liquid Glass, for the screen

See [decision 0005](decisions/0005-the-screen-s-design-andy-glass.md).

## On this day

See [decision 0006](decisions/0006-on-this-day-from-wikipedia.md).

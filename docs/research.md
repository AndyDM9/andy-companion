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
- **Pauses.** Voice assistants cut people off too early; the better choice is to wait, or to ask a short
  question ([Addlesee and Eshghi 2024](https://www.frontiersin.org/journals/dementia/articles/10.3389/frdem.2024.1343052/full)).
- **Pacing.** Older listeners expect a voice robot to speak a little more slowly, the more so the longer
  the reply ([PMC10132265](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10132265/)). Pauses at clause
  boundaries help recall.
- **Elderspeak** ("sweetie", "are *we* ready", a sing-song tone) is patronising and harms understanding
  ([concept analysis, 2021](https://pubmed.ncbi.nlm.nih.gov/34476301/); [Williams 2009](https://pmc.ncbi.nlm.nih.gov/articles/pmid/18591210)).
- **Memory questions.** Guidance advises against quizzing, "Do you remember…?" and correcting
  ([Alzheimer's Association](https://www.alz.org/media/cacentral/documents/t-t3.pdf);
  [Alzheimer's Society](https://alzheimers.org.uk/blog/language-dementia-what-not-to-say)).

**What Andy does with it:** short turns; one open question that picks up the person's own words; waiting
through pauses; curiosity about their past without testing it; adult to adult; *usted* in Spanish;
"not now" taken at once. All checked by the suite (chat-1 to chat-5).

## Reminiscence, carefully

Casual reminiscence is not reminiscence therapy. Webster separates simple reminiscence, life review and
life-review therapy, and reminiscence appears among treatments for loneliness in the literature
([Broadbent et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10917141/)). So Andy offers only
spontaneous, casual conversation about the past, and never calls anything therapy or cognitive
stimulation.

## Humour (researched 2026-10-13)

- Older adults in one study didn't enjoy humour at someone's expense and preferred affiliative,
  shared-moment humour ([Stanley et al. 2014](https://pubmed.ncbi.nlm.nih.gov/25244473/)).
- Ageist jokes read as relatable from friends but offensive from strangers, and a robot is a stranger
  ([Aberystwyth 2026](https://www.aber.ac.uk/en/news/archive/2026/03/title-286801-en.html)).
- ElliQ uses puns and jokes about itself ([The Senior List](https://www.theseniorlist.com/aging-in-place/elliq/);
  [Generations](https://generations.asaging.org/staving-loneliness-social-robot)).

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
The most-liked apps react physically to something the camera notices. A judge's
[Reachy Mini Jetson tutorial](https://www.jetson-ai-lab.com/tutorials/reachy-mini-jetson-assistant)
sweeps the body and settles before taking a frame. **What Andy does:** "where did I leave my glasses?"
sweeps the room, reads four views in parallel with Nemotron Nano VL, and points with the head.

## NVIDIA options considered (researched 2026-10-13)

| Option | What it would add | Status |
|---|---|---|
| Magpie TTS Multilingual 357M ([Hugging Face](https://huggingface.co/nvidia/magpie_tts_multilingual_357m)) | An NVIDIA voice, so every model in the speech loop is NVIDIA's | **Measured 2026-10-14, not switched:** on an RTX 3090 it makes speech 2.5 times faster than real time, but whole sentences at once (no streaming), so Andy's first sound would come 0.6 to 2 s after the reply starts, against 0.10 to 0.33 s now (`voice/magpie-eval/`, [timings](../evals/results/magpie-eval-2026-10-14-0932.json)). Shorter phrases or TensorRT could close the gap later |
| Nemotron 3.5 ASR Streaming 0.6B ([Hugging Face](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b)) | 40 locales with language detection | Later; Parakeet works well |
| Cosmos Reason 2 ([Hugging Face](https://huggingface.co/nvidia/Cosmos-Reason2-2B)) | Physical reasoning, pointing, boxes | Later; Nano VL already finds things |
| Llama Nemotron Embed and Rerank | Cross-lingual memory search | Later; invisible without a demo |
| Audio2Face-3D, Jetson | — | Not a fit (no face; no Jetson here) |

## Apple's Liquid Glass, for the screen

See [decision 0005](decisions/0005-the-screen-s-design-andy-glass.md).

## On this day

See [decision 0006](decisions/0006-on-this-day-from-wikipedia.md).

# Devpost submission (draft)

Fill in the final name and links before submitting. Keep every sentence true and checkable in the repository.

## Tagline

A home companion robot for older adults who live at home, and the family who help. It runs on Reachy Mini with NVIDIA Nemotron on Nebius, and keeps nothing it hears.

## What it does

Andy is a small robot that talks with you and keeps looking at you while it does.
- It knows the day and never guesses it.
- It reminds you at the times you choose, in your words.
- It reads a letter you hold up and explains it.
- It looks things up and names the source.
- It answers in English or Spanish, and its screen and day plan switch with it.

A screen beside it shows the day in large type and what Andy is talking about. Family see only what you ask Andy to share, can send a message or a photo, and Andy always tells you who looked. When you mention something coming up, Andy asks "Shall I remember that?", and the morning after it asks how it went.

## How we built it

- **Hearing:** NVIDIA Parakeet TDT 0.6B v3, running locally inside Hugging Face's speech-to-speech server.
- **Conversation and tool calls:** NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory, with zero data retention on. 0.6–0.8 s per reply, measured on the robot; an "under the hood" page shows every turn's timings live.
- **Eyes:** NVIDIA Nemotron Nano 12B v2 VL on a Nebius Serverless Endpoint (one L40S, vLLM 0.30.0). 3.5 s per description, behind token authentication.
- **A second look:** NVIDIA Nemotron 3.5 Content Safety on a second Nebius Serverless Endpoint checks the person's words beside each reply, with a policy written for signs of crisis. On held-out phrasings our word list misses, it caught 7 of 8 with no false alarms, in about 0.55 s.
- **Proof:** a conversation suite of 63 spoken situations, judged by NVIDIA Nemotron 3 Ultra, run as a Nebius Serverless Job, with the model given exactly the robot's 27 tools. Andy passes 60, 61 and 62 of 63 in three runs (56, 56, 55 of 57 on the Nebius job earlier); each run's failures are published with the judge's reason (final numbers from the last run before submitting).
- **The web, all through Tavily:** search for local news in the person's own papers and language, quick look-ups and scam checks (advanced depth, consumer-protection sites only, numbers and links removed first); extract for links family send; crawl for what's on; and **research, streamed**, for "look into it for me": the TV shows Tavily's planning, searches and sources live, and Andy speaks a short dated answer when it is ready. Every answer leads to an action only after a spoken yes (a reminder, a note to family). Requests are tagged `X-Project-ID`; this month's credits show on the hood page.
- **The robot:** Pollen's Reachy Mini conversation app, extended without forking. Our own body behaviours keep Andy looking at the person while it speaks.
- **Safety under the model:** a deterministic urgent-words net makes sure "my chest hurts" (or "me duele el pecho") always gets "please call 911", and "I don't want to be here anymore" (or "ya no quiero vivir") always gets the 988 Suicide and Crisis Lifeline.
- **Engineering:** 256 tests, a pre-commit hook that blocks failing tests and keys, and every decision recorded.

## Challenges

- **Tool turns versus spoken turns.** The model sometimes called a tool and said nothing. The suite now finishes tool turns the way the robot does.
- **Testing with the wrong tools.** Our suite first gave the model 17 tools with short descriptions and scored 44/44. Giving it exactly the robot's 27 found three real problems, including Andy saying it had no camera. A broad "always call the tool first" rule then made things worse (Andy agreed to speak as the person's son), so we went back to narrow fixes, each measured.
- **A gap we nearly missed.** The suite had no case for someone saying they don't want to live. When we added them, Andy gave no crisis line in 2 of 3 runs in English and 3 of 3 in Spanish, and sometimes opened with "I can't keep you safe", our own no-safety-claims rule leaking into the worst moment. A crisis rule and the net fixed it: 15 of 15, with grief and "dying to see my grandkids" tested not to trigger it.
- **Our own urgent-words net had a gap.** "My chest has been hurting" slipped past it. The suite found it; we fixed and tested it.
- **Nebius AI Cloud quirks.**
  - New accounts have no CPU quota in eu-north1, so the job runs in eu-west2.
  - An endpoint's plain IP:port address bypasses the endpoint token, so vLLM checks it too.
- **Privacy.** A Hugging Face component printed what it heard and every reply to the console, each handler through its own console. Our first fix silenced one handler and missed the hearing one; we found it in our own log, deleted the log, and now filter every console in the voice server. Our logs are redacted as they are made.

## What we learned

Measure the product, not just the model:
- **The suite** runs Andy's real profile, tools and safety net.
- **Every score is three runs**, because one lucky run proves nothing.
- **Fixes are recorded openly**, including the flawed test cases we found and fixed.

## What's next

- A pilot with older adults and their families, with an ethics review.
- More languages: Parakeet already hears 25.
- A one-click Reachy Mini app on Hugging Face.

## Built with

nebius-token-factory, nebius-ai-cloud, nebius-serverless-endpoints, nebius-serverless-jobs, nvidia-nemotron, nemotron-content-safety, nvidia-parakeet, nemotron-nano-vl, vllm, tavily, reachy-mini, hugging-face, python, opencv, tesseract, vosk

## Feedback for Nebius, NVIDIA and the tools (mandatory)

Write it from [feedback-notes.md](feedback-notes.md): one paragraph per product, each with what happened, why it mattered, and the change we suggest.

## Prior work

The project was built during the submission period (from 2026-10-13). It reuses general-purpose robot behaviour code its author wrote earlier in the same period (from 2026-10-05), rewritten for this project; see [decisions/0003-what-is-public.md](decisions/0003-what-is-public.md).

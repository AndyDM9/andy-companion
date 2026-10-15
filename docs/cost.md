# What Andy costs to run, for one household

An estimate, with every price dated and every assumption stated so it can be checked or redone. Prices
are from Nebius Token Factory's model list and Tavily's pricing page on **2026-10-14**; they change.

## The services, per month

| Part | Price (2026-10-14) | Assumed use | Per month |
|---|---|---|---|
| Conversation: NVIDIA Nemotron 3.5 Lightning on Token Factory | $0.06 per million input tokens, $0.24 per million output | 80 model calls a day (about 50 turns, some with a tool); 10,000 input tokens a call (7,514 measured for Andy's instructions and 35 tools, plus the conversation so far); 80 output tokens a call | **about $1.50** |
| Hard questions and the scam check's second look: Nemotron 3 Ultra | $1.00 per million input, $3.00 per million output | 2 "think it through" and 2 scam checks a day, about 1,500 tokens in and 1,500 out each | **about $0.75** |
| Letter cards and On this day: Lightning, structured output | as above | a few calls a day, under 2,000 tokens each | **under $0.05** |
| The web: Tavily | Free up to 1,000 credits a month; then $0.008 a credit | 10 searches a day at basic depth (1 credit), 2 scam checks (2 credits each), 2 research tasks a week (about 25 credits each, estimated from this month's use) | **about 640 credits: free**, or about $5 if paid |
| Hearing (Parakeet) and speaking (Qwen3-TTS) | Free: they run on the home computer's GPU | — | **$0** |

**Altogether: about $2.30 a month** for conversation, help and the web, at this level of use (the web free within Tavily's 1,000 monthly credits). The estimate
scales with use: twice the talking is about twice the conversation line.

## The eyes and the second look

For the hackathon, Nemotron Nano VL (the eyes, finding things) and Nemotron 3.5 Content Safety (the
second look) each run on a Nebius Serverless Endpoint, one L40S at about **$1.55 an hour** while running.
We start them when needed and stop them after; stopped, they cost nothing for compute. An endpoint kept
running for one household all month would cost about $1,100, so that is not how a product would run them:

- **Shared:** one endpoint serving many households, batched. The cost per household falls with the
  number of households.
- **At home:** Nemotron Nano 12B v2 VL in FP8 is about 14 GB of weights, which fits a 24 GB home GPU
  beside the voice server; the Content Safety model is smaller still.

Both are open questions for after the hackathon; we haven't measured either.

## Hardware, once

- A Pollen Robotics Reachy Mini (the Lite version, on USB).
- A computer with an NVIDIA GPU of 8 GB or more for the voice server.
- Any TV or monitor for the screen.

## How to redo this

Token Factory lists each model's price per token in its models API (`GET /v1/models`, `pricing`). The
7,514 input tokens are one real request with Andy's instructions and all 35 tools (2026-10-14). Tavily's
monthly use shows on Andy's `/hood` page, and since 2026-10-14 each web answer on the TV shows the
credits Tavily reported for it (a basic search measured at 1 credit, live), so the web line can be
checked against real use.

# What Andy costs to run, for one household

An estimate, with every price dated and every assumption stated so it can be checked or redone. Prices
are from Nebius Token Factory's model list and Tavily's pricing page on **2026-10-14**; they change.

## The services, per month

| Part | Price (2026-10-14) | Assumed use | Per month |
|---|---|---|---|
| Conversation: NVIDIA Nemotron 3.5 Lightning on Token Factory | $0.06 per million input tokens, $0.24 per million output | 80 model calls a day (about 50 turns, some with a tool); 10,000 input tokens a call (7,514 measured for Andy's instructions and 35 tools, plus the conversation so far); 80 output tokens a call | **about $1.50** |
| Hard questions and the scam check's warning match: Nemotron 3 Ultra | $1.00 per million input, $3.00 per million output | 2 "think it through" and 2 scam checks a day, about 1,500 tokens in and 1,500 out each | **about $0.75** |
| Letter cards and On this day: Lightning, structured output | as above | a few calls a day, under 2,000 tokens each | **under $0.05** |
| The web: Tavily | Free up to 1,000 credits a month; then $0.008 a credit | 10 searches a day at basic depth (1 credit), 2 scam checks (2 credits each), 2 research tasks a week (about 25 credits each, estimated from this month's use) | **about 640 credits: free**, or about $5 if paid |
| Hearing (Parakeet) and speaking (Qwen3-TTS) | Free: they run on the home computer's GPU | — | **$0** |

**Altogether: about $2.30 a month** for conversation, help and the web, at this level of use (the web free within Tavily's 1,000 monthly credits). The estimate
scales with use: twice the talking is about twice the conversation line.

This is an **API-use estimate**, not the total cost of owning or operating Andy. It excludes the computer,
robot and display, electricity, internet, maintenance, the optional hourly second-check endpoint, and the
eyes priced below. If Tavily's free allowance is unavailable or shared with other use, include the paid web
line. The developer's current pay-as-you-go account is not evidence that a household's web use will be free.

## The eyes

Since 2026-10-20 the eyes are NVIDIA Nemotron 3.5 Super VL on Token Factory, paid per picture. A description is
the camera's view at 1280 px wide with its middle at full detail (since 2026-10-25): about 1,900 input tokens (1,898
measured, against about 490 for the 768 px picture before) and under 60 output. A search reads
each of its four views as six tiles at full resolution: measured on a 1920 x 1080 view (2026-10-20), 3,636 input
tokens and about 190 output a view, and 651 in and 33 out for each closer look (one or two). A search is about
**15,000 to 16,000 input tokens and 800 output**. At Token Factory's price (its models API, 2026-10-20: $0.30 per
million input tokens, $0.90 per million output, served from us-north1), a search is about **$0.005** and a
description about $0.0006; three searches a day would add about $0.50 a month to the total above. Nothing runs,
and nothing is paid, while idle.

## The scam check, per check (measured 2026-10-20)

One advanced Tavily search (2 credits, $0.016 on pay-as-you-go), Lightning about 180 tokens in and 65 out, and
Ultra about 560 in and 10 out: about **$0.017 a check, or $17 per 1,000**, 96% of it the search
(`evals/scam_eval.py`, `COST`).

## The second look, and the eyes on our own endpoint

Nemotron 3.5 Content Safety (the second look), and Nemotron Nano VL when the eyes are set to our own endpoint
(`ANDY_VISION=endpoint`), each run on a Nebius Serverless Endpoint, one L40S at about **$1.55 an hour** while
running. We start them when needed and stop them after; stopped, they cost nothing for compute. An endpoint kept
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
7,514 input tokens are one real request with Andy's instructions and the 35 tools it had then (2026-10-14; 38 now). Tavily's
monthly use shows on Andy's `/hood` page, and since 2026-10-14 each web answer on the TV shows the
credits Tavily reported for it (a basic search measured at 1 credit, live), so the web line can be
checked against real use.

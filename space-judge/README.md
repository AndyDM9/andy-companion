---
title: Try Andy — guided AI challenges
emoji: 🤖
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
license: apache-2.0
short_description: Real Nemotron replies to invented companion examples
---

# Try Andy

Three guided examples with real NVIDIA Nemotron 3.5 Lightning inference on Nebius Token Factory:
explain an invented bill, choose whether to share a sample family note, and respond when glasses
are absent from simulated views. No account, API key or payment is needed from a visitor.

**No robot is connected.** Camera/OCR results, searches and family-page effects are simulated.
The real confirmation gate controls the sample note; its exact readback is displayed before Yes/No.
The robot's physical performance and the real family page must be tested separately.

Only fixed invented prompts are accepted; no free text, uploads, microphone or camera input.
Ephemeral sessions are isolated, expire after five minutes of inactivity and are never written to
disk. Request paths, bodies, model text and provider errors are not logged by this application.
Provider credentials are server secrets, never in this repository or the browser.

The author funds inference. The public service limits concurrent requests and provider calls;
if unavailable, [testing instructions](https://github.com/AndyDM9/andy-companion/blob/main/docs/judging.md)
offer a separate free real-robot demonstration. This supplemental playground is not the complete
working robot or the sole judge-access arrangement.

For deployment, set `JUDGE_NEBIUS_API_KEY` as a Space **secret**, and `JUDGE_PUBLIC_ORIGIN` as a public
variable containing this Space's HTTPS origin. Without the key, the page reports inference is off.
The per-process allowance is 120 provider calls per UTC day, including failures, and resets on a
restart. There are at most two provider calls per step and two steps per sharing example.
It is an operational guard, not an account-level spending guarantee; review provider usage as well.

[Screens preview](https://andydm-andy-companion.hf.space/) ·
[Source and measured results](https://github.com/AndyDM9/andy-companion)

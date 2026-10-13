# Feedback notes for the Devpost form

The submission's feedback on Nebius Token Factory, AI Cloud and the NVIDIA tools is mandatory, and
the ten most valuable win a prize. Each note is something we met while building, with the date,
what happened, and what would have helped. Written up for the form in M10.

| Date | Product | What we met | What would help |
|---|---|---|---|
| 2026-10-13 | Token Factory | Zero data retention is off by default; prompts and completions are stored for speculative decoding unless the account owner switches it on. We found it only by reading the legal guide | Show the choice at sign-up with a plain explanation (the profile screen does offer it at sign-up; it deserves a line on why it matters for personal data) |
| 2026-10-13 | Token Factory | No NVIDIA vision-language model on serverless since 2026-08-31 (Nemotron Nano Omni moved to dedicated endpoints only), so a robot's camera needs a dedicated or self-hosted endpoint | A small serverless Nemotron VL model for robotics prototypes |
| 2026-10-13 | Token Factory | The hackathon promo form (HubSpot) did not render on first load; it worked on a second visit | — |
| 2026-10-13 | Token Factory | Nemotron 3.5 Lightning: correct tool calls in 0.62–0.83 s with thinking off; this made a spoken robot feel immediate | Publish time-to-first-token per model, with thinking on and off |
| 2026-10-13 | Nemotron 3.5 Lightning | Accepted the person's guess of the day ("is it Tuesday?") as fact without a clock; Super said it did not know | — (we give the model a clock tool) |
| 2026-10-13 | Nemotron 3.5 Lightning | Tool choice depends on the size of the tool list: with 17 tools Andy called the clock every time; with the robot's real 27, it sometimes answered "what time is it?" with an invented time. A broad system-prompt rule to call tools first fixed that but, after calling two tools, it then agreed to speak as the person's son | Guidance on tool-list size for small models, and a note that persona rules can weaken after tool results |
| 2026-10-13 | NVIDIA Parakeet (in speech-to-speech) | 0.02–0.08 s per utterance on an RTX 3090; excellent for a home robot | — |
| 2026-10-13 | speech-to-speech 1.0.0 (Hugging Face, upstream) | Transcripts are logged only as their length by default, but every speech-to-text handler prints what it heard ("USER: ...", Parakeet included) and every text-to-speech handler prints each reply ("ASSISTANT: ...") to the console, regardless of `--log_transcripts`. Each handler has its own console, so silencing one module misses the others: our first fix covered the reply print and missed Parakeet's | Gate every such print behind the same flag (worth a pull request upstream) |
| 2026-10-13 | Tavily | `safe_search` is rejected with `search_depth` fast or ultra-fast (HTTP 400). A companion for older adults needs safe results, so we use `basic` (1.4–6 s). Fast results for a local-news query were also off-topic | Allow safe search at every depth, or say so in the parameter table |
| 2026-10-13 | Tavily | Domain-limited search to consumer-protection sites (FTC, AARP) found the right warnings for a grandparent-scam message on the first try | — |
| 2026-10-13 | AI Cloud | Billing is separate from Token Factory's (a second card and a $25 top-up), which surprised us after setting up Token Factory first | One Nebius billing account across both, or a clear note at sign-up |
| 2026-10-13 | AI Cloud | L40S is offered only in eu-north1, and the endpoints guide's only example is an H100 | Show the cheapest GPU per region in the endpoint form |
| 2026-10-13 | Nemotron Nano VL | The model card says to use the vLLM nightly image; we pinned v0.30.0 | Name the first stable vLLM release that serves it |
| 2026-10-13 | AI Cloud | A new account has a CPU-only VM quota of 0 in eu-north1 (but 200 vCPUs in eu-west1/west2 and GPUs in eu-north1), so a CPU Serverless Job failed there with ResourceExhausted. We ran it in eu-west2 | Give new accounts a small CPU quota everywhere GPUs are offered, or say so in the Jobs guide |
| 2026-10-13 | AI Cloud | An endpoint lists a plain IP:port address beside the managed HTTPS one, and the plain one reaches the container directly, bypassing the endpoint token unless the app checks it too | Mark the HTTPS address as the one to use, and say that the IP:port is not covered by endpoint auth |

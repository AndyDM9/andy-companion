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
| 2026-10-13 | NVIDIA Parakeet (in speech-to-speech) | 0.02–0.08 s per utterance on an RTX 3090; excellent for a home robot | — |
| 2026-10-13 | speech-to-speech 1.0.0 (Hugging Face, upstream) | Transcripts are logged only as their length by default, but the Qwen3-TTS handler prints every reply to the console ("ASSISTANT: ...") regardless of `--log_transcripts` | Gate that print behind the same flag (worth a pull request upstream) |

# Feedback for the Devpost form

The form's feedback on Token Factory, AI Cloud and the NVIDIA tools is mandatory; the ten most valuable
win the Most Valuable Feedback award, judged on completeness, viability and potential impact. Each
product below says what we used it for, what worked, what needs work, how onboarding felt (zero to hello
world), and whether we'd build with it again, and why: the organisers' own list ("How to build a winning
project", Devpost update). Every point is from [feedback-notes.md](feedback-notes.md), dated and
reproducible. Final 2026-10-25: paste it into the form as it is, the summary first.

## The five that matter most

If only five points are read, these are the ones that would save the next builder the most time, each with the
change we would make:

1. **AI Cloud endpoints: the plain IP:port bypasses the endpoint token.** Mark the HTTPS address as the one to use,
   and say that the IP:port isn't covered by endpoint auth.
2. **Token Factory: structured output is silently ignored when thinking is on.** Return an error, or apply the
   schema after the reasoning, and say so in the structured-output guide.
3. **Nemotron 3 Ultra: with a strict schema it can loop on blank space inside the JSON** (17 of 360 answers, the same
   messages every run). Stop or repair the decoder when it loops on whitespace inside a schema.
4. **Nemotron 3.5 Lightning: no default crisis line**, in English or Spanish, without a rule from the developer. A
   default that names one (or asks the developer for one) in every supported language.
5. **Serverless Jobs: the 64 KB request and the two-VM default aren't documented.** Say both in the Jobs guide, and
   let a job mount a folder or object storage.

## Nebius Token Factory

**Used for:** every conversation turn of a home companion robot (Nemotron 3.5 Lightning, 38 tools),
hard questions (Nemotron 3 Ultra), the judge of our test suite (Ultra), and structured output for screen
cards and content vetting.
**Worked:**
- One OpenAI-compatible key for every Nemotron model made routing trivial: Lightning for everyday turns
  at 0.6 to 0.8 s, Ultra for a hard question at 2.1 s.
- Strict `json_schema` output was exact in under a second.
**Needs work:**
- **Zero data retention is off by default.** It is offered at sign-up, but without saying why it matters
  for personal conversation; we understood it only from the legal guide.
- **Structured output is silently ignored when thinking is on.** The same request returned free-text
  reasoning instead of the schema. An error, or a note in the structured-output guide, would save
  people hours.
- Time to first token, per model, with thinking on and off, isn't published. It decides whether a
  spoken robot feels alive.
**Onboarding (zero to hello world):** the OpenAI-compatible API worked with Hugging Face's speech-to-speech server's chat-completions backend as it was, by changing only the base URL, key and model name.
**Would we build with it again?** Yes. It is why Nemotron answers Andy in under a second.

## NVIDIA Nemotron 3.5 Lightning

**Used for:** Andy's voice conversation with tool calls, in English and Spanish.
**Worked:** correct tool calls in 0.62 to 0.83 s with thinking off; fast enough that a robot feels
immediate.
**Needs work**, each found by our conversation suite (now 97 spoken situations):
- **Tool choice changes with the size of the tool list:** with 17 tools it always called the clock;
  with the robot's real 27 it once invented a time.
- **Persona rules weaken after tool results:** a broad "call tools first" rule led it to agree to speak
  as the user's son.
- **No default crisis line:** without a rule it gave none for "everyone would be better off without me"
  in 2 of 3 runs, and in 3 of 3 in Spanish.
- **Recall over tools for famous texts:** it recited a public-domain story from memory, with misquotes,
  instead of calling the story tool.
- **Register in Spanish:** it used *tú*, and guessed the listener's gender, with an older adult until
  told to use *usted*. Told once, it still slipped back to *tú* in the Spanish crisis reply (2026-10-28) until that
  section gave its own example sentence in *usted*.
- **A tool's own result can restart it:** when a background research answer was handed back as "Tell the person
  you looked into: <the question>", it started the same research again, seven times in five minutes (2026-10-25,
  on the robot), and "stop searching" had nothing to stop. Wording the hand-over as finished ("do not call it
  again") and a guard in code fixed it; a note on tool re-invocation from tool results would help agent builders.
- **Tool calls written as text:** in one of three suite runs (2026-10-28) a letter case's whole reply was
  `<tool_call> <function=read_letter </function>`, a malformed call in the content instead of `tool_calls`. A voice
  pipeline speaks whatever content it gets; we now strip such markup before speech, and make the call it names when
  it fits a tool Andy has (four such replies in the three final Job runs of 2026-10-28). A server-side check that never
  returns tool-call markup as content would protect every voice builder.
- **A memory offer asked for three times in the system prompt was still missed:** "Sofia has her recital on
  Thursday" got "What was the recital like?" in 6 of 12 runs (2026-10-28). A one-line note on that turn, added in
  code when the words show something coming up with its day, brought it to 1 of 15. Recency beat repetition.
- **A tool result's reason gets said aloud:** a result worded as the reason ("the person has already supplied message
  words aloud, not a held-up page") came back in the spoken reply ("Since this is spoken content, not a held-up
  letter…") in 4 of 6 replies on 2026-10-27 and 10-28, and a longer instruction placed after fixed words was read out
  with them once in 27. Results that give the words to say, with a few words of instruction, fixed both in 50 tries.
- **Adversarial pages:** filling a structured card from a scam letter, it put the scam's own demand in
  "to do". The decision had to move into code.

A model card section on tool-list size, register in other languages, and a default crisis line would
help every builder of a voice assistant.
**Onboarding (zero to hello world):** Token Factory's OpenAI-compatible chat completions worked on the first try with tools. The
one surprise: with thinking on, a strict `json_schema` response format was ignored (free-text reasoning
came back instead); with thinking off it returned exactly the schema in 0.73 to 0.97 s.
**Would we build with it again?** Yes: correct tool calls in 0.6 to 0.8 s with thinking off make a spoken robot feel immediate; with those rules in our own prompt and code.

## NVIDIA Nemotron 3 Ultra

**Used for:** the judge of our conversation suite (three runs of all 97 cases per check), and
"think it through" for decisions.
**Worked:** reliable judgments with reasons we could act on; balanced, short answers in 2.1 s.
**Needs work:** as a judge it passed a reply that read out a scam letter's phone number, although the
rule said not to. With a strict `json_schema` (thinking off), it sometimes stops after a field and writes
blank space until `max_tokens` instead of the remaining required field: 17 of 360 answers in our scam
evaluation, the same messages each run (2026-10-14). A guard in the decoder, or a note in the docs, would
help. Evaluation guidance should say to check hard constraints deterministically beside an
LLM judge.
**Onboarding (zero to hello world):** the same key and endpoint as Lightning, only the model name changed, so routing hard turns
to Ultra was one line.
**Would we build with it again?** Yes: it judged 97 spoken situations three times in minutes with reasons we could act on, and answers a hard question in about two seconds.

## NVIDIA Nemotron 3.5 Content Safety

**Used for:** a second look at the person's words beside each reply, with a custom policy for signs of
crisis, on a Nebius Serverless Endpoint.
**Worked:**
- About 0.55 s per check.
- With our policy it caught 7 of 8 held-out phrasings that our word list misses, with no false alarms.
**Needs work:**
- The standard categories caught 5 of 8, and filed "putting my pills aside for when I've had enough"
  under controlled substances. Indirect signs of self-harm deserve a place in the default taxonomy.
- The card pins vLLM at or below 0.20.2.
- The card doesn't say that the custom-policy mode works without reasoning, or how fast it is then (about 0.55 s
  for us); both decide whether a guard can sit beside every spoken turn.
- It isn't on serverless Token Factory, so a guard needs its own GPU.
**Onboarding (zero to hello world):** on our own endpoint with the vLLM version the card names; its plain-text answer ("User
Safety: unsafe", then the categories) needed a small parser, and the custom-policy mode worked without
reasoning.
**Would we build with it again?** Yes. Serverless would make it a default.

## NVIDIA Nemotron 3.5 Super VL (on Token Factory)

**Used for:** Andy's eyes since 2026-10-20: describing what's in front of the camera, family photos, and
finding things (four views at once, as structured output with a JSON schema).
**Worked:** it appeared on serverless Token Factory for our key in October, and moving to it was one setting.
At the desk it described Andy's TV screen in 1.35 s (word for word) and read four views in 2.08 s, all right,
against 3.45 s and 2.28 s for Nano VL on our own L40S endpoint, with nothing to start. The models API lists
its price, region and limits, which made the cost page exact.
**Needs work:**
- It reasons before answering by default: our first call with `max_tokens: 200` came back with empty content
  and 200 reasoning tokens. `chat_template_kwargs: {"enable_thinking": false}` fixes it; a line on the model's
  page would save the next person the surprise.
- One region (us-north1) for now; a European household would want eu-north1.
- **Small things need crops sent at full size.** It reads an image at the size it is sent (16-pixel patches, no
  tiles of its own), so a 768-pixel copy of a room loses a pair of glasses: 0 of 9 at the desk, against 9 of 9 for
  six full-size tiles per frame read at once (1.8 s for 24). A line on the model's page saying so would help every
  robotics builder. A strict yes or no on a close-up confirmed 8 of 9 and wrongly confirmed none of 9 hard
  negatives, a pattern worth showing in an example.
**Onboarding (zero to hello world):** under five minutes: the same key and base URL as the conversation, an
image as a data URL, the first answer in 2.6 s.
**Would we build with it again?** Yes: a bigger model, faster than our own endpoint, always on, and paid per picture.

## NVIDIA Cosmos Reason 2 2B

**Used for:** Andy's offline eyes since 2026-10-25: when Token Factory can't be reached, "what do you see?" and the
finder's questions go to it on the home computer's second GPU, so nothing leaves the house.
**Worked:** vLLM 0.32.0 served it on the first try with no special flags, and a description of Andy's TV screen came
back right in about 0.5 s. In Pollen's MuJoCo scene, on the same 30 searches as Super VL, it pointed 18 of 23 times
(Super VL 21), claimed nothing when the thing wasn't there, and answered faster (2.1 s against 3.2 s).
**Needs work:**
- The model card shows only a Transformers example; a vLLM serving line, as other NVIDIA cards give, would save the
  first hour.
- The card says 24 GB is the minimum, without saying for what: vLLM ran it with about 14 GB reserved. Memory for
  images, and latency per GPU, would let builders plan a Jetson.
- It points less precisely than Super VL (3.06° median error against 0.78°); the card's pointing coordinate format
  isn't stated, so we asked for our own JSON.
- **The 8B model** fills a 24 GB GPU (about 21 GB with a 12,288-token context; 16,384 didn't fit) and, on the same
  searches, pointed 22 of 23 times, never at the wrong place, 1.95° median error, in 4.8 s: for pointing, size
  matters. A note on the card comparing the two sizes on grounding would help builders choose.
**Onboarding (zero to hello world):** about 25 minutes: accept the licence, `uv sync` with vLLM, and the first start
downloads and compiles in about 5 minutes.
**Would we build with it again?** Yes: a small NVIDIA model that keeps a robot's eyes working with the network
down, and the one NVIDIA's Jetson design for the Reachy Mini runs.

## NVIDIA Nemotron Nano 12B v2 VL

**Used for:** Andy's eyes until 2026-10-20 (now the option, `ANDY_VISION=endpoint`), describing what's in front of the camera, on a Nebius Serverless Endpoint.
**Worked:** accurate descriptions in 3.5 s on one L40S.
**Needs work:**
- The card asks for a vLLM nightly image; we pinned v0.30.0.
- Until October there was no NVIDIA vision model on serverless Token Factory, so robotics prototypes needed a
  dedicated endpoint (Nemotron 3.5 Super VL has since arrived; see above).
**Onboarding (zero to hello world):** about 15 minutes to the endpoint's first start (14.3 GB of weights downloaded in 4.7
minutes), then 3.5 s per description.
**Would we build with it again?** Yes: accurate descriptions in 3.5 s, and four views read at once as structured output, which is what lets Andy turn its head toward something; on an endpoint we start only when needed.

## NVIDIA Parakeet TDT 0.6B v3

**Used for:** speech to text, locally, in Hugging Face's speech-to-speech server.
**Worked:** 0.02 to 0.08 s per utterance on the desktop's GPU. Excellent for a home robot.
**Needs work:** no way to say which languages to expect. On the robot (2026-10-28), one turn of the founder's
accented English and one muffled turn came out in Cyrillic, detected as Ukrainian and Russian, and the conversation
model answered in Russian. Andy speaks English and Spanish, so we now treat another alphabet as unclear and ask again.
A list of allowed languages at decode time (we would pass `en,es`) would fix this at the source for every bilingual
assistant. What a home robot also misses is who is speaking: with two people in the room Andy can't tell their words
apart, so it keeps nothing about a person in company. Speaker turns from the same model would be the next thing we'd use.
**Onboarding (zero to hello world):** it worked out of the box in speech-to-speech. The only work was privacy: the server prints
every transcript to the console whatever `--log_transcripts` says, so we filter those prints. A later version added
live transcription ("Live: …", printed as rich Text) that our filter didn't know: heard words reached the journal for ten
days (2026-10-15 to 25). Now our health check reads the log itself. An option that turns every transcript print off
would end this for everyone.
**Would we build with it again?** Yes: 0.02 to 0.08 s per utterance on a home GPU is what makes a spoken robot feel immediate.

## NVIDIA Magpie TTS Multilingual 357M (evaluated, not adopted)

**Used for:** a trial as Andy's voice, so that every model in the speech loop would be NVIDIA's.
**Worked:** good English and Spanish in five voices, about 2.5 times faster than real time on an RTX 3090.
**Needs work:** the NeMo API makes a whole sentence at once, so a voice assistant waits 0.6 to 0.8 s for
its first sound, against 0.10 to 0.33 s from a streaming voice. A streaming interface, or a TensorRT
recipe for short phrases, would make it a drop-in choice for robots.
**Onboarding (zero to hello world):** installing NeMo's main branch, as the card says, also needed `peft`, which the card doesn't
mention.
**Would we build with it again?** Yes, once it streams.

## Nebius AI Cloud (Serverless Endpoints and Jobs)

**Used for:** two endpoints (content safety; Nano VL eyes until 2026-10-20, now the option) and CPU jobs: the
whole conversation suite, the scam evaluation (four jobs), and Andy's search in simulation (MuJoCo with software
rendering, two jobs of 30 trials each).
**Worked:** the job runs our whole suite (97 cases, three runs, a few minutes) and leaves a
scorecard; we stop the endpoints between uses, and stopped they cost nothing for compute. **MysteryBox with endpoints
works well:** we remade the content-safety endpoint with its token in MysteryBox (`--token-secret` for the HTTPS
check, `--env-secret` for vLLM's own key), so the token is on no command line and in no endpoint spec, and both the
HTTPS address and the plain IP:port refused a request without it (2026-10-25).
**Needs work:**
- **An endpoint's plain IP:port reaches the container directly and bypasses the endpoint token.** Mark the
  HTTPS address as the one to use, and say the IP:port isn't covered.
- **New accounts have no CPU quota in eu-north1** (the only L40S region), so our first job failed with
  ResourceExhausted. We moved it to eu-west2. It came back on 2026-10-25: the CLI's default project is still the
  eu-north1 one, so a job started without `--parent-id` went there and failed with "Quota limit exceeded …
  compute.instance.non-gpu.vcpu (limit 0, requested 2)", naming a quota but not the region or a region that has it.
  Saying "this project's region has no CPU quota; eu-west2 does" in that error, or defaulting jobs to a region with
  quota, would save every new account the same detour.
- **The cheapest GPU isn't easy to find:** L40S is offered only in eu-north1, and the endpoints guide's only example
  is an H100. Showing the cheapest GPU per region in the endpoint form would cut a prototype's cost at once.
- **Jobs accept at most 64 KB of injected files.** We ship a compressed bundle, and on 2026-10-20 the suite's
  outgrew it (49.6 KB gzipped is 66 KB in base64); xz brought it to 44 KB. On 2026-10-28 it was refused again ("plaintext must not exceed 65536 bytes"):
  the files are encoded once more inside the limit, so 40 KB of xz sent as base64 text is over it, and sent as bytes it fits. A way to mount a folder or object
  storage into a job would end this.
- **AI Cloud bills separately from Token Factory.** That means a second card and a top-up.
- **A job's whole request may hold 64 KB, and a new account may run two VMs at once.** Our scam evaluation
  needed four parts, two at a time; a third job at once failed with QuotaExceeded. The Jobs guide should
  say both.
- **A job's log cuts lines at 16,384 characters and may return them out of order,** so a long result
  printed on one line comes back broken; we print it in numbered chunks.
**Onboarding (zero to hello world):** the endpoint took about 15 minutes to first start (14 GB of weights). The job worked once
it was in the right region.
**Would we build with it again?** Yes, for evaluation above all.

## Tavily

**Used for:** five ways at runtime: search (news, look-ups, events, scam warnings on consumer-protection
sites), extract (a link family sent), crawl and map (finding the town's events page at setup), and
research, streamed to the TV step by step.
**Worked:**
- Streaming research is excellent for a robot: planning, the queries, the sources and then the answer
  arrive as they happen, so the screen shows progress while the robot waits; `output_schema` gave
  exactly the two spoken sentences we asked for.
- A search limited to consumer-protection sites found the right warning for a grandparent-scam message on
  the first try. Measured on 120 messages (three runs), Tavily's warnings matched by Nemotron 3 Ultra
  caught 58 of 60 scams with no false alarm, against a mean of 55.7 of 60 over three runs for Ultra without the web.
- The usage API lets the robot show credits used on its own status page.
**Needs work:**
- `safe_search` is rejected with the fast and ultra-fast depths (HTTP 400); a product for older adults
  needs safe results at every speed.
- With `include_domains`, `basic` depth found nothing for a classic prize-scam letter where `advanced`
  found four exact warnings; the docs could say when depth matters.
- `language` alone didn't change English results (2026-10-13); `filter_by_language` (August 2026) does
  exactly what a Spanish speaker needs: Spanish local news, three of three, in one call (2026-10-14).
  `include_domains_mode: "prefer"` didn't put the chosen site first.
- Research latency (12 to 57 s for a mini task) isn't documented.
- `map` came back empty for a town site that refuses crawlers; saying so in the response, rather than an
  empty list, would help.
**Onboarding (zero to hello world):** one key and plain HTTPS calls to the REST API (no SDK needed, so the robot adds no dependency); a working search within minutes.
**Would we build with it again?** Yes: one key gives a robot search, extract, crawl, map and research, and the consumer-protection warnings it finds give every scam verdict a source the person can check (checked by Nemotron 3 Ultra, with no false alarms in 60 ordinary messages).

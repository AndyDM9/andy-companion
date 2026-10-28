# Decisions

One file per decision: the context, what was decided, why, and when to revisit it. A changed decision
gets a dated amendment, or a new decision that replaces it. New ones start from [TEMPLATE.md](TEMPLATE.md).

**Start here:** the product's main choices are [0001](0001-voice-stack.md) (the voice stack),
[0002](0002-one-search-provider-tavily.md) (Tavily), [0007](0007-the-scam-check-two-narrow-questions.md) (the scam
check), [0011](0011-the-eyes-on-token-factory.md) to [0013](0013-the-finder-tested-in-simulation.md) (the eyes and the
finder), [0015](0015-cosmos-on-this-computer-as-the-offline-eyes.md) (the offline eyes),
[0018](0018-one-confirmation-for-one-proposed-action.md) (consent) and
[0022](0022-judge-testing-without-sharing-provider-keys.md) (how judges can test it). Most later ones harden
what these built.

| # | Decision | Date | Status |
|---|---|---|---|
| [0001](0001-voice-stack.md) | The voice stack: Parakeet, Nemotron on Token Factory, Qwen3-TTS | 2026-10-13 | accepted |
| [0002](0002-one-search-provider-tavily.md) | Tavily is the only web provider | 2026-10-13 | accepted; amended 2026-10-14; amended by 0004 and 0006 |
| [0003](0003-what-is-public.md) | What goes in this public repository, and what never does | 2026-10-13 | accepted |
| [0004](0004-weather-from-the-national-weather-service.md) | The weather from the National Weather Service | 2026-10-13 | accepted; amends 0002 |
| [0005](0005-the-screen-s-design-andy-glass.md) | The screen's design, "Andy Glass" | 2026-10-13 | accepted; amended 2026-10-14 and 2026-10-20 |
| [0006](0006-on-this-day-from-wikipedia.md) | "On this day" from Wikipedia, checked twice | 2026-10-13 | accepted; amends 0002 |
| [0007](0007-the-scam-check-two-narrow-questions.md) | The scam check: two narrow questions, the web's warnings matched by a strong model | 2026-10-14 | accepted |
| [0008](0008-andy-runs-as-user-services.md) | Andy and its voice server run as user services | 2026-10-14 | accepted |
| [0009](0009-four-private-links-each-with-its-own-token.md) | Four private links, each with its own token | 2026-10-14 | accepted |
| [0010](0010-a-public-read-only-demo-of-the-screens.md) | A public, read-only demo of the screens, as a Hugging Face Space | 2026-10-20 | accepted; Space public since 2026-10-25 |
| [0011](0011-the-eyes-on-token-factory.md) | The eyes on Token Factory: Nemotron 3.5 Super VL, with our own endpoint as an option | 2026-10-20 | accepted; amended by 0012 |
| [0012](0012-the-finder-zooms-in-then-looks-closer.md) | The finder zooms in, then looks closer | 2026-10-20 | accepted; amends 0011; amended by 0016 |
| [0013](0013-the-finder-tested-in-simulation.md) | The finder tested in simulation, as Nebius Serverless Jobs | 2026-10-20 | accepted |
| [0014](0014-cosmos-considered-not-yet.md) | Cosmos Reason 2 considered for the finder, not added before submitting | 2026-10-25 | amended by 0015 |
| [0015](0015-cosmos-on-this-computer-as-the-offline-eyes.md) | NVIDIA Cosmos Reason 2 2B on this computer, as the offline eyes | 2026-10-25 | accepted; amends 0014 |
| [0016](0016-the-finder-turns-its-body-to-look.md) | The finder turns its body to look past the head's reach | 2026-10-25 | accepted; amends 0012 |
| [0017](0017-the-voice-log-is-checked-not-trusted.md) | The voice log is checked, not only filtered | 2026-10-25 | accepted |
| [0018](0018-one-confirmation-for-one-proposed-action.md) | One confirmation authorizes one exact proposed action, once | 2026-10-26 | accepted; amended by 0021 |
| [0019](0019-transient-content-stays-in-the-screen-servers-memory.md) | Cards and research stay in the screen server's memory | 2026-10-26 | accepted |
| [0020](0020-one-settings-reader-for-desktop-and-dashboard.md) | One settings reader for desktop and dashboard | 2026-10-26 | accepted |
| [0021](0021-external-memory-tool-has-a-unique-name.md) | The external memory tool has a unique name | 2026-10-26 | accepted; amends 0018 |
| [0022](0022-judge-testing-without-sharing-provider-keys.md) | Judge testing does not require sharing provider keys | 2026-10-26 | accepted; clarifies 0003 |
| [0023](0023-guided-inference-is-separate-from-the-household.md) | Guided judge inference is separate from the household | 2026-10-26 | accepted; extends 0022 |
| [0024](0024-video-preflight-checks-metadata-not-content.md) | Video preflight checks metadata and keeps content review manual | 2026-10-26 | accepted |
| [0025](0025-discoverable-voice-examples-and-honest-search-progress.md) | Make voice examples discoverable and show actual search progress | 2026-10-26 | accepted |
| [0026](0026-preflight-tests-model-availability-not-catalogue-membership.md) | Preflight tests model availability, not catalogue membership | 2026-10-26 | accepted |
| [0027](0027-start-object-search-before-announcing-it.md) | Start an object search before announcing it | 2026-10-26 | accepted |
| [0028](0028-spoken-message-text-does-not-open-letter-ocr.md) | Supplied spoken-message text does not open letter OCR | 2026-10-26 | accepted; amended 2026-10-27 |
| [0029](0029-recognised-credential-values-do-not-enter-memory.md) | Recognised credential values do not enter memory through tool dispatch | 2026-10-27 | accepted |
| [0030](0030-quoted-content-does-not-grant-permission.md) | Quoted content does not grant permission | 2026-10-27 | accepted |
| [0031](0031-validate-and-preserve-reminder-data.md) | Validate reminder times and preserve unreadable data with visible deletion | 2026-10-27 | accepted |
| [0032](0032-use-only-completed-model-answers.md) | Use only completed, typed non-streaming model answers | 2026-10-27 | accepted |
| [0033](0033-complete-guided-replies-before-sample-actions.md) | Require completed guided replies before sample actions | 2026-10-27 | accepted |
| [0034](0034-check-setup-types-before-changing-settings.md) | Check setup value types before changing settings | 2026-10-27 | accepted |
| [0035](0035-bound-screen-status-polls-to-the-current-connection.md) | Bound screen status polls to the current connection | 2026-10-27 | accepted |
| [0036](0036-keep-private-publishing-metadata-out-of-history.md) | Keep private publishing metadata out of history | 2026-10-27 | accepted |
| [0037](0037-validate-and-preserve-saved-settings.md) | Validate saved settings and preserve unreadable originals with visible deletion | 2026-10-27 | accepted |
| [0038](0038-final-export-checks-the-published-release.md) | Final export checks the exact published tag and app package metadata before emitting fields | 2026-10-27 | accepted |
| [0039](0039-physical-scorecards-use-only-validated-metadata.md) | Physical scorecards validate metadata, distinguish errors and preserve previous files | 2026-10-27 | accepted |
| [0040](0040-unreadable-mode-does-not-wake-andy.md) | Unreadable saved mode pauses automatic wakes until explicit intent restores valid control state | 2026-10-27 | accepted |
| [0041](0041-preflight-requires-current-counts-and-final-text.md) | Preflight requires current audio counts and usable final model text | 2026-10-27 | accepted |
| [0042](0042-outline-only-the-confirmed-screen-copy.md) | Outline only the confirmed screen copy using an optional local mask | 2026-10-28 | accepted |

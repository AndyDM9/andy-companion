# 0017: The voice log is checked, not only filtered

**Date:** 2026-10-25. **Status:** accepted.

## Context

The voice server is Hugging Face's speech-to-speech, upstream code. It logs transcripts only as their length, but
its handlers also print what they hear and say to the console, which the journal keeps. Since 2026-10-13
`voice/serve.py` dropped the prints it knew ("USER:", "ASSISTANT:"). A newer version added live transcription,
printed as rich Text starting "Live:", which the filter didn't know: from 2026-10-15 to 2026-10-25 the person's
words as they were heard reached the journal (2,664 lines, some running over several lines), and syslog's copy of
it. Found while looking into why Andy misunderstood a name.

## Options

1. **Add "Live:" to the filter and carry on:** fixes this print; the next new print would leak the same way.
2. **Pin the speech package and read every update's prints:** safe until someone updates it without reading.
3. **Run the voice server with its output thrown away:** no transcript can reach a log, but neither can an error,
   and the voice server is where most failures show.
4. **Filter, and check the log itself:** keep the filter (with "Live:"), and have the health check read the last
   day of the voice log and fail on any line that is not one of the kinds the server may write.

## Decision

Option 4. `privacy.TRANSCRIPT_PRINTS` drops "ASSISTANT:", "USER:" and "Live:" on every console (tested on the
real upstream handler's own print function). `scripts/doctor.py --live` has a check, **No words in the voice log**:
it reads `journalctl --user -u andy-voice` for the last day and counts lines that don't match the voice server's
logger format or its fixed start and stop notices (`VOICE_LOG_OK`); any such line fails the check, and the fix it
names is to add the new print to the filter and clear the journal. The lines already logged on the founder's
desktop were removed with sudo the same evening (this user's journal files, and the voice and eyes servers' lines
in syslog).

## Why

A filter only knows the prints it was told about; a check of the log catches the ones nobody has seen yet. It
counted 842 suspect lines in the last day before the fix and 0 after, and passes on the ordinary output
(loggers, warnings, start and stop).

## Consequences

- Anything new the voice server prints at start-up, a library warning say, fails the check until it is added to
  `VOICE_LOG_OK`: a false alarm costs a minute, a missed leak costs trust.
- The check reads only line kinds, never shows what a line says, and runs only on the computer it checks.
- The README, the architecture and the Devpost text now say the log is checked, not only that prints are filtered.

## Revisit when

- speech-to-speech gains one option that turns every transcript print off: then run with it and keep the check.

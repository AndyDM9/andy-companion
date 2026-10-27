# 0028: Supplied spoken-message text does not open letter OCR

**Date:** 2026-10-26. **Status:** accepted.

## Context

A real-model audit requested `read_letter` once for an invented message already supplied as a quote.
The evaluation's default OCR stand-in then produced an unrelated bill. Tool descriptions prohibit
that source confusion, but a model can still choose the wrong tool. A separate audit case stopped
at a request to hold a letter steady without invoking the reader.

## Options

1. Rely on descriptions alone and retain the preliminary spoken announcement.
2. Add a separate automatic reading/routing path.
3. Dispatch requested page reading before speech, and reject a narrow spoken-message pattern in
   the existing SDK dispatcher before its camera/OCR routine can run.

## Decision

Choose option 3. As with object search (0027), an actual held-up letter request calls the tool before
speech. The existing per-conversation `Confirmation` state supplies the latest utterance to a source
check, without copying it to any new store or log. For a message/text/email introduction followed by
a colon or opening quote, with no explicit physical-page cue in that introduction, the SDK wrapper
returns a fixed non-camera result. Payload words cannot provide the physical cue. The reply says no
camera was used and redirects suspicious content to the existing message checker.

The evaluation uses this same check before its synthetic OCR result. It retains the model's attempted
tool name and the original judge verdicts; a rejected call is not silently counted as correct routing.
The public guided bill has fixed physical-page wording and simulated effects, and remains separate.

## Why

The actual SDK boundary can prevent this particular mistaken OCR invocation even when the model
ignores its description. Explicitly held/printed pages keep their existing path. The check uses English
and Spanish introductions, and is deliberately narrow: it does not cover every paraphrase or all
camera tools, and is not a general prompt-injection defence. No second controller or motion path.

## Revisit when

Physical page requests are wrongly refused, or another spoken-message form reaches OCR. Expand only
with representative invented regressions; never retain household speech to diagnose the classifier.

## Amended 2026-10-27

Invented negative-page introductions exposed a gap: “without using the camera” and “not holding
any paper” counted as positive physical cues. Negated cues now do not authorise this OCR path; an
explicit camera refusal in the introduction wins over another positive page cue. Unrelated and
quoted-payload negations keep the physical-page path. Nine pure cases and two additional installed
dispatch cases cover the change. The existing narrow scope and limitations still apply.

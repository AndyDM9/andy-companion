# 0022: Judge testing does not require sharing provider keys

**Date:** 2026-10-26. **Status:** accepted; clarifies 0003 for judge access.

## Context

The founder asked whether judges should use the author's LLM API. The public Space is a sample
screen preview and does not call a model. The official rules exempt Physical AI from a hosted-demo
URL, but require free working-project testing access through December 15 and permit hardware requests.
Requiring judges to buy their own inference credits is not our required access path.

## Options

1. **Distribute provider keys:** easy to describe, but exposes account capabilities and spending outside Andy.
2. **Author-funded real robot testing:** use the existing robot and API accounts in a supervised session,
   alongside source, video and the sample preview. Arrange hardware access when organisers request it.
3. **An additional funded browser AI sandbox:** convenient for an independent text/model check, but requires
   separate session data, server-side secrets, access and spending controls, and operational support. It
   demonstrates a subset of Andy and cannot replace the physical evidence.

## Decision

Use option 2 for the current entry. Independent installations still bring their own keys (0003);
judges can test the author's robot without buying credits or receiving provider credentials. Final
testing instructions and hardware arrangements must be confirmed before marking access complete.
Use invented test-household data and consented photographs, keeping personal household information
out of judge access. No new public model endpoint or remote motor control is deployed by this decision.

Option 3 is deferred until the video and core live checks are complete and its funding/access scope
is chosen. Any later service must keep its provider key server-side and provide enough free access
for judges to complete testing through the required period.

## Why

The Physical AI entry needs evidence of sensing, model decisions, movement and task outcomes.
A reliable hardware demonstration and measured real trials address the judging criteria directly.
The existing code already supports the author-funded test; a second product would add work before filming.

## Consequences

Testing instructions now distinguish the public preview, optional self-funded reproduction and
author-funded real-robot testing. The rules-compliance access row stays in progress until final
instructions and arrangements are confirmed. Public secrets or new billed services are not needed.

## Revisit when

- Organisers request another testing method, or the founder chooses to fund a separate browser sandbox.

## Amended 2026-10-26

The founder approved the guided browser playground in decision 0023. It is a separate, author-funded
Space with fixed invented inputs and simulated tool effects; the provider key stays in a server secret.
It supplements the preview and robot-testing path, and does not complete hardware-access arrangements.

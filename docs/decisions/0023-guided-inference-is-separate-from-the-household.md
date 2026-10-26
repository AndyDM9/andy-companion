# 0023: Guided judge inference runs separately from the household

**Date:** 2026-10-26. **Status:** accepted; extends 0022.

## Context

The screen Space shows sample interfaces but cannot exercise a live model. The founder approved the
standout review's recommendations on October 26, including a guided judge playground. This adds
hands-on software access while physical evidence and the final robot-access arrangement remain pending.

## Options

1. Connect visitors to the household: exposes private state and hardware and couples availability to the home.
2. Offer unrestricted public chat: adds free-text processing, broader tool exposure and unpredictable inference costs.
3. Run three predefined invented challenges in a separate Space: narrower testing, clear simulation boundaries,
   isolated short-lived state and bounded model calls.

## Decision

Choose option 3. The separate Docker Space uses the public companion profile with an explicit software-demo
boundary and one of three existing tool schemas per challenge. Nemotron on Nebius selects the tool and
generates replies; camera/OCR, search and family effects are simulated. Only the actual confirmation gate
is executed. For sharing, the interface displays its exact proposal before a fresh Yes/No button choice.
The No path is enforced in code. The gate never permits a different sample note.

The process does not load household settings, import SDK/motor/camera tools or read the household store.
Its deployment archive includes only the required source, assets, public profile and schema definitions.
The provider key is a server secret. Inputs are fixed identifiers; no free text or uploads are accepted.
Sessions are memory-only, isolated, capped at 64 and expire after five idle minutes, including when no
new visitors arrive. The public endpoint allows two concurrent examples, at most two provider calls per
step, a fixed response-token cap and 120 calls per UTC day per process; failed calls count and are not retried.
Restarting resets this operational allowance; provider usage still needs review.

## Why

Judges can try real model behavior without keys or a robot, while the household boundary remains intact.
This does not turn synthetic tool responses into evidence of physical accuracy. The original robot
profile, motors and conversation services are unchanged by the playground.

## Consequences

The original Space remains a read-only screen preview. The playground is supplemental, clearly labelled
and author-funded; the free real-robot access path in 0022 remains separate. Its public allowance is not
represented as unrestricted access to the complete working project. Physical task results, footage and
potential-user sessions still need to be completed and recorded honestly.

## Revisit when

- Judges need additional tasks beyond these guided examples, or usage requires a different funding arrangement.

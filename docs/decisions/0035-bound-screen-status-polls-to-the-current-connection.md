# 0035: Bound screen status polls to the current connection

**Date:** 2026-10-27. **Status:** accepted.

## Context

The main screen refresh already had a single-request guard and five-second abort. The faster status
poll had neither. An injected stalled fetch started 12 requests from 12 poll invocations. A second
fixture reproduced a late response body replacing the disconnected pill with an old speaking state.
These are software fault fixtures, not observed household network incidents.

## Options

1. Keep starting status requests every 400 ms regardless of earlier requests.
2. Add only a timeout, allowing responses to cross a disconnect/reconnect transition.
3. Allow one status request at a time, bound its duration and reject replies from an older connection.

## Decision

Choose option 3. Status polling has its own single-request guard, separate from the main refresh.
With AbortController it aborts after five seconds, including response-body reading, and clears the
timer/guard in `finally`. Failure does not prevent a later poll. While marked offline it sends no
status requests; the existing main refresh detects reconnection.

Every actual offline/online transition increments a browser-local generation. A status request
captures that generation before fetching and checks it after JSON decoding. It cannot update the
pill, looking label, ready hints or last-speaking time across a transition, even after the screen
has already reconnected. The next fresh request supplies the current state.

The main refresh and ten-second offline indication keep their existing behaviour; the clock keeps
running. No server protocol, model, robot control, storage, API key or request rate increase.

## Why

One pending request prevents a stalled connection accumulating polls. Checking after body decoding
closes the late-response window. Separate guards let the main screen recover while a status call
is still pending. Tests execute the page's actual functions with controlled clocks/responses.

## Consequences

Status may wait for the current request or its timeout before retrying. Browsers without
AbortController still cap pending status requests at one, but cannot cancel one that never settles;
a reload may be needed. Generation checks validate connection freshness, not arbitrary payload
semantics or end-to-end robot health. Simulated disconnects do not establish physical Wi-Fi recovery,
voice latency or hardware task success.

## Revisit when

- Supported browsers or the status transport change.
- A measured hardware-network trial exposes another recovery failure.

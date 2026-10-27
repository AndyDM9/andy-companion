# 0026: Preflight tests model availability, not catalogue membership

**Date:** 2026-10-26. **Status:** accepted.

## Context

Post-deployment preflight reported unavailable cloud eyes because the configured Super VL model
was absent from the provider's model catalogue. The same model returned HTTP 200 for both a fixed
text request and an invented blue image, with the expected returned model ID and colour. The old
check would suggest starting a paid endpoint even though the configured service worked.

## Options

1. Treat catalogue membership as a prerequisite, or change providers when it is missing.
2. Ask the configured model to answer a small invented request.

## Decision

Choose option 2. `doctor.py --live` sends eight output tokens at most, with a 15-second timeout,
using the existing configured model/base/key. It checks a nonempty text reply. It sends no camera
picture or household words and returns no provider text, exception message or URL. Missing models,
authorisation failures, transport failures and malformed/empty replies remain failed checks.

## Why

An inference response establishes availability more directly than a directory entry. This text-only
probe does not establish visual understanding, latency on real images, spoken behaviour or pointing.
The separate synthetic-image and camera-local-fallback probes are scoped in the deployment evidence.

## Revisit when

The provider offers an authoritative availability endpoint, or the bounded request is unsupported.

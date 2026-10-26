# 0021: The external memory tool has a unique name

**Date:** 2026-10-26. **Status:** accepted; amends 0018.

## Context

The first real launch after USB reconnection failed before the conversation loop: Pollen's Config
rejects a tool module named `remember` in both its built-in directory and Andy's external directory.
The earlier dispatcher and installation checks did not execute that configuration path.

## Options

1. **Override the SDK collision check:** patch upstream configuration behavior and depend on undocumented precedence.
2. **Give Andy's external tool a unique name:** use the supported loader and update the profile, gate and evaluation.

## Decision

Use `remember_fact`, retaining the same memory store, parameters and per-action consent procedure.
The gate still recognises the legacy built-in name defensively, but the profile exposes only the
custom fact tool. Profile histories, synthetic tool definitions and new scorecard hashes use the new name.
The dashboard also defers importing Pollen's main module until Andy has configured its profile.

## Why

This works with Pollen's supported external-tool loader. A fresh-process SDK test now creates the
actual Config and registry; another checks dashboard import order. CI runs these with the installed
robot environment, without connecting to hardware. The registry is the 38 profile tools plus the SDK's
two task controls; the text suite covers the profile tools.

## Consequences

Andy reached its conversation loop on the connected robot after the change. Existing scorecards
remain historical evidence, including the earlier profile that could not start. New evaluation runs
are separate. Hardware task outcomes and spoken interruption still require observation.

## Revisit when

- Pollen changes its tool-loading or configuration API.

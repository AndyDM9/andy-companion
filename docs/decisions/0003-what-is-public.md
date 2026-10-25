# 0003: What goes in this public repository, and what never does

**Date:** 2026-10-13. **Status:** accepted.

## Context

Andy reuses ideas and general-purpose code from an earlier private assistant on the same robot. That assistant also holds private things, including its owner's own projects and API keys.

## Decision

| In this repository (public) | Never in this repository |
|---|---|
| Code: the voice setup, the profile, tools, body behaviours, the screen, tests | API keys, tokens, `.env` files |
| General-purpose robot behaviours, rewritten here without links to private code | Anything about the owner's other projects or servers |
| Documentation, decisions, measurements | Memories, reminders, conversation text, logs, recordings |
| A sample `.env.example` with empty values | Face identification of any person |

**Andy's memory** is its own small local store on the robot's computer (`~/.local/share/andy-companion/`). It holds only what the person asked Andy to remember, and the reminders they set. It is never a notes vault, never synced, and never in this repository.

**Each user brings their own keys:** Nebius and Tavily ([0002](0002-one-search-provider-tavily.md)).

## Why

The repository is public so judges and anyone else can check every claim against the code. Keys, private projects
and anything a person said would be exposed by the same openness, so they are kept out by rule, not by care.

## How we keep to it

- **Code from the private assistant** is copied module by module, with its private imports removed and personal examples rewritten. It is never copied as a whole folder.
- **Every commit's history** is checked for keys before the repository goes public.
- **Before going public**, names, the founder's town and an endpoint address that had reached older commits are
  rewritten out of the history, every commit's date kept (done 2026-10-25; gitleaks clean after).

## Revisit when

- Andy takes contributions from others: then a contributor guide and a review of what they may add.

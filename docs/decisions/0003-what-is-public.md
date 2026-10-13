# 0003: What goes in this public repository, and what never does

**Date:** 2026-10-13. **Status:** accepted.

## Context

Andy reuses ideas and general-purpose code from an earlier private assistant on the same robot. That assistant also holds private things: its owner's projects and coding tools, other businesses, a personal notes vault used as memory, and API keys.

## Decision

| In this repository (public) | Never in this repository |
|---|---|
| Code: the voice setup, the profile, tools, body behaviours, the screen, tests | API keys, tokens, `.env` files |
| General-purpose robot behaviours, rewritten here without links to private code | Anything about the owner's projects, coding jobs, other businesses or servers |
| Documentation, decisions, measurements | Memories, reminders, conversation text, logs, recordings |
| A sample `.env.example` with empty values | Face identification of any person |

**Andy's memory** is its own small local store on the robot's computer (`~/.local/share/andy-companion/`). It holds only what the person asked Andy to remember, and the reminders they set. It is never a notes vault, never synced, and never in this repository.

**Each user brings their own keys:** Nebius and Tavily ([0002](0002-one-search-provider-tavily.md)).

## How we keep to it

- **Code from the private assistant** is copied module by module, with its private imports removed and personal examples rewritten. It is never copied as a whole folder.
- **Every commit's history** is checked for keys before the repository goes public.

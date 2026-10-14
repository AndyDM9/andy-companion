# 0006: "On this day" comes from Wikipedia, checked twice

**Date:** 2026-10-13. **Status:** accepted. **Amends** [0002](0002-one-search-provider-tavily.md) for
this one feature, as [0004](0004-weather-from-the-national-weather-service.md) did for the weather.

## Context

A companion needs things to talk about. A dated thing from today's date in years gone by ("On this day
in 1969, Apollo 11 landed on the Moon") is a natural opening for a memory of the time. Research on
older adults and social robots (Irfan et al., 2024 and 2025) found that people want conversation with
depth, not small talk, with follow-up questions that invite reflection. ElliQ offers "interesting
facts". A web search for "what happened today" gives mixed, undated pages; Wikipedia keeps a curated,
dated list for every day.

## Decision

- **Source:** Wikipedia's On this day feed (`en.wikipedia.org/api/rest_v1/feed/onthisday/all/MM/DD`).
  It is free and needs no key. Requests send a User-Agent naming the project, as Wikimedia asks.
  `rest_v1` is used because Wikimedia's changelog retires the API portal in June 2026 (research
  2026-10-13).
- **Licence:** Wikipedia's text is CC BY-SA 4.0. Andy says "according to Wikipedia", and the screen
  shows "Wikipedia (CC BY-SA 4.0)". Andy saying it in its own words, or in Spanish, is an adaptation,
  which the licence allows with that credit.
- **Only gentle things, checked twice:**
  - **Code:** years 1900 to 2010; firsts, openings, launches, records, films, songs, books, flights and
    space; words for death, war, violence, disaster, politics, religion and illness ruled out.
  - **Nemotron 3.5 Lightning** reads the shortlist against the same rule (strict schema, reasoning
    off, once a day, about 1 s), because a word list leaks: "Hijacking of Lufthansa Flight 181" passed
    the code on "Flight".
  - If the check can't be made, nothing is offered.
- **How Andy uses it:** Andy picks one, says it with its year, and asks an open question about the time.
  It never asks "Do you remember".
- Tavily stays the only search provider.

## Consequences

- Only the date leaves the computer for Wikipedia; nothing about the person does.
- Spanish speakers hear the English feed's facts in Spanish; the screen card is in English below a
  Spanish date.
- The check is cautious and drops some harmless items (Concorde's first flight, a basketball record).
  We accept that.

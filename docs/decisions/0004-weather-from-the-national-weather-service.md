# 0004: The weather comes from the National Weather Service

**Date:** 2026-10-13. **Status:** accepted. **Amends** [0002](0002-one-search-provider-tavily.md)
for the weather only.

## Context

"What's the weather today? Do I need an umbrella?" is one of the first things anyone asks a home
robot. Asked through Tavily search, the answers came from pages with stale times ("Current weather
2:18 PM"), mixed sources and unclear dates (tested 2026-10-13). Andy never guesses the day; it
should not guess the weather either.

## Decision

- **Forecast and alerts:** the US National Weather Service API (`api.weather.gov`): free, no key,
  public domain, plain-English periods ("Tonight: Mostly clear, with a low around 80"), and the
  official alerts for the point (heat, storms, hurricanes).
- **Where the town is:** Open-Meteo's geocoding API turns the town set on the setup page into
  coordinates once; they are kept in Andy's settings with the town and looked up again only when
  the town changes.
- Only the town's name and its coordinates leave the computer; no key, nothing about the person.
- Tavily stays the only search provider.

## Why

- **Right, and dated:** the forecast names its periods ("Tonight", "Wednesday"), so Andy can say
  which day it means.
- **No new key:** setup stays at two keys.
- **Alerts from the source:** in Florida a hurricane or heat alert matters more than any search.

## Revisit when

- Andy is used outside the United States (the NWS covers the US only): Open-Meteo's forecast is the
  candidate, with its terms checked for the use.

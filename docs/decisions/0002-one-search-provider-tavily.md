# 0002: Tavily is the only web provider

**Date:** 2026-10-13. **Status:** accepted.

## Context

An earlier private assistant on the same robot used several web services, each with its own
key: Brave Search, Firecrawl, Perplexity. This repository is public. Keys are never committed,
and every user supplies their own.

## Decision

Andy uses one web provider, Tavily, for everything those services did:

| Need | Tavily endpoint |
|---|---|
| Search, news (was Brave) | `search`, with `topic: news` and `include_domains` for chosen local sources |
| Read a page or a link (was Firecrawl) | `extract` |
| Many pages of a site, what's on this week | `map` and `crawl` |
| A cited answer to a bigger question (was Perplexity) | `research` |

## In use (2026-10-13)

`search` (news, look-ups, scam checks at advanced depth), `extract` (links), `crawl` (what's on),
and `research`, streamed with `output_schema`, for "look into it for me" (`looking.py`). Every
request carries `X-Project-ID: andy-companion`; `GET /usage` feeds the hood page. The weather comes
from the National Weather Service instead ([0004](0004-weather-from-the-national-weather-service.md)).

## Why

- **Fewer keys:** a user needs two (Nebius and Tavily), so setup stays short.
- **The bonus prize:** the hackathon's Best Use of Tavily rewards a real runtime use.
- **One privacy story:** one provider's terms to read and explain.

## Revisit when

- A user needs something Tavily cannot do.
- Tavily's terms change.

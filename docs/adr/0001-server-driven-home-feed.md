# ADR-0001: Server-driven home feed

Status: accepted, April 2025

## Context

Mobile releases go out roughly every week and wait on app store review. Product wanted to change what the home screen shows without waiting for a release.

## Decision

The backend returns the home screen as an ordered list of typed cards. The apps render the card types they know and skip the rest. The order comes from `HOME_FEED_ORDER` in `nudge/config.py`.

## Consequences

- Card content and order change with a backend deploy, not an app release.
- The order is one global list. Every user sees the same cards in the same order. Per-user ordering was left for later.
- A card builder returns nothing when it has nothing to show, so a user with no linked accounts sees fewer cards.
- `feed_viewed` records how many cards were returned, not which ones.

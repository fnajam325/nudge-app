# ADR-0003: Global push frequency cap

Status: accepted, June 2025

## Context

Support and app store reviews pointed at notification fatigue. Several nudge types fired independently, so an active user could get three pushes in a day.

## Decision

A user gets at most 2 pushes in any rolling 7 days, across all nudge types. When more than one nudge is due, the scheduler works down a fixed priority list and sends at most one per user per run. The list is `NUDGE_PRIORITY` in `nudge/config.py`.

## Consequences

- A user who is eligible for many nudge types hits the cap quickly. Types lower in the list can go unsent for them.
- There are no per-type caps and no per-user preferences beyond the opt-in flag.
- Failed sends do not count toward the cap.

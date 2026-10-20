# ADR-0002: Nightly transaction sync

Status: accepted, March 2025

## Context

The bank aggregator rate-limits per customer and only exposes a transaction the day after it posts. Polling per user on demand would burn through the limit and still not show anything newer.

## Decision

One batch job syncs every linked account at 04:00 UTC. Each run re-reads from the start of the previous sync day. Inserts are idempotent by transaction id, so the overlap is harmless.

## Consequences

- What users see is 24 to 48 hours behind their bank.
- A user who links an account sees data only after the next nightly run.
- `accounts.last_synced_at` lets the app show an as-of time. The balance card marks data stale after 36 hours.
- A failure on one account is recorded and skipped. The rest of the batch continues.

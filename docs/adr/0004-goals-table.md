# ADR-0004: Goals get their own table

Status: accepted, August 2025. Backfill complete. Follow-up open.

## Context

In v1 a goal was a name stored on the savings account (`accounts.goal_name`). Users asked for several goals, and for goals with a target amount and progress. A column on the account could not hold that.

## Decision

Goals move to a `goals` table with a name, a target, the amount saved and a status. Migration 004 creates it and backfills one row per account that had a `goal_name`. The old column stays until the backfill is verified.

## Consequences

- New goals are created through the goals API and never touch `accounts.goal_name`.
- Goals created by the backfill have a target of 0, which the app treats as no target set.
- Follow-up ENG-212: move the remaining readers of `accounts.goal_name` over to `goals`, then drop the column.

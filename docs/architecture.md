# Architecture

## Shape of the system

```
 iOS / Android apps
        |
        v
 mobile gateway (auth, routing)            not in this repo
        |
        v
 nudge/api/handlers.py
   GET  /home    -> feed composer -> card builders -> SQLite
   POST /goals   -> goals
   POST /events  -> analytics tracker, nudge engagement

 Scheduled jobs (nudge/jobs.py)
   04:00 UTC daily    nightly_sync          bank aggregator -> transactions, balances -> categorize
   every hour at :00  hourly_notifications  selector -> frequency cap -> template -> push provider
```

The mobile apps are thin. The home screen is a list of typed cards the backend builds on each request ([ADR-0001](adr/0001-server-driven-home-feed.md)). Pushes are chosen by the backend and delivered through a push provider owned by the platform team.

## Data

SQLite in this repo. Production runs the same schema on Postgres.

| Table | Written by | Notes |
| --- | --- | --- |
| `users` | signup | `timezone` is collected at signup |
| `accounts` | account linking, nightly sync | one row per linked bank account, `type` is checking, savings or credit_card |
| `transactions` | nightly sync | `category` is filled by the rules in `transactions/categorize.py`, NULL when no rule matches |
| `goals` | goals API | one row per savings goal, see [ADR-0004](adr/0004-goals-table.md) |
| `nudges` | notification scheduler | one row per push attempt, with open and action timestamps |
| `events` | analytics tracker | names are validated against `analytics/events.py` |
| `experiment_assignments` | experiment assignment | one row per user per experiment |

## Jobs and timing

| Job | Schedule | Notes |
| --- | --- | --- |
| `nightly_sync` | 04:00 UTC | Pulls balances and transactions per account. One failing account does not stop the rest. |
| `hourly_notifications` | top of every hour | Does nothing except in the send hour, 15:00 UTC. |

## Ownership

| Area | Owner |
| --- | --- |
| `feed/`, `notifications/`, `goals.py` | Engage squad |
| `transactions/` and the aggregator integration | Core Banking |
| `experiments/`, `analytics/`, `migrations/`, push delivery | Platform |

A change that touches more than one area needs a reviewer from each.

## Client contract

The apps call three endpoints through the gateway: `GET /home`, `POST /goals`, `POST /events`. Cards the app does not recognize are skipped, so new card types can ship on the backend before the apps support them.

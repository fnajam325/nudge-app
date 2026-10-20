# Nudge

Nudge is a consumer personal finance app. Users link their bank accounts, see where their money goes, set savings goals, and get nudges to stay on track.

This repository is the Nudge backend: accounts and transactions, the home feed, push notifications, experiments and analytics events. The iOS and Android apps live in separate repositories.

Nudge is a fictional company. This is a teaching codebase for the course Claude Code for Product Managers. It is small on purpose and, like any real codebase, it has rough edges.

## Run it

Python 3.10 or newer. There are no dependencies.

```
python3 -m nudge migrate
python3 -m nudge seed --now 2026-02-02T15:00:00Z
python3 -m nudge feed u0001 --at 2026-02-02T15:00:00Z
python3 -m nudge notify --at 2026-02-02T15:00:00Z --days 28
python3 -m unittest discover -s tests -t .
```

`seed` loads deterministic demo data into `nudge.db`. `notify` simulates one notification run per day, starting at the given time. Pushes are logged, not delivered.

## Layout

| Path | What lives there |
| --- | --- |
| `nudge/users.py`, `accounts.py`, `goals.py` | Users, linked bank accounts, savings goals |
| `nudge/transactions/` | Nightly sync from the bank aggregator, merchant categorization |
| `nudge/feed/` | The home feed: card builders and the composer |
| `nudge/notifications/` | Who gets which push, when, and how often |
| `nudge/experiments/` | Experiment registry and sticky assignment |
| `nudge/analytics/` | The event vocabulary and the tracker |
| `nudge/api/handlers.py` | What the mobile gateway calls |
| `nudge/jobs.py` | The scheduled jobs: nightly sync, hourly notifications |
| `nudge/migrations/` | Forward-only SQL migrations |
| `tests/` | Unit tests, one file per area |

## Docs

- [Architecture](docs/architecture.md): components, data flow, schedules, who owns what
- [Decision records](docs/adr/): why the feed, the sync, the push cap and the goals table look the way they do
- [Known issues](docs/KNOWN_ISSUES.md)

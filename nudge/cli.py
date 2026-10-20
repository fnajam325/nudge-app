"""Local command line: migrate, seed demo data, run a notification pass, print a user's home feed."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import timedelta

from . import config, db
from .api.handlers import get_home
from .jobs import hourly_notifications
from .notifications.sender import LoggingPushProvider
from .seed import seed_demo
from .timeutil import parse, utcnow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nudge")
    parser.add_argument("--db", default=config.DB_PATH, help="SQLite path (default: %(default)s)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="apply database migrations")
    seed = sub.add_parser("seed", help="load deterministic demo data")
    seed.add_argument("--users", type=int, default=120)
    seed.add_argument("--now", help="UTC time, e.g. 2026-02-02T15:00:00Z (default: now)")
    notify = sub.add_parser("notify", help="run one notification pass")
    notify.add_argument("--at", help="UTC time, e.g. 2026-02-02T15:00:00Z (default: now)")
    notify.add_argument("--days", type=int, default=1, help="run once a day for this many days, starting at --at")
    feed = sub.add_parser("feed", help="print a user's home feed")
    feed.add_argument("user_id")
    feed.add_argument("--at", help="UTC time, e.g. 2026-02-02T15:00:00Z (default: now)")
    args = parser.parse_args(argv)

    conn = db.connect(args.db)
    db.migrate(conn)

    if args.cmd == "migrate":
        print("database is up to date")
    elif args.cmd == "seed":
        now = parse(args.now) if args.now else utcnow()
        print(json.dumps(seed_demo(conn, now, args.users), indent=2))
    elif args.cmd == "notify":
        now = parse(args.at) if args.at else utcnow()
        if now.hour != config.NUDGE_SEND_HOUR_UTC:
            print(f"no pushes go out at {now:%H}:00 UTC; the send hour is {config.NUDGE_SEND_HOUR_UTC}:00 UTC")
        push = LoggingPushProvider()
        sent = []
        for day in range(args.days):
            sent += hourly_notifications(conn, push, now + timedelta(days=day))
        counts = Counter(r["nudge_type"] for r in sent)
        print(json.dumps({"sent": len(sent), "by_type": dict(sorted(counts.items()))}, indent=2))
    elif args.cmd == "feed":
        now = parse(args.at) if args.at else utcnow()
        print(json.dumps(get_home(conn, args.user_id, now), indent=2))
    return 0

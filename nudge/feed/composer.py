"""Builds the ordered list of cards for the home screen (docs/adr/0001-server-driven-home-feed.md)."""
from __future__ import annotations

from datetime import datetime

from .. import config
from ..analytics import track
from . import cards

CARD_BUILDERS = {
    "balance": cards.balance_card,
    "recent_transactions": cards.recent_transactions_card,
    "spending_by_category": cards.spending_by_category_card,
    "goals": cards.goals_card,
}


def compose_home_feed(conn, user, now: datetime) -> list[dict]:
    feed = []
    for card_type in config.HOME_FEED_ORDER:  # same order for every user
        card = CARD_BUILDERS[card_type](conn, user, now)
        if card is not None:
            feed.append(card)
    track(conn, user["id"], "feed_viewed", now, {"card_count": len(feed)})
    return feed

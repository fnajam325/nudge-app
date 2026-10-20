"""Push delivery. The real provider client lives in the platform service."""
from __future__ import annotations

from typing import Protocol


class PushError(Exception):
    pass


class PushProvider(Protocol):
    def send(self, user, title: str, body: str, deep_link: str) -> str:
        """Deliver a push. Returns a provider message id. Raises PushError on failure."""


class LoggingPushProvider:
    """Records pushes instead of sending them. Used by the CLI and the tests."""

    def __init__(self) -> None:
        self.sent: list[dict] = []
        self.failing_users: set[str] = set()

    def send(self, user, title: str, body: str, deep_link: str) -> str:
        if user["id"] in self.failing_users:
            raise PushError(f"device token rejected for {user['id']}")
        self.sent.append({"user_id": user["id"], "title": title, "body": body, "deep_link": deep_link})
        return f"msg_{len(self.sent)}"

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def make_context():
    def factory(
        *,
        guild=None,
        author=None,
        channel=None,
    ):
        if author is None:
            author = SimpleNamespace(
                id=100,
                name="TestUser",
                roles=[],
                guild_permissions=SimpleNamespace(
                    manage_messages=True,
                ),
            )

        if channel is None:
            channel = MagicMock()
            channel.id = 200
            channel.__str__ = lambda self: "test-channel"
            channel.permissions_for.return_value = SimpleNamespace(
                manage_channels=True,
                manage_messages=True,
                read_message_history=True,
            )
            channel.purge = AsyncMock(return_value=[])

        ctx = SimpleNamespace(
            guild=guild,
            author=author,
            channel=channel,
            respond=AsyncMock(),
            defer=AsyncMock(),
            followup=SimpleNamespace(
                send=AsyncMock(),
            ),
        )

        return ctx

    return factory

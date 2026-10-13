from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from otc_bot.cogs.general import General


def make_general():
    return General(MagicMock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [
        "hello",
        "Hi there!",
        "HEY everyone",
        "Good morning, bonjour!",
    ],
)
async def test_greeting_adds_wave_reaction(content):
    cog = make_general()
    message = SimpleNamespace(
        author=SimpleNamespace(bot=False),
        content=content,
        add_reaction=AsyncMock(),
        id=123,
        channel=SimpleNamespace(id=456),
    )

    await cog.on_message(message)

    message.add_reaction.assert_awaited_once_with("👋")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [
        "",
        "This is a test.",
        "hiking is fun",
        "history matters",
    ],
)
async def test_non_greeting_does_not_add_reaction(content):
    cog = make_general()
    message = SimpleNamespace(
        author=SimpleNamespace(bot=False),
        content=content,
        add_reaction=AsyncMock(),
        id=123,
        channel=SimpleNamespace(id=456),
    )

    await cog.on_message(message)

    message.add_reaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_bot_message_is_ignored():
    cog = make_general()
    message = SimpleNamespace(
        author=SimpleNamespace(bot=True),
        content="Hello!",
        add_reaction=AsyncMock(),
        id=123,
        channel=SimpleNamespace(id=456),
    )

    await cog.on_message(message)

    message.add_reaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_forbidden_reaction_is_logged(monkeypatch):
    cog = make_general()
    message = SimpleNamespace(
        author=SimpleNamespace(bot=False),
        content="Hello!",
        add_reaction=AsyncMock(
            side_effect=discord.Forbidden(
                response=MagicMock(status=403, reason="Forbidden"),
                message="Forbidden",
            ),
        ),
        id=123,
        channel=SimpleNamespace(id=456, __str__=lambda self: "general"),
    )

    warnings = []
    monkeypatch.setattr(
        "otc_bot.cogs.general.log_warning",
        lambda text, **kwargs: warnings.append(text),
    )

    await cog.on_message(message)

    assert warnings


@pytest.mark.asyncio
async def test_http_error_is_logged(monkeypatch):
    cog = make_general()
    message = SimpleNamespace(
        author=SimpleNamespace(bot=False),
        content="Hello!",
        add_reaction=AsyncMock(
            side_effect=discord.HTTPException(
                response=MagicMock(status=500, reason="Server error"),
                message="Server error",
            ),
        ),
        id=123,
        channel=SimpleNamespace(id=456),
    )

    errors = []
    monkeypatch.setattr(
        "otc_bot.cogs.general.log_exception",
        lambda text, **kwargs: errors.append(text),
    )

    await cog.on_message(message)

    assert errors

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from otc_bot.cogs.mod_only import ModOnly


def make_mod_cog():
    return ModOnly(MagicMock())


def make_member(*, manage_messages=True):
    return SimpleNamespace(
        id=100,
        name="TestUser",
        guild_permissions=SimpleNamespace(
            manage_messages=manage_messages,
        ),
    )


def make_discord_exception(
        exception_type,
        *,
        status,
        reason,
    ):
    response = MagicMock()
    response.status = status
    response.reason = reason

    return exception_type(
        response=response,
        message=reason,
    )


@pytest.mark.asyncio
async def test_purge_rejects_dm(make_context):
    cog = make_mod_cog()
    ctx = make_context(guild=None)

    await ModOnly.purge.callback(cog, ctx, amount=10)

    ctx.respond.assert_awaited_once_with(
        "This command can only be used in a server.",
        ephemeral=True,
    )
    ctx.defer.assert_not_awaited()
    ctx.channel.purge.assert_not_awaited()


@pytest.mark.asyncio
async def test_purge_requires_user_permission(make_context):
    cog = make_mod_cog()
    ctx = make_context(
        guild=MagicMock(),
        author=make_member(manage_messages=False),
    )

    await ModOnly.purge.callback(cog, ctx, amount=10)

    ctx.respond.assert_awaited_once_with(
        "You need the Manage Messages permission.",
        ephemeral=True,
    )
    ctx.channel.purge.assert_not_awaited()


@pytest.mark.asyncio
async def test_purge_requires_bot_permission(make_context):
    cog = make_mod_cog()
    guild = MagicMock()
    guild.me = object()

    ctx = make_context(guild=guild)
    ctx.channel.permissions_for.return_value = SimpleNamespace(
        manage_messages=False,
        read_message_history=True,
    )

    await ModOnly.purge.callback(cog, ctx, amount=10)

    ctx.respond.assert_awaited_once_with(
        "I need the Manage Messages permission.",
        ephemeral=True,
    )
    ctx.channel.purge.assert_not_awaited()


@pytest.mark.asyncio
async def test_purge_requires_message_history(make_context):
    cog = make_mod_cog()
    guild = MagicMock()
    guild.me = object()

    ctx = make_context(guild=guild)
    ctx.channel.permissions_for.return_value = SimpleNamespace(
        manage_messages=True,
        read_message_history=False,
    )

    await ModOnly.purge.callback(cog, ctx, amount=10)

    ctx.respond.assert_awaited_once_with(
        "I need the Read Message History permission.",
        ephemeral=True,
    )
    ctx.channel.purge.assert_not_awaited()


@pytest.mark.asyncio
async def test_purge_rejects_missing_bot_member(make_context):
    cog = make_mod_cog()
    guild = MagicMock()
    guild.me = None

    ctx = make_context(guild=guild)

    await ModOnly.purge.callback(cog, ctx, amount=10)

    ctx.respond.assert_awaited_once_with(
        "Unable to verify the bot's server permissions.",
        ephemeral=True,
    )
    ctx.defer.assert_not_awaited()
    ctx.channel.purge.assert_not_awaited()


@pytest.mark.asyncio
async def test_purge_deletes_requested_amount(make_context):
    cog = make_mod_cog()
    guild = MagicMock()
    guild.name = "Test Server"
    guild.id = 300
    guild.me = object()

    messages = [
        SimpleNamespace(
            id=501,
            content="First test message",
            author=SimpleNamespace(id=601, name="AuthorOne"),
            created_at=datetime.now(timezone.utc),
        ),
        SimpleNamespace(
            id=502,
            content="Second test message",
            author=SimpleNamespace(id=602, name="AuthorTwo"),
            created_at=datetime.now(timezone.utc),
        ),
    ]

    ctx = make_context(
        guild=guild,
        author=make_member(),
    )
    ctx.channel.permissions_for.return_value = SimpleNamespace(
        manage_messages=True,
        read_message_history=True,
    )
    ctx.channel.purge = AsyncMock(return_value=messages)

    await ModOnly.purge.callback(cog, ctx, amount=2)

    ctx.defer.assert_awaited_once_with(ephemeral=True)
    ctx.channel.purge.assert_awaited_once_with(limit=2)

    ctx.followup.send.assert_awaited_once_with(
        "Deleted 2 message(s).",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_purge_handles_forbidden_error(
        make_context,
        monkeypatch,
    ):
    cog = make_mod_cog()
    guild = MagicMock()
    guild.name = "Test Server"
    guild.id = 300
    guild.me = object()

    ctx = make_context(guild=guild)
    ctx.channel.permissions_for.return_value = SimpleNamespace(
        manage_messages=True,
        read_message_history=True,
    )
    ctx.channel.purge.side_effect = make_discord_exception(
        discord.Forbidden,
        status=403,
        reason="Forbidden",
    )

    monkeypatch.setattr(
        "otc_bot.cogs.mod_only.log_notice",
        lambda *args, **kwargs: None,
    )
    warnings = []
    monkeypatch.setattr(
        "otc_bot.cogs.mod_only.log_warning",
        lambda message, **kwargs: warnings.append(message),
    )

    await ModOnly.purge.callback(cog, ctx, amount=10)

    ctx.channel.purge.assert_awaited_once_with(limit=10)
    ctx.followup.send.assert_awaited_once_with(
        "Discord denied permission to delete messages.",
        ephemeral=True,
    )
    assert warnings

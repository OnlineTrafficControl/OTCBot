from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from otc_bot.cogs.general import General


def make_general():
    bot = MagicMock()
    bot.latency = 0.025
    bot.application_commands = []
    return General(bot)


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
async def test_ping_responds_with_latency(make_context):
    cog = make_general()
    ctx = make_context()

    await General.ping.callback(cog, ctx)

    ctx.defer.assert_awaited_once()
    ctx.followup.send.assert_awaited_once()

    kwargs = ctx.followup.send.await_args.kwargs
    embed = kwargs["embed"]

    assert embed.title == "Pong!"
    assert "Gateway latency" in embed.description
    assert "Initial response time" in embed.description


@pytest.mark.asyncio
async def test_help_sends_ephemeral_embed(make_context):
    cog = make_general()
    ctx = make_context()

    await General.help.callback(cog, ctx)

    ctx.respond.assert_awaited_once()

    kwargs = ctx.respond.await_args.kwargs

    assert kwargs["ephemeral"] is True
    assert isinstance(kwargs["embed"], discord.Embed)
    assert kwargs["embed"].title == "OTCBot Commands"


@pytest.mark.asyncio
async def test_help_excludes_hidden_and_non_slash_commands(
        make_context,
        monkeypatch,
    ):
    cog = make_general()
    ctx = make_context()

    class FakeSlashCommand:
        def __init__(self, name, description, hidden=False):
            self.name = name
            self.description = description
            self.hidden = hidden

    visible_command = FakeSlashCommand(
        "ping",
        "Returns latency.",
    )
    hidden_command = FakeSlashCommand(
        "secret",
        "Hidden command.",
        hidden=True,
    )
    non_slash_command = SimpleNamespace(
        name="user-info",
        description="A user command.",
    )

    monkeypatch.setattr(
        "otc_bot.cogs.general.discord.SlashCommand",
        FakeSlashCommand,
    )

    cog.bot.application_commands = [
        visible_command,
        hidden_command,
        non_slash_command,
    ]

    await General.help.callback(cog, ctx)

    embed = ctx.respond.await_args.kwargs["embed"]
    field_names = [field.name for field in embed.fields]

    assert "/ping" in field_names
    assert "/secret" not in field_names
    assert "/user-info" not in field_names
    assert len(field_names) == 1

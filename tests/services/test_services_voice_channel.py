from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from otc_bot.core.constants import Channels
from otc_bot.services import voice_channel as service


def make_status_channel(messages=()):
    channel = MagicMock(spec=discord.TextChannel)
    channel.history.return_value = _async_messages(messages)
    channel.send = AsyncMock(
        return_value=MagicMock(spec=discord.Message),
    )
    return channel


def make_guild(categories=None):
    guild = MagicMock(spec=discord.Guild)
    guild.categories = categories or []
    guild.create_category = AsyncMock()
    return guild


def make_category(name="LFBD"):
    category = MagicMock(spec=discord.CategoryChannel)
    category.name = name
    category.voice_channels = []
    category.channels = []
    category.create_voice_channel = AsyncMock()
    category.delete = AsyncMock()
    return category


def make_voice_channel(name):
    channel = MagicMock(spec=discord.VoiceChannel)
    channel.name = name
    channel.mention = f"<#{name}>"
    channel.delete = AsyncMock()
    return channel


async def _async_messages(messages):
    for message in messages:
        yield message


def make_status_message(
        *,
        message_id=1,
        footer=None,
        author_id=999,
        content="",
):
    message = MagicMock(spec=discord.Message)
    message.id = message_id
    message.author.id = author_id
    message.content = content
    message.embeds = []

    if footer is not None:
        embed = MagicMock()
        embed.footer.text = footer
        message.embeds = [embed]

    message.edit = AsyncMock()
    message.delete = AsyncMock()

    return message


def make_status_guild(
        *,
        categories=None,
        channel=None,
        bot_id=999,
):
    guild = MagicMock(spec=discord.Guild)
    guild.categories = categories or []
    guild.me = SimpleNamespace(id=bot_id)
    guild.get_channel.return_value = channel
    guild.fetch_channel = AsyncMock(return_value=channel)

    return guild


@pytest.mark.asyncio
async def test_refresh_status_creates_message_when_none_exists(
    monkeypatch,
):
    channel = make_status_channel()
    guild = make_status_guild(channel=channel)

    monkeypatch.setattr(
        service,
        "Channels",
        Channels,
    )

    result = await service.refresh_airport_status(guild)

    channel.send.assert_awaited_once()
    assert result is channel.send.return_value
    embed = channel.send.await_args.kwargs["embed"]

    assert embed.title == "Airport Voice Status"
    assert embed.description == "No airports are currently open."
    assert embed.footer.text == service.AIRPORT_STATUS_FOOTER


@pytest.mark.asyncio
async def test_refresh_status_fetches_channel_when_not_cached():
    channel = make_status_channel()
    guild = make_status_guild(channel=channel)
    guild.get_channel.return_value = None

    await service.refresh_airport_status(guild)

    guild.fetch_channel.assert_awaited_once_with(
        Channels.AIRPORT_STATUS.value.id,
    )
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_status_rejects_non_text_channel():
    guild = make_status_guild(channel=MagicMock())

    with pytest.raises(TypeError, match="not a text channel"):
        await service.refresh_airport_status(guild)


@pytest.mark.asyncio
async def test_refresh_status_edits_existing_status_message():
    existing = make_status_message(
        footer=service.AIRPORT_STATUS_FOOTER,
    )
    channel = make_status_channel([existing])
    guild = make_status_guild(channel=channel)

    result = await service.refresh_airport_status(guild)

    assert result is existing
    existing.edit.assert_awaited_once()
    assert existing.edit.await_args.kwargs["content"] is None
    assert existing.edit.await_args.kwargs["embed"].title == (
        "Airport Voice Status"
    )
    channel.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_status_removes_duplicate_status_messages():
    first = make_status_message(
        message_id=1,
        footer=service.AIRPORT_STATUS_FOOTER,
    )
    duplicate = make_status_message(
        message_id=2,
        footer=service.AIRPORT_STATUS_FOOTER,
    )
    channel = make_status_channel([first, duplicate])
    guild = make_status_guild(channel=channel)

    result = await service.refresh_airport_status(guild)

    assert result is first
    first.edit.assert_awaited_once()
    duplicate.delete.assert_awaited_once()
    channel.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_status_removes_legacy_announcement():
    legacy = make_status_message(
        content="**Airport status: LFBD**",
        author_id=999,
    )
    channel = make_status_channel([legacy])
    guild = make_status_guild(channel=channel, bot_id=999)

    await service.refresh_airport_status(guild)

    legacy.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_status_keeps_legacy_message_from_other_author():
    legacy = make_status_message(
        content="**Airport status: LFBD**",
        author_id=123,
    )
    channel = make_status_channel([legacy])
    guild = make_status_guild(channel=channel, bot_id=999)

    await service.refresh_airport_status(guild)

    legacy.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_status_ignores_not_found_when_deleting_duplicate():
    first = make_status_message(
        footer=service.AIRPORT_STATUS_FOOTER,
    )
    duplicate = make_status_message(
        footer=service.AIRPORT_STATUS_FOOTER,
    )
    duplicate.delete.side_effect = discord.NotFound(
        MagicMock(status=404, reason="Not Found"),
        "Message not found",
    )

    channel = make_status_channel([first, duplicate])
    guild = make_status_guild(channel=channel)

    result = await service.refresh_airport_status(guild)

    assert result is first
    duplicate.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_status_lists_airports_and_voice_channels():
    voice_one = make_voice_channel("LFBD - GND")
    voice_two = make_voice_channel("LFBD - TWR")
    voice_one.mention = "<#101>"
    voice_two.mention = "<#102>"

    category = MagicMock(spec=discord.CategoryChannel)
    category.name = service.get_category_name("LFBD")
    category.voice_channels = [voice_two, voice_one]

    channel = make_status_channel()
    guild = make_status_guild(
        categories=[category],
        channel=channel,
    )

    await service.refresh_airport_status(guild)

    embed = channel.send.await_args.kwargs["embed"]

    assert "**LFBD**" in embed.description
    assert "<#101>" in embed.description
    assert "<#102>" in embed.description
    assert embed.description.index("<#101>") < (
        embed.description.index("<#102>")
    )


@pytest.mark.asyncio
async def test_refresh_status_ignores_unmanaged_categories():
    category = MagicMock(spec=discord.CategoryChannel)
    category.name = "General"
    category.voice_channels = []

    channel = make_status_channel()
    guild = make_status_guild(
        categories=[category],
        channel=channel,
    )

    await service.refresh_airport_status(guild)

    embed = channel.send.await_args.kwargs["embed"]

    assert embed.description == "No airports are currently open."


@pytest.mark.asyncio
async def test_refresh_status_handles_empty_airport_category():
    category = MagicMock(spec=discord.CategoryChannel)
    category.name = service.get_category_name("LFBD")
    category.voice_channels = []

    channel = make_status_channel()
    guild = make_status_guild(
        categories=[category],
        channel=channel,
    )

    await service.refresh_airport_status(guild)

    embed = channel.send.await_args.kwargs["embed"]

    assert "**LFBD**" in embed.description
    assert "_No voice channels._" in embed.description


@pytest.mark.asyncio
async def test_close_airport_channels_deletes_no_unmanaged_channels():
    category = make_category()
    unrelated = make_voice_channel("Other channel")
    category.voice_channels = [unrelated]
    category.channels = [unrelated]

    guild = make_guild([category])

    deleted_count, category_deleted = await service.close_airport_channels(
        guild,
        "LFBD",
    )

    assert deleted_count == 0
    assert category_deleted is False
    unrelated.delete.assert_not_awaited()
    category.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_airport_channels_rejects_invalid_code():
    guild = make_guild()

    with pytest.raises(ValueError, match="exactly four letters"):
        await service.close_airport_channels(guild, "BAD")

    assert guild.categories == []

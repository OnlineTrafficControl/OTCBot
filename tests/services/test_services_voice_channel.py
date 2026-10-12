from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from otc_bot.services import voice_channel as service


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
    channel.delete = AsyncMock()
    return channel


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("lfbd", "LFBD"),
        (" LFBD ", "LFBD"),
        ("EGLL", "EGLL"),
    ],
)
def test_normalize_airport_code(value, expected) -> None:
    assert service.normalize_airport_code(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "ABC",
        "ABCDE",
        "AB1D",
        "AB-D",
        "AB D",
        "éBCD",
    ],
)
def test_normalize_airport_code_rejects_invalid_values(value) -> None:
    with pytest.raises(ValueError, match="exactly four letters"):
        service.normalize_airport_code(value)


def test_get_category_name() -> None:
    assert service.get_category_name("lfbd") == "LFBD"


def test_get_voice_channel_name() -> None:
    assert service.get_voice_channel_name("lfbd", "twr") == "LFBD - TWR"


def test_get_managed_positions() -> None:
    positions = service.get_managed_positions()

    assert positions
    assert all(isinstance(position, str) for position in positions)
    assert len(positions) == len(set(positions))


@pytest.mark.asyncio
async def test_get_or_create_category_reuses_existing_category() -> None:
    category = make_category()
    guild = make_guild([category])

    result, created = await service.get_or_create_category(guild, "lfbd")

    assert result is category
    assert created is False
    guild.create_category.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_or_create_category_creates_category() -> None:
    guild = make_guild()
    category = make_category()
    guild.create_category.return_value = category

    result, created = await service.get_or_create_category(guild, "lfbd")

    assert result is category
    assert created is True
    guild.create_category.assert_awaited_once_with(name="LFBD")


@pytest.mark.asyncio
async def test_get_or_create_voice_channel_reuses_existing_channel() -> None:
    category = make_category()
    channel = make_voice_channel("LFBD - TWR")
    category.voice_channels = [channel]

    result, created = await service.get_or_create_voice_channel(
        category,
        "lfbd",
        "twr",
    )

    assert result is channel
    assert created is False
    category.create_voice_channel.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_or_create_voice_channel_creates_channel() -> None:
    category = make_category()
    channel = make_voice_channel("LFBD - TWR")
    category.create_voice_channel.return_value = channel

    result, created = await service.get_or_create_voice_channel(
        category,
        "lfbd",
        "twr",
    )

    assert result is channel
    assert created is True
    category.create_voice_channel.assert_awaited_once_with(
        name="LFBD - TWR",
    )


@pytest.mark.asyncio
async def test_open_airport_channels_creates_all_positions() -> None:
    guild = make_guild()
    category = make_category()
    guild.create_category.return_value = category

    created_channels = []

    async def create_channel(*, name):
        channel = make_voice_channel(name)
        created_channels.append(channel)
        return channel

    category.create_voice_channel.side_effect = create_channel

    channels, category_created = await service.open_airport_channels(
        guild,
        "lfbd",
        "ALL",
    )

    assert category_created is True
    assert len(channels) == len(service.get_managed_positions())
    assert len(created_channels) == len(service.get_managed_positions())


@pytest.mark.asyncio
async def test_open_airport_channels_creates_one_position() -> None:
    guild = make_guild()
    category = make_category()
    guild.create_category.return_value = category

    channel = make_voice_channel("LFBD - TWR")
    category.create_voice_channel.return_value = channel

    channels, category_created = await service.open_airport_channels(
        guild,
        "lfbd",
        "TWR",
    )

    assert channels == [channel]
    assert category_created is True
    category.create_voice_channel.assert_awaited_once_with(
        name="LFBD - TWR",
    )


@pytest.mark.asyncio
async def test_open_airport_channels_reuses_existing_resources() -> None:
    channel = make_voice_channel("LFBD - TWR")
    category = make_category()
    category.voice_channels = [channel]
    guild = make_guild([category])

    channels, category_created = await service.open_airport_channels(
        guild,
        "LFBD",
        "TWR",
    )

    assert channels == [channel]
    assert category_created is False
    guild.create_category.assert_not_awaited()
    category.create_voice_channel.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_airport_channels_rejects_invalid_position() -> None:
    guild = make_guild()
    category = make_category()
    guild.create_category.return_value = category

    with pytest.raises(ValueError, match="Unsupported airport position"):
        await service.open_airport_channels(guild, "LFBD", "INVALID")

    category.create_voice_channel.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_airport_channels_returns_when_category_missing() -> None:
    guild = make_guild()

    deleted_count, category_deleted = await service.close_airport_channels(
        guild,
        "LFBD",
    )

    assert deleted_count == 0
    assert category_deleted is False


@pytest.mark.asyncio
async def test_close_airport_channels_deletes_managed_channels() -> None:
    channel = make_voice_channel("LFBD - TWR")
    unrelated_channel = make_voice_channel("Other channel")

    category = make_category()
    category.voice_channels = [channel, unrelated_channel]
    category.channels = [channel, unrelated_channel]

    guild = make_guild([category])

    deleted_count, category_deleted = await service.close_airport_channels(
        guild,
        "LFBD",
    )

    assert deleted_count == 1
    assert category_deleted is False
    channel.delete.assert_awaited_once()
    unrelated_channel.delete.assert_not_awaited()
    category.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_airport_channels_deletes_empty_category() -> None:
    channel = make_voice_channel("LFBD - TWR")

    category = make_category()
    category.voice_channels = [channel]
    category.channels = []

    guild = make_guild([category])

    deleted_count, category_deleted = await service.close_airport_channels(
        guild,
        "LFBD",
    )

    assert deleted_count == 1
    assert category_deleted is True
    channel.delete.assert_awaited_once()
    category.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_airport_channels_keeps_category_with_other_channels() -> None:
    managed_channel = make_voice_channel("LFBD - TWR")
    other_channel = MagicMock()
    other_channel.name = "Unmanaged text channel"

    category = make_category()
    category.voice_channels = [managed_channel]
    category.channels = [other_channel]

    guild = make_guild([category])

    deleted_count, category_deleted = await service.close_airport_channels(
        guild,
        "LFBD",
    )

    assert deleted_count == 1
    assert category_deleted is False
    managed_channel.delete.assert_awaited_once()
    category.delete.assert_not_awaited()

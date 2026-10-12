##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# cogs.voice_channel #


import re

import discord

from otc_bot.core.constants import (
    AIRPORT_CATEGORY_NAME_FORMAT,
    AIRPORT_VOICE_CHANNEL_NAME_FORMAT,
    ALL_AIRPORT_POSITIONS,
    AirportPositions,
)


AIRPORT_CODE_PATTERN = re.compile(r"[A-Z]{4}\Z")


def normalize_airport_code(airport_code: str) -> str:

    airport_code = airport_code.strip().upper()

    if AIRPORT_CODE_PATTERN.fullmatch(airport_code) is None:
        raise ValueError(
            "Airport codes must contain exactly four letters."
        )

    return airport_code


def get_category_name(airport_code: str) -> str:

    return AIRPORT_CATEGORY_NAME_FORMAT.format(
        airport_code=normalize_airport_code(airport_code),
    )


def get_voice_channel_name(
        airport_code: str,
        position: AirportPositions | str,
    ) -> str:

    return AIRPORT_VOICE_CHANNEL_NAME_FORMAT.format(
        airport_code=normalize_airport_code(airport_code),
        position=str(position).upper(),
    )


def get_managed_positions() -> tuple[str, ...]:

    return tuple(
        position.value
        for position in ALL_AIRPORT_POSITIONS
    )


async def get_or_create_category(
        guild: discord.Guild,
        airport_code: str,
    ) -> tuple[discord.CategoryChannel, bool]:

    category_name = get_category_name(airport_code)

    category = discord.utils.get(
        guild.categories,
        name=category_name,
    )

    if category is not None:
        return category, False

    category = await guild.create_category(
        name=category_name,
    )

    return category, True


async def get_or_create_voice_channel(
        category: discord.CategoryChannel,
        airport_code: str,
        position: AirportPositions | str,
    ) -> tuple[discord.VoiceChannel, bool]:

    channel_name = get_voice_channel_name(
        airport_code,
        position,
    )

    channel = discord.utils.get(
        category.voice_channels,
        name=channel_name,
    )

    if channel is not None:
        return channel, False

    channel = await category.create_voice_channel(
        name=channel_name,
    )

    return channel, True


async def open_airport_channels(
        guild: discord.Guild,
        airport_code: str,
        position: str,
    ) -> tuple[list[discord.VoiceChannel], bool]:

    airport_code = normalize_airport_code(airport_code)
    position = position.strip().upper()

    category, category_created = await get_or_create_category(
        guild,
        airport_code,
    )

    if position == "ALL":
        positions = get_managed_positions()
    else:
        valid_positions = get_managed_positions()

        if position not in valid_positions:
            raise ValueError(
                f"Unsupported airport position: {position}"
            )

        positions = (position,)

    channels: list[discord.VoiceChannel] = []

    for airport_position in positions:
        channel, _ = await get_or_create_voice_channel(
            category,
            airport_code,
            airport_position,
        )

        channels.append(channel)

    return channels, category_created


async def close_airport_channels(
        guild: discord.Guild,
        airport_code: str,
    ) -> tuple[int, bool]:

    airport_code = normalize_airport_code(airport_code)

    category_name = get_category_name(airport_code)

    category = discord.utils.get(
        guild.categories,
        name=category_name,
    )

    if category is None:
        return 0, False

    managed_channel_names = {
        get_voice_channel_name(airport_code, position)
        for position in get_managed_positions()
    }

    channels_to_delete = [
        channel
        for channel in category.voice_channels
        if channel.name in managed_channel_names
    ]

    deleted_count = 0

    for channel in channels_to_delete:
        await channel.delete(
            reason=f"Closing airport channels for {airport_code}",
        )
        deleted_count += 1

    category_deleted = False

    if not category.channels:
        await category.delete(
            reason=f"Closing empty airport category {airport_code}",
        )
        category_deleted = True

    return deleted_count, category_deleted

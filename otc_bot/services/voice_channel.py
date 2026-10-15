##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# services.voice_channel #


import re

import discord

from otc_bot.core.constants import (
    AIRPORT_CATEGORY_NAME_FORMAT,
    AIRPORT_VOICE_CHANNEL_NAME_FORMAT,
    ALL_AIRPORT_POSITIONS,
    AirportPositions,
    Channels,
)


AIRPORT_CODE_PATTERN = re.compile(r"[A-Z]{4}\Z")
AIRPORT_STATUS_FOOTER = "OTCBot Airport Status v1"
AIRPORT_STATUS_DESCRIPTION_LIMIT = 4000


async def refresh_airport_status(
        guild: discord.Guild,
    ) -> discord.Message:

    channel = guild.get_channel(
        Channels.AIRPORT_STATUS.value.id,
    )

    if channel is None:
        channel = await guild.fetch_channel(
            Channels.AIRPORT_STATUS.value.id,
        )

    if not isinstance(channel, discord.TextChannel):
        raise TypeError(
            "The configured airport status channel is not a text channel."
        )

    airport_categories: list[
        tuple[str, discord.CategoryChannel]
    ] = []

    for category in guild.categories:
        try:
            airport_code = normalize_airport_code(category.name)

        except ValueError:
            continue

        if category.name != get_category_name(airport_code):
            continue

        airport_categories.append(
            (airport_code, category),
        )

    airport_categories.sort(
        key=lambda item: item[0],
    )

    description_parts: list[str] = []
    description_length = 0
    omitted_airports = 0

    for index, (airport_code, category) in enumerate(
            airport_categories
        ):

        voice_channels = sorted(
            category.voice_channels,
            key=lambda voice_channel: voice_channel.name,
        )

        lines = [f"**{airport_code}**"]

        if voice_channels:
            lines.extend(
                channel.mention
                for channel in voice_channels
            )
        else:
            lines.append("_No voice channels._")

        block = "\n".join(lines)
        separator = "\n\n" if description_parts else ""
        addition = separator + block

        if (
            description_length + len(addition)
            > AIRPORT_STATUS_DESCRIPTION_LIMIT
        ):
            omitted_airports = (
                len(airport_categories) - index
            )
            break

        description_parts.append(block)
        description_length += len(addition)

    if not description_parts:
        description = "No airports are currently open."

    else:
        description = "\n\n".join(description_parts)

    if omitted_airports:
        description += (
            "\n\n"
            f"*{omitted_airports} additional airport(s) omitted "
            "because of Discord's embed size limit.*"
        )

    embed = discord.Embed(
        title="Airport Voice Status",
        description=description,
        color=discord.Color.blue(),
    )

    embed.set_footer(
        text=AIRPORT_STATUS_FOOTER,
    )

    bot_member = guild.me
    bot_member_id = (
        bot_member.id
        if bot_member is not None
        else None
    )

    status_messages: list[discord.Message] = []
    legacy_messages: list[discord.Message] = []

    async for message in channel.history(limit=None):
        is_status_embed = any(
            message_embed.footer.text == AIRPORT_STATUS_FOOTER
            for message_embed in message.embeds
        )

        is_legacy_announcement = (
            bot_member_id is not None
            and message.author.id == bot_member_id
            and message.content.startswith("**Airport status:")
        )

        if is_status_embed:
            status_messages.append(message)

        elif is_legacy_announcement:
            legacy_messages.append(message)

    if status_messages:
        status_message = status_messages[0]

        await status_message.edit(
            content=None,
            embed=embed,
        )

        duplicates = status_messages[1:]

    else:
        status_message = await channel.send(
            embed=embed,
        )

        duplicates = []

    for message in duplicates + legacy_messages:
        try:
            await message.delete()

        except discord.NotFound:
            continue

    return status_message


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

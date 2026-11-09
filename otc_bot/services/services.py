from typing import Any

import jardiscordengine as JDE

from otc_bot.constants import AIRPORT_POSITIONS, BOT_NAME
from otc_bot.resources import (
    OPEN_AIRPORTS,
    TRACKED_CATEGORIES,
    TRACKED_CHANNELS,
    AirportResources,
)
from otc_bot.services.generic_helpers import (
    airport_category_name,
    airport_channel_name,
    get_positions,
    log_error,
    log_info,
    normalize_icao,
)
from otc_bot.services.guild_helpers import (
    get_airport_resources,
    get_guild_manager,
    remove_tracked_airport,
    remove_tracked_category,
    remove_tracked_channel,
)

async def open_airport(
    jde_bot: JDE.Bots.JDEBot,
    ctx: JDE.Entities.JDEEntityApplicationContext,
    icao: str,
    position: str,
) -> tuple[list[str], list[str]]:
    icao = normalize_icao(icao)
    positions = get_positions(position)

    guild_manager = get_guild_manager(jde_bot, ctx)

    if ctx.guild is None:
        raise ValueError(
            "This command can only be used in a Discord server."
        )

    guild_id = ctx.guild.id
    key = (guild_id, icao)

    resources = OPEN_AIRPORTS.get(key)

    if resources is None:
        resources = AirportResources(
            guild_id=guild_id,
            icao=icao,
        )
        OPEN_AIRPORTS[key] = resources

    if resources.category is None:
        category = await guild_manager.create_category(
            airport_category_name(icao),
            reason=f"{BOT_NAME}: opening airport {icao}",
        )

        resources.category = category
        TRACKED_CATEGORIES.append(category)

        log_info(
            "Airport category created",
            (
                f"Created category '{airport_category_name(icao)}' "
                f"(ID: {category.id})."
            ),
        )

    category = resources.category

    existing_category_channel_names = {
        channel.name
        for channel in category.discord.channels
    }

    created_channels: list[str] = []
    existing_channels: list[str] = []

    for airport_position in positions:
        channel_name = airport_channel_name(
            icao,
            airport_position,
        )

        if channel_name in existing_category_channel_names:
            existing_channels.append(channel_name)
            continue

        channel = await guild_manager.create_voice_channel(
            channel_name,
            category=category,
            reason=f"{BOT_NAME}: opening {icao} {airport_position}",
        )

        resources.channels.append(channel)
        TRACKED_CHANNELS.append(channel)

        created_channels.append(channel_name)
        existing_category_channel_names.add(channel_name)

        log_info(
            "Airport channel created",
            f"Created voice channel '{channel_name}' (ID: {channel.id}).",
        )

    OPEN_AIRPORTS.pop(key)
    OPEN_AIRPORTS[key] = resources

    return created_channels, existing_channels

async def close_airport(
    jde_bot: JDE.Bots.JDEBot,
    ctx: JDE.Entities.JDEEntityApplicationContext,
    icao: str,
) -> list[str]:
    icao = normalize_icao(icao)

    if ctx.guild is None:
        raise ValueError(
            "This command can only be used in a Discord server."
        )

    guild_manager = get_guild_manager(jde_bot, ctx)

    resources = get_airport_resources(
        ctx.guild.id,
        icao,
    )

    if resources is None:
        raise LookupError(
            f"Airport {icao} has no resources tracked by this bot."
        )

    deleted_channels: list[str] = []
    failures: list[str] = []

    for channel in list(resources.channels):
        try:
            await guild_manager.delete_channel(
                channel.id,
                reason=f"{BOT_NAME}: closing airport {icao}",
            )

        except Exception as error:
            failures.append(
                f"Channel '{channel.name}' (ID: {channel.id}): {error}"
            )

            log_error(
                "Airport channel deletion failed",
                (
                    f"Failed to delete channel '{channel.name}' "
                    f"(ID: {channel.id}): {error}"
                ),
            )

            continue

        deleted_channels.append(channel.name)
        remove_tracked_channel(resources, channel)

        log_info(
            "Airport channel deleted",
            f"Deleted tracked channel '{channel.name}' (ID: {channel.id}).",
        )

    if failures:
        raise RuntimeError(
            "Some airport resources could not be deleted:\n"
            + "\n".join(failures)
        )

    category = resources.category

    if category is not None:
        try:
            await guild_manager.delete_category(
                category.id,
                reason=f"{BOT_NAME}: closing airport {icao}",
            )

        except Exception as error:
            log_error(
                "Airport category deletion failed",
                (
                    f"Failed to delete category '{category.name}' "
                    f"(ID: {category.id}): {error}"
                ),
            )

            raise RuntimeError(
                f"Failed to delete the tracked category for {icao}: {error}"
            ) from error

        remove_tracked_category(category)
        resources.category = None

        log_info(
            "Airport category deleted",
            (
                f"Deleted tracked category '{category.name}' "
                f"(ID: {category.id})."
            ),
        )

    remove_tracked_airport(resources)

    return deleted_channels

async def force_close_airport(
    jde_bot: JDE.Bots.JDEBot,
    ctx: JDE.Entities.JDEEntityApplicationContext,
    icao: str,
) -> tuple[list[str], list[str], bool]:
    icao = normalize_icao(icao)

    if ctx.guild is None:
        raise ValueError(
            "This command can only be used in a Discord server."
        )

    guild = ctx.guild
    guild_id = guild.id
    guild_manager = get_guild_manager(jde_bot, ctx)

    resources = get_airport_resources(guild_id, icao)

    category_name = airport_category_name(icao)

    category = next(
        (
            candidate
            for candidate in guild.categories
            if candidate.name == category_name
        ),
        None,
    )

    if category is None and resources is not None:
        category = resources.category

    channels_to_delete: dict[int, Any] = {}

    if category is not None:
        for channel in category.channels:
            channels_to_delete[channel.id] = channel

    if resources is not None:
        for channel in resources.channels:
            channels_to_delete[channel.id] = channel

    if category is None:
        expected_channel_names = {
            airport_channel_name(icao, position)
            for position in AIRPORT_POSITIONS
        }

        for channel in guild.channels:
            if channel.name in expected_channel_names:
                channels_to_delete[channel.id] = channel

    if not channels_to_delete and category is None:
        raise LookupError(
            f"No category or channels were found for airport {icao}."
        )

    deleted_channels: list[str] = []
    failures: list[str] = []

    for channel in channels_to_delete.values():
        try:
            await guild_manager.delete_channel(
                channel.id,
                reason=(
                    f"{BOT_NAME}: force-closing airport {icao}"
                ),
            )

        except Exception as error:
            message = (
                f"Channel '{channel.name}' (ID: {channel.id}): "
                f"{error}"
            )

            failures.append(message)

            log_error(
                "Force-close channel deletion failed",
                message,
            )
            continue

        deleted_channels.append(channel.name)

        for tracked_resources in list(OPEN_AIRPORTS.values()):
            for tracked_channel in list(tracked_resources.channels):
                if tracked_channel.id == channel.id:
                    remove_tracked_channel(
                        tracked_resources,
                        tracked_channel,
                    )

        log_info(
            "Force-close channel deleted",
            (
                f"Deleted channel '{channel.name}' "
                f"(ID: {channel.id}) for airport {icao}."
            ),
        )

    category_deleted = False

    if category is not None and not failures:
        try:
            await guild_manager.delete_category(
                category.id,
                reason=(
                    f"{BOT_NAME}: force-closing airport {icao}"
                ),
            )

        except Exception as error:
            message = (
                f"Category '{category.name}' (ID: {category.id}): "
                f"{error}"
            )

            failures.append(message)

            log_error(
                "Force-close category deletion failed",
                message,
            )

        else:
            category_deleted = True

            for tracked_category in list(TRACKED_CATEGORIES):
                if tracked_category.id == category.id:
                    remove_tracked_category(tracked_category)

            for tracked_resources in list(OPEN_AIRPORTS.values()):
                tracked_category = tracked_resources.category

                if (
                    tracked_category is not None
                    and tracked_category.id == category.id
                ):
                    tracked_resources.category = None

            log_info(
                "Force-close category deleted",
                (
                    f"Deleted category '{category.name}' "
                    f"(ID: {category.id}) for airport {icao}."
                ),
            )

    for tracked_resources in list(OPEN_AIRPORTS.values()):
        remove_tracked_airport(tracked_resources)

    return deleted_channels, failures, category_deleted

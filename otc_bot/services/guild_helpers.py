
import re
from typing import Any

import jardiscordengine as JDE

from otc_bot.constants import AIRPORT_CATEGORY_SUFFIX, AIRPORT_CHANNEL_PATTERN
from otc_bot.resources import (
    OPEN_AIRPORTS,
    TRACKED_CATEGORIES,
    TRACKED_CHANNELS,
    AirportResources,
)
from otc_bot.services.generic_helpers import log_info, log_warning, normalize_icao


def load_existing_airport_resources(
    jde_bot: JDE.Bots.JDEBot,
) -> None:
    if not jde_bot.synchronized:
        raise RuntimeError(
            "Cannot discover airport resources before "
            "Discord entity synchronization completes."
        )

    discovered_airports: set[tuple[int, str]] = set()
    discovered_categories = 0
    discovered_channels = 0

    for category in jde_bot.categories.values():
        category_name = category.name

        if not category_name.endswith(AIRPORT_CATEGORY_SUFFIX):
            continue

        candidate = category_name[:-len(AIRPORT_CATEGORY_SUFFIX)]

        try:
            icao = normalize_icao(candidate)
        except ValueError:
            continue

        guild_id = category.discord.guild.id
        key = (guild_id, icao)

        resources = OPEN_AIRPORTS.get(key)

        if resources is None:
            resources = AirportResources(
                guild_id=guild_id,
                icao=icao,
            )
            OPEN_AIRPORTS[key] = resources

        if resources.category is not None:
            if resources.category.id != category.id:
                log_warning(
                    "Duplicate airport category",
                    (
                        f"Multiple categories found for airport {icao} "
                        f"in guild {guild_id}. Ignoring category "
                        f"'{category.name}' (ID: {category.id})."
                    ),
                )
                continue

        else:
            resources.category = category

            if not any(
                tracked.id == category.id
                for tracked in TRACKED_CATEGORIES
            ):
                TRACKED_CATEGORIES.append(category)

            discovered_categories += 1

        discovered_airports.add(key)

        log_info(
            "Airport category discovered",
            (
                f"Found existing airport category '{category.name}' "
                f"(ID: {category.id}) for airport {icao}."
            ),
        )

    for channel in jde_bot.channels.values():
        match = AIRPORT_CHANNEL_PATTERN.fullmatch(channel.name)

        if match is None:
            continue

        try:
            icao = normalize_icao(match.group(1))
        except ValueError:
            continue

        guild_id = channel.discord.guild.id
        key = (guild_id, icao)

        resources = OPEN_AIRPORTS.get(key)

        if resources is None:
            resources = AirportResources(
                guild_id=guild_id,
                icao=icao,
            )
            OPEN_AIRPORTS[key] = resources

        # Avoid tracking the same channel more than once.
        if any(
            tracked.id == channel.id
            for tracked in resources.channels
        ):
            continue

        resources.channels.append(channel)

        if not any(
            tracked.id == channel.id
            for tracked in TRACKED_CHANNELS
        ):
            TRACKED_CHANNELS.append(channel)

        discovered_channels += 1
        discovered_airports.add(key)

        log_info(
            "Airport channel discovered",
            (
                f"Found existing airport channel '{channel.name}' "
                f"(ID: {channel.id}) for airport {icao}."
            ),
        )

    log_info(
        "Airport resource discovery",
        (
            f"Discovery completed. Found "
            f"{len(discovered_airports)} airport(s), "
            f"{discovered_categories} categor(ies) and "
            f"{discovered_channels} channel(s)."
        ),
    )

def get_guild_manager(
    jde_bot: JDE.Bots.JDEBot,
    ctx: JDE.Entities.JDEEntityApplicationContext,
):
    if ctx.guild is None:
        raise ValueError(
            "This command can only be used in a Discord server."
        )

    guild = jde_bot.guilds.get(ctx.guild.id)

    if guild is None:
        raise RuntimeError(
            "The server has not been synchronized by JarDiscordEngine."
        )

    return jde_bot.guild(guild)

def get_airport_resources(
    guild_id: int,
    icao: str,
) -> AirportResources | None:
    return OPEN_AIRPORTS.get((guild_id, icao))

def get_guild_airport_codes(
    ctx: JDE.Entities.JDEEntityApplicationContext,
) -> set[str]:
    if ctx.guild is None:
        raise ValueError(
            "This command can only be used in a Discord server."
        )

    guild = ctx.guild
    airport_codes: set[str] = set()

    for category in guild.categories:
        if not category.name.endswith(AIRPORT_CATEGORY_SUFFIX):
            continue

        candidate = category.name[:-len(AIRPORT_CATEGORY_SUFFIX)]

        try:
            icao = normalize_icao(candidate)
        except ValueError:
            continue

        airport_codes.add(icao)

    channel_pattern = re.compile(
        r"^([A-Z0-9]{4})-(GND|TWR|DEP|APP|CTR)$",
        re.IGNORECASE,
    )

    for channel in guild.channels:
        match = channel_pattern.fullmatch(channel.name)

        if match is None:
            continue

        try:
            icao = normalize_icao(match.group(1))
        except ValueError:
            continue

        airport_codes.add(icao)

    for guild_id, icao in OPEN_AIRPORTS:
        if guild_id == guild.id:
            airport_codes.add(icao)

    return airport_codes

def remove_tracked_channel(
    resources: AirportResources,
    channel: Any,
) -> None:
    if channel in resources.channels:
        resources.channels.remove(channel)

    if channel in TRACKED_CHANNELS:
        TRACKED_CHANNELS.remove(channel)

def remove_tracked_category(
    category: Any,
) -> None:
    if category in TRACKED_CATEGORIES:
        TRACKED_CATEGORIES.remove(category)

def remove_tracked_airport(
    resources: AirportResources,
) -> None:
    key = (resources.guild_id, resources.icao)

    if not resources.channels and resources.category is None:
        OPEN_AIRPORTS.pop(key, None)

import jardiscordengine as JDE

from otc_bot.constants import ALL_POSITION
from otc_bot.services.generic_helpers import log_error, normalize_icao
from otc_bot.services.guild_helpers import get_guild_airport_codes
from otc_bot.services.services import close_airport, force_close_airport, open_airport


@JDE.Commands.command(
    name="open",
    description="Open an airport and create its ATC voice channels.",
)
@JDE.Commands.option(
    name="airport",
    description="The four-character airport ICAO code.",
    option_type=str,
    required=True,
)
@JDE.Commands.option(
    name="position",
    description="The ATC position to open, or ALL.",
    option_type=str,
    required=True,
    choices=[
        "GND",
        "TWR",
        "DEP",
        "APP",
        "CTR",
        "ALL",
    ],
)
@JDE.Commands.guild_only()
@JDE.Commands.bot_has_permissions(manage_channels=True)
async def command_open(
    jde_bot: JDE.Bots.JDEBot,
    ctx: JDE.Entities.JDEEntityApplicationContext,
    airport: str,
    position: str,
) -> None:
    await ctx.defer(ephemeral=True)

    try:
        icao = normalize_icao(airport)

        created_channels, existing_channels = await open_airport(
            jde_bot,
            ctx,
            icao,
            position,
        )

    except ValueError as error:
        await ctx.followup.send(
            f"Invalid argument: {error}",
            ephemeral=True,
        )
        return

    except Exception as error:
        log_error(
            "Airport opening failed",
            f"Failed to open airport '{airport}': {error}",
        )

        await ctx.followup.send(
            "An error occurred while opening the airport. "
            "Check the bot logs for details.",
            ephemeral=True,
        )
        return

    response_lines = [
        f"**Airport {icao}**",
        "",
    ]

    if created_channels:
        response_lines.append(
            "**Created channels:**\n"
            + "\n".join(
                f"- `{channel}`"
                for channel in created_channels
            )
        )

    if existing_channels:
        response_lines.append(
            "**Already existing channels:**\n"
            + "\n".join(
                f"- `{channel}`"
                for channel in existing_channels
            )
        )

    if not created_channels and not existing_channels:
        response_lines.append(
            "No channels needed to be created."
        )

    await ctx.followup.send(
        "\n".join(response_lines),
        ephemeral=True,
    )

@JDE.Commands.command(
    name="close",
    description="Close an airport and delete its ATC voice channels.",
)
@JDE.Commands.option(
    name="airport",
    description="The four-character ICAO code of the airport to close.",
    option_type=str,
    required=True,
)
@JDE.Commands.guild_only()
@JDE.Commands.bot_has_permissions(manage_channels=True)
async def command_close(
    jde_bot: JDE.Bots.JDEBot,
    ctx: JDE.Entities.JDEEntityApplicationContext,
    airport: str,
) -> None:
    await ctx.defer(ephemeral=True)

    try:
        icao = normalize_icao(airport)

        deleted_channels = await close_airport(
            jde_bot,
            ctx,
            icao,
        )

    except ValueError as error:
        await ctx.followup.send(
            f"Invalid argument: {error}",
            ephemeral=True,
        )
        return

    except LookupError as error:
        await ctx.followup.send(
            str(error),
            ephemeral=True,
        )
        return

    except Exception as error:
        log_error(
            "Airport closing failed",
            f"Failed to close airport '{airport}': {error}",
        )

        await ctx.followup.send(
            "An error occurred while closing the airport. "
            "Check the bot logs for details.",
            ephemeral=True,
        )
        return

    if deleted_channels:
        deleted_channel_list = "\n".join(
            f"- `{channel}`"
            for channel in deleted_channels
        )

        response = (
            f"**Airport {icao} closed successfully.**\n\n"
            f"Deleted channels:\n{deleted_channel_list}"
        )

    else:
        response = (
            f"**Airport {icao} closed successfully.**\n"
            "No tracked voice channels needed to be deleted."
        )

    await ctx.followup.send(
        response,
        ephemeral=True,
    )

@JDE.Commands.command(
    name="force-close",
    description="Force-close an airport or all airports in this server.",
)
@JDE.Commands.option(
    name="airport",
    description="The airport ICAO code to close, or ALL.",
    option_type=str,
    required=True,
)
@JDE.Commands.guild_only()
@JDE.Commands.has_permissions(manage_channels=True)
@JDE.Commands.bot_has_permissions(manage_channels=True)
async def command_force_close(
    jde_bot: JDE.Bots.JDEBot,
    ctx: JDE.Entities.JDEEntityApplicationContext,
    airport: str,
) -> None:
    await ctx.defer(ephemeral=True)

    try:
        requested_airport = airport.strip().upper()

        if requested_airport == ALL_POSITION:
            airport_codes = get_guild_airport_codes(ctx)

            if not airport_codes:
                await ctx.followup.send(
                    "No airports were found in this server.",
                    ephemeral=True,
                )
                return

            response_lines = [
                "**Force-close all airports**",
                "",
                f"Found {len(airport_codes)} airport(s).",
            ]

            successful_airports = 0
            failed_airports = 0

            for icao in sorted(airport_codes):
                try:
                    (
                        deleted_channels,
                        failures,
                        category_deleted,
                    ) = await force_close_airport(
                        jde_bot,
                        ctx,
                        icao,
                    )

                except Exception as error:
                    failed_airports += 1

                    log_error(
                        "Airport force-close failed",
                        f"Failed to force-close airport {icao}: {error}",
                    )

                    response_lines.append(
                        f"\n**{icao}: Failed**\n"
                        f"- {error}"
                    )
                    continue

                if failures:
                    failed_airports += 1

                    response_lines.append(
                        f"\n**{icao}: Partially closed**"
                    )

                    if deleted_channels:
                        response_lines.append(
                            f"- Deleted {len(deleted_channels)} channel(s)."
                        )

                    if category_deleted:
                        response_lines.append(
                            "- Deleted the airport category."
                        )

                    response_lines.extend(
                        f"- Error: {failure}"
                        for failure in failures
                    )

                    continue

                successful_airports += 1

                response_lines.append(
                    f"\n**{icao}: Closed successfully**"
                )

                if deleted_channels:
                    response_lines.append(
                        f"- Deleted {len(deleted_channels)} channel(s)."
                    )

                if category_deleted:
                    response_lines.append(
                        "- Deleted the airport category."
                    )

                if not deleted_channels and not category_deleted:
                    response_lines.append(
                        "- No resources needed to be deleted."
                    )

            response_lines.extend(
                [
                    "",
                    "**Summary**",
                    f"- Successfully closed: {successful_airports}",
                    f"- Failed or partially closed: {failed_airports}",
                ]
            )

            await ctx.followup.send(
                "\n".join(response_lines),
                ephemeral=True,
            )
            return

        icao = normalize_icao(requested_airport)

        (
            deleted_channels,
            failures,
            category_deleted,
        ) = await force_close_airport(
            jde_bot,
            ctx,
            icao,
        )

    except ValueError as error:
        await ctx.followup.send(
            f"Invalid argument: {error}",
            ephemeral=True,
        )
        return

    except LookupError as error:
        await ctx.followup.send(
            str(error),
            ephemeral=True,
        )
        return

    except Exception as error:
        log_error(
            "Airport force-close failed",
            f"Failed to force-close airport '{airport}': {error}",
        )

        await ctx.followup.send(
            "An error occurred while force-closing the airport. "
            "Check the bot logs for details.",
            ephemeral=True,
        )
        return

    response_lines = [
        f"**Force-close results for airport {icao}**",
        "",
    ]

    if deleted_channels:
        response_lines.append(
            "**Deleted channels:**\n"
            + "\n".join(
                f"- `{channel}`"
                for channel in deleted_channels
            )
        )
    else:
        response_lines.append("No channels needed to be deleted.")

    if category_deleted:
        response_lines.append(
            "\nThe airport category was deleted successfully."
        )
    elif failures:
        response_lines.append(
            "\nThe airport category was not deleted."
        )
    else:
        response_lines.append(
            "\nNo airport category was found to delete."
        )

    if failures:
        response_lines.extend(
            [
                "",
                "**Errors:**",
                *(
                    f"- {failure}"
                    for failure in failures
                ),
                "",
                "Some resources may still exist. Check the bot logs for details.",
            ]
        )
    elif category_deleted or deleted_channels:
        response_lines.append(
            "\nThe force-close operation completed successfully."
        )

    await ctx.followup.send(
        "\n".join(response_lines),
        ephemeral=True,
    )

def register_commands(bot: JDE.Bots.JDEBot):
    bot.command_manager.register_commands(
        command_open,
        command_close,
        command_force_close,
    )

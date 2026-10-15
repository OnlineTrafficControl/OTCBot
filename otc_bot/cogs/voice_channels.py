##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# cogs.voice_channels #


import discord
from discord.ext import commands

from otc_bot.core.constants import (
    SERVER_IDS,
    ALL_AIRPORT_POSITIONS,
    ModRoles,
)
from otc_bot.core.logging import (
    log_exception,
    log_info,
    log_warning,
)
from otc_bot.services.voice_channel import (
    close_airport_channels,
    normalize_airport_code,
    open_airport_channels,
    refresh_airport_status,
)

AIRPORT_POSITIONS = ["ALL"] + list(ALL_AIRPORT_POSITIONS)



class VoiceChannels(commands.Cog):


    def __init__(self, bot: discord.Bot) -> None:

        self.bot = bot


    @discord.slash_command(
        description="Open voice channels for an airport and position.",
        guild_ids=list(SERVER_IDS),
    )
    async def open(
            self,
            ctx: discord.ApplicationContext,
            airport_code: discord.Option(
                str,
                description="The four-letter ICAO airport code.",
            ),
            position: discord.Option(
                str,
                description="The position to open.",
                choices=AIRPORT_POSITIONS,
            ),
        ) -> None:

        guild = ctx.guild

        if guild is None:
            await ctx.respond(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        if guild.me is None or not (
                ctx.channel.permissions_for(guild.me).manage_channels
        ):
            await ctx.respond(
                "I need the Manage Channels permission.",
                ephemeral=True,
            )
            return

        try:
            airport_code = normalize_airport_code(airport_code)

        except ValueError as error:
            await ctx.respond(
                str(error),
                ephemeral=True,
            )
            return

        position = position.strip().upper()

        await ctx.defer(ephemeral=True)

        try:
            channels, category_created = await open_airport_channels(
                guild,
                airport_code,
                position,
            )

            log_info(
                f"{ctx.author} (ID: {ctx.author.id}) opened "
                f"{position} channel(s) for {airport_code} "
                f"in {guild.name} (ID: {guild.id}). "
                f"Channels returned: {len(channels)}.",
                scope="VoiceChannels",
            )

            channel_list = "\n".join(
                channel.mention
                for channel in channels
            )

            category_message = (
                "Created the airport category."
                if category_created
                else "Reused the existing airport category."
            )

            status_updated = await self.update_status(guild)

            status_message = (
                ""
                if status_updated
                else "\nWarning: The airport status embed could not be updated."
            )

            await ctx.followup.send(
                f"{category_message}\n"
                f"Airport: **{airport_code}**\n"
                f"Channels:\n{channel_list}"
                f"{status_message}",
                ephemeral=True,
            )


        except discord.Forbidden:
            log_warning(
                f"Discord denied channel creation for "
                f"{airport_code}, requested by {ctx.author} "
                f"(ID: {ctx.author.id}).",
                scope="VoiceChannels",
            )

            await ctx.followup.send(
                "Discord denied permission to create the channels.",
                ephemeral=True,
            )

        except discord.HTTPException:
            log_exception(
                f"Failed to open channels for {airport_code}, "
                f"requested by {ctx.author} (ID: {ctx.author.id}).",
                scope="VoiceChannels",
            )

            await ctx.followup.send(
                "An error occurred while opening the airport channels.",
                ephemeral=True,
            )

    @discord.slash_command(
        description="Close an airport if all its voice channels are empty.",
        guild_ids=list(SERVER_IDS),
    )
    async def close(
            self,
            ctx: discord.ApplicationContext,
            airport_code: discord.Option(
                str,
                description="The four-letter ICAO airport code.",
            ),
            force: discord.Option(
                bool,
                description="Force closure even if users are connected.",
                default=False,
            ),
        ) -> None:

        guild = ctx.guild

        if guild is None:
            await ctx.respond(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        if guild.me is None or not (
                ctx.channel.permissions_for(guild.me).manage_channels
        ):
            await ctx.respond(
                "I need the Manage Channels permission.",
                ephemeral=True,
            )
            return

        try:
            airport_code = normalize_airport_code(airport_code)

        except ValueError as error:
            await ctx.respond(
                str(error),
                ephemeral=True,
            )
            return

        await ctx.defer(ephemeral=True)

        category = discord.utils.get(
            guild.categories,
            name=airport_code,
        )

        if category is None:
            await ctx.followup.send(
                f"No airport category was found for **{airport_code}**.",
                ephemeral=True,
            )
            return

        occupied_channels = [
            channel
            for channel in category.voice_channels
            if channel.members
        ]

        if occupied_channels and not force:
            channel_list = "\n".join(
                f"{channel.mention}: {len(channel.members)} member(s)"
                for channel in occupied_channels
            )

            await ctx.followup.send(
                f"Cannot close **{airport_code}** because "
                f"some voice channels are occupied:\n"
                f"{channel_list}\n\n"
                "Everyone must leave before these channels can be closed.",
                ephemeral=True,
            )
            return

        if force and not self.is_moderator(ctx.author):
            await ctx.followup.send(
                "You need a moderator role to force-close an airport.",
                ephemeral=True,
            )
            log_warning(
                f"{ctx.author} (ID: {ctx.author.id}) attempted to "
                f"force-close airport {airport_code} without a "
                f"moderator role.",
                scope="VoiceChannels",
            )
            return

        try:
            deleted_count, category_deleted = (
                await close_airport_channels(
                    guild,
                    airport_code,
                )
            )

            if deleted_count == 0 and not category_deleted:
                await ctx.followup.send(
                    f"No managed channels were found for "
                    f"**{airport_code}**.",
                    ephemeral=True,
                )
                return

            log_info(
                f"{ctx.author} (ID: {ctx.author.id}) closed "
                f"airport {airport_code} in {guild.name} "
                f"(ID: {guild.id}). Deleted {deleted_count} "
                f"voice channel(s).",
                scope="VoiceChannels",
            )

            status_updated = await self.update_status(guild)

            status_message = (
                ""
                if status_updated
                else "\nWarning: The airport status embed could not be updated."
            )

            await ctx.followup.send(
                f"Closed **{deleted_count}** voice channel(s) "
                f"for **{airport_code}**.\n"
                + (
                    "The airport category was deleted."
                    if category_deleted
                    else "The category was preserved because it still contains channels."
                )
                + status_message,
                ephemeral=True,
            )


        except discord.Forbidden:
            log_warning(
                f"Discord denied deletion of airport {airport_code}, "
                f"requested by {ctx.author} (ID: {ctx.author.id}).",
                scope="VoiceChannels",
            )

            await ctx.followup.send(
                "Discord denied permission to delete the channels.",
                ephemeral=True,
            )

        except discord.HTTPException:
            log_exception(
                f"Failed to close airport {airport_code}, "
                f"requested by {ctx.author} (ID: {ctx.author.id}).",
                scope="VoiceChannels",
            )

            await ctx.followup.send(
                "An error occurred while closing the airport channels.",
                ephemeral=True,
            )


    def is_moderator(self, member: discord.Member) -> bool:

        moderator_role_ids = {
            role.value.id
            for role in ModRoles
        }

        return any(
            role.id in moderator_role_ids
            for role in member.roles
        )


    async def update_status(
            self,
            guild: discord.Guild,
        ) -> bool:

        try:
            await refresh_airport_status(guild)
            return True

        except Exception:
            log_exception(
                f"Failed to refresh the airport status embed "
                f"in {guild.name} (ID: {guild.id}).",
                scope="VoiceChannels",
            )
            return False


def setup(bot: discord.Bot) -> None:

    bot.add_cog(VoiceChannels(bot))

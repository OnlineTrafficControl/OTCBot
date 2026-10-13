
##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# cogs.mod_only #


import discord
from discord.ext import commands

from otc_bot.core.constants import (
    SERVER_IDS,
    EngineerRoles,
    Channels, ANNOUNCEMENTS,
)
from otc_bot.core.logging import (
    log_exception,
    log_notice,
    log_warning,
)


class EngineerOnly(commands.Cog):


    def __init__(self, bot: discord.Bot) -> None:

        self.bot = bot


    async def _send_announcement(
            self,
            ctx: discord.ApplicationContext,
            command_name: str,
            message: str | None,
        ) -> None:

        if ctx.guild is None:
            await ctx.respond(
                "I can only make announcements from inside a server. "
                "I'm not that powerful... yet.",
                ephemeral=True,
            )
            return

        engineer_role_ids = {
            role.value.id
            for role in EngineerRoles
        }

        member_role_ids = {
            role.id
            for role in ctx.author.roles
        }

        if not engineer_role_ids.intersection(member_role_ids):
            await ctx.respond(
                "Access denied! Nice try, but you need the Engineer role.",
                ephemeral=True,
            )
            return

        announcement_channel = ctx.guild.get_channel(
            Channels.ANNOUNCEMENT.value.id,
        )

        if not isinstance(
            announcement_channel,
            discord.TextChannel,
        ):
            log_warning(
                "Unable to find the announcement text channel "
                f"(ID: {Channels.ANNOUNCEMENT.value.id}) "
                f"in {ctx.guild.name} (ID: {ctx.guild.id}).",
                scope="EngineerOnly",
            )

            await ctx.respond(
                "I can't find the announcement channel. "
                "Have you tried turning the server off and on again?",
                ephemeral=True,
            )
            return

        announcement = ANNOUNCEMENTS[command_name]

        title = str(announcement["title"])
        description = str(announcement["description"])
        funny_message = str(announcement["funny"])
        color = int(announcement["color"])

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color(color),
        )

        if message and message.strip():
            embed.add_field(
                name="Additional Information",
                value=message.strip(),
                inline=False,
            )

        embed.add_field(
            name="OTCBot says",
            value=f"*{funny_message}*",
            inline=False,
        )

        if self.bot.user is not None:
            embed.set_author(
                name="OTCBot",
                icon_url=self.bot.user.display_avatar.url,
            )
            embed.set_thumbnail(
                url=self.bot.user.display_avatar.url,
            )

        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )
        embed.timestamp = discord.utils.utcnow()

        try:
            await announcement_channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )

            log_notice(
                f"Announcement sent by {ctx.author} "
                f"(ID: {ctx.author.id}) using /{command_name} "
                f"in #{announcement_channel.name} "
                f"(ID: {announcement_channel.id}) "
                f"on {ctx.guild.name} (ID: {ctx.guild.id}).",
                scope="EngineerOnly",
            )

            await ctx.respond(
                f"Announcement sent to "
                f"#{announcement_channel.name}. "
                "My public-speaking career is thriving.",
                ephemeral=True,
            )

        except discord.Forbidden:
            log_warning(
                f"Permission denied while sending /{command_name} "
                f"announcement to channel "
                f"(ID: {announcement_channel.id}).",
                scope="EngineerOnly",
            )

            await ctx.respond(
                "I can't post there! I need permission to send messages "
                "and embed links in the announcement channel.",
                ephemeral=True,
            )

        except discord.HTTPException:
            log_exception(
                f"Failed to send /{command_name} announcement "
                f"to channel (ID: {announcement_channel.id}).",
                scope="EngineerOnly",
            )

            await ctx.respond(
                "Discord refused my announcement. "
                "I'll take it personally.",
                ephemeral=True,
            )


    @discord.slash_command(
        name="bot-maint",
        description="Announces the start of bot maintenance.",
        guild_ids=list(SERVER_IDS),
    )
    async def announce_maint(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Option(
                str,
                description="Optional additional announcement text.",
                required=False,
                max_length=1500,
            ) = None,
        ) -> None:

        await self._send_announcement(
            ctx,
            "bot-maint",
            message,
        )


    @discord.slash_command(
        name="bot-up",
        description="Announces that the bot is operational.",
        guild_ids=list(SERVER_IDS),
    )
    async def announce_up(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Option(
                str,
                description="Optional additional announcement text.",
                required=False,
                max_length=1500,
            ) = None,
        ) -> None:

        await self._send_announcement(
            ctx,
            "bot-up",
            message,
        )


    @discord.slash_command(
        name="bot-down",
        description="Announces that the bot is going offline.",
        guild_ids=list(SERVER_IDS),
    )
    async def announce_down(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Option(
                str,
                description="Optional additional announcement text.",
                required=False,
                max_length=1500,
            ) = None,
        ) -> None:

        await self._send_announcement(
            ctx,
            "bot-down",
            message,
        )


    @discord.slash_command(
        name="bot-issue",
        description="Announces a bot issue.",
        guild_ids=list(SERVER_IDS),
    )
    async def announce_issue(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Option(
                str,
                description="Optional additional announcement text.",
                required=False,
                max_length=1500,
            ) = None,
        ) -> None:

        await self._send_announcement(
            ctx,
            "bot-issue",
            message,
        )


    @discord.slash_command(
        name="bot-update",
        description="Announces a bot update.",
        guild_ids=list(SERVER_IDS),
    )
    async def announce_update(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Option(
                str,
                description="Optional additional announcement text.",
                required=False,
                max_length=1500,
            ) = None,
        ) -> None:

        await self._send_announcement(
            ctx,
            "bot-update",
            message,
        )


    @discord.slash_command(
        name="bot-test",
        description="Sends a test announcement.",
        guild_ids=list(SERVER_IDS),
    )
    async def announce_test(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Option(
                str,
                description="Optional additional announcement text.",
                required=False,
                max_length=1500,
            ) = None,
        ) -> None:

        await self._send_announcement(
            ctx,
            "bot-test",
            message,
        )


def setup(bot: discord.Bot) -> None:

    bot.add_cog(EngineerOnly(bot))

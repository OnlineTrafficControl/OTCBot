##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# cogs.general #


import re
import time

import discord
from discord.ext import commands

from otc_bot.core.constants import SERVER_IDS
from otc_bot.core.logging import (
    log_exception,
    log_info,
    log_notice,
    log_warning,
)


GREETINGS: tuple[str, ...] = (
"hi",
"hello",
"hey",
"hiya",
"heya",
"howdy",
"hallo",
"bonjour",
)

GREETING_PATTERN = re.compile(
r"\b(?:"
+ "|".join(
re.escape(greeting)
for greeting in GREETINGS
)
+ r")\b",
re.IGNORECASE,
)


class General(commands.Cog):


    def __init__(self, bot: discord.Bot) -> None:

        self.bot = bot


    @commands.Cog.listener()
    async def on_message(
            self,
            message: discord.Message,
        ) -> None:

        if message.author.bot:
            return

        if not message.content:
            return

        if not GREETING_PATTERN.search(message.content):
            return

        try:
            await message.add_reaction("👋")

        except discord.Forbidden:
            log_warning(
                f"Unable to react to message {message.id} "
                f"in #{message.channel} "
                f"(ID: {message.channel.id}): "
                f"missing permissions.",
                scope="General",
            )

        except discord.HTTPException:
            log_exception(
                f"Failed to react to greeting message "
                f"{message.id} in #{message.channel} "
                f"(ID: {message.channel.id}).",
                scope="General",
            )


    @discord.slash_command(
        description="Returns the bot's latency and response time.",
        guild_ids=list(SERVER_IDS),
    )
    async def ping(
            self,
            ctx: discord.ApplicationContext,
        ) -> None:

        started_at = time.perf_counter()

        await ctx.defer()

        response_time = (
            time.perf_counter() - started_at
        ) * 1000

        gateway_latency = self.bot.latency * 1000

        await ctx.followup.send(
            embed=discord.Embed(
                title="Pong!",
                color=discord.Color.green(),
                description=(
                    f"**Gateway latency:** "
                    f"{gateway_latency:.1f} ms\n"
                    f"**Initial response time:** "
                    f"{response_time:.1f} ms"
                ),
            )
        )


    @discord.slash_command(
        description="Displays the available bot commands.",
        guild_ids=list(SERVER_IDS),
    )
    async def help(
            self,
            ctx: discord.ApplicationContext,
        ) -> None:

        embed = discord.Embed(
            title="OTCBot Commands",
            color=discord.Color.blurple(),
        )

        for command in self.bot.application_commands:
            if not isinstance(
                command,
                discord.SlashCommand,
            ):
                continue

            if getattr(command, "hidden", False):
                continue

            embed.add_field(
                name=f"/{command.name}",
                value=(
                    command.description
                    or "No description available."
                ),
                inline=False,
            )

        await ctx.respond(
            embed=embed,
            ephemeral=True,
        )


    @discord.slash_command(
        description="Deletes a specified number of messages.",
        guild_ids=list(SERVER_IDS),
    )
    async def purge(
            self,
            ctx: discord.ApplicationContext,
            amount: discord.Option(
                int,
                description="The number of messages to delete.",
                min_value=1,
                max_value=100,
            ),
        ) -> None:

        guild = ctx.guild

        if guild is None:
            await ctx.respond(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        if not ctx.author.guild_permissions.manage_messages:
            await ctx.respond(
                "You need the Manage Messages permission.",
                ephemeral=True,
            )
            return

        if guild.me is None:
            await ctx.respond(
                "Unable to verify the bot's server permissions.",
                ephemeral=True,
            )
            return

        permissions = ctx.channel.permissions_for(guild.me)

        if not permissions.manage_messages:
            await ctx.respond(
                "I need the Manage Messages permission.",
                ephemeral=True,
            )
            return

        if not permissions.read_message_history:
            await ctx.respond(
                "I need the Read Message History permission.",
                ephemeral=True,
            )
            return

        log_notice(
            f"Message purge requested by {ctx.author} "
            f"(ID: {ctx.author.id}) in #{ctx.channel} "
            f"(ID: {ctx.channel.id}) on {guild.name} "
            f"(ID: {guild.id}). Requested amount: {amount}.",
            scope="General",
        )

        await ctx.defer(ephemeral=True)

        try:
            deleted_messages = await ctx.channel.purge(
                limit=amount,
            )

            log_notice(
                f"Message purge completed by {ctx.author} "
                f"(ID: {ctx.author.id}) in #{ctx.channel} "
                f"(ID: {ctx.channel.id}) on {guild.name} "
                f"(ID: {guild.id}). "
                f"Deleted {len(deleted_messages)} message(s).",
                scope="General",
            )

            for message in deleted_messages:
                content = message.content or (
                    "[No text content; possibly an attachment, "
                    "embed, or other non-text message]"
                )

                log_info(
                    f"Deleted message | "
                    f"Author: {message.author} "
                    f"(ID: {message.author.id}) | "
                    f"Message ID: {message.id} | "
                    f"Timestamp: {message.created_at.isoformat()} | "
                    f"Content: {content}",
                    scope="General",
                )

            await ctx.followup.send(
                f"Deleted {len(deleted_messages)} message(s).",
                ephemeral=True,
            )

        except discord.Forbidden:
            log_warning(
                f"Discord denied the purge requested by {ctx.author} "
                f"(ID: {ctx.author.id}) in #{ctx.channel} "
                f"(ID: {ctx.channel.id}).",
                scope="General",
            )

            await ctx.followup.send(
                "Discord denied permission to delete messages.",
                ephemeral=True,
            )

        except discord.HTTPException:
            log_exception(
                f"Failed to purge messages requested by {ctx.author} "
                f"(ID: {ctx.author.id}) in #{ctx.channel} "
                f"(ID: {ctx.channel.id}) on {guild.name} "
                f"(ID: {guild.id}).",
                scope="General",
            )

            await ctx.followup.send(
                "An error occurred while deleting messages.",
                ephemeral=True,
            )


def setup(bot: discord.Bot) -> None:

    bot.add_cog(General(bot))

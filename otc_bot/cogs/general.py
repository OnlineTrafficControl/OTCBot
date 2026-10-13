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

from otc_bot.core.constants import (
    SERVER_IDS,
    GREETINGS,
)
from otc_bot.core.logging import (
    log_exception,
    log_warning,
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


def setup(bot: discord.Bot) -> None:

    bot.add_cog(General(bot))

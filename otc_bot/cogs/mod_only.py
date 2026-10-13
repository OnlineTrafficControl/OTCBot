##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# cogs.mod_only #


from pathlib import Path
import discord
from discord.ext import commands

from otc_bot.core.constants import (
    SERVER_IDS,
    ModRoles,
    EngineerRoles,
)
from otc_bot.core.logging import (
    log_exception,
    log_info,
    log_notice,
    log_warning,
    LOG_DIRECTORY,
)


LOG_HEAD_LINES = 20
LOG_TAIL_LINES = 20
LOG_MAX_CHARS = 1800
LOG_MAX_LINE_CHARS = 250


def _get_latest_log() -> Path | None:

    log_files = list(LOG_DIRECTORY.rglob("*.jar-log"))

    if not log_files:
        return None

    return max(
        log_files,
        key=lambda path: path.stat().st_mtime,
    )


def _format_log_excerpt(log_path: Path) -> str:

    content = log_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = [
        (
            line[:LOG_MAX_LINE_CHARS]
            + " [...]"
            if len(line) > LOG_MAX_LINE_CHARS
            else line
        )
        for line in content.splitlines()
    ]

    if not lines:
        return "[The log file is empty.]"

    if len(lines) <= LOG_HEAD_LINES + LOG_TAIL_LINES:
        excerpt = "\n".join(lines)

        if len(excerpt) <= LOG_MAX_CHARS:
            return excerpt

    head_count = min(LOG_HEAD_LINES, len(lines))
    tail_count = min(LOG_TAIL_LINES, len(lines) - head_count)

    while True:
        head = lines[:head_count]
        tail = lines[len(lines) - tail_count:] if tail_count else []

        truncated = (
            head
            + ["[...]"]
            + tail
        )

        excerpt = "\n".join(truncated)

        if len(excerpt) <= LOG_MAX_CHARS:
            return excerpt

        if head_count >= tail_count and head_count > 0:
            head_count -= 1
        elif tail_count > 0:
            tail_count -= 1
        else:
            return excerpt[:LOG_MAX_CHARS]


class ModOnly(commands.Cog):


    def __init__(self, bot: discord.Bot) -> None:

        self.bot = bot


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


    @discord.slash_command(
        description="Displays the latest bot log.",
        guild_ids=list(SERVER_IDS),
    )
    async def logs(
            self,
            ctx: discord.ApplicationContext,
        ) -> None:

        guild = ctx.guild

        if guild is None:
            await ctx.respond(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        moderator_role_ids = {
            role.value.id
            for role in list(ModRoles) + list(EngineerRoles)
        }

        member_role_ids = {
            role.id
            for role in ctx.author.roles
        }

        if not moderator_role_ids.intersection(member_role_ids):
            await ctx.respond(
                "You need a moderator role to use this command.",
                ephemeral=True,
            )
            return

        log_path = _get_latest_log()

        if log_path is None:
            await ctx.respond(
                "No log files were found.",
                ephemeral=True,
            )
            return

        try:
            excerpt = _format_log_excerpt(log_path)

        except OSError:
            log_exception(
                f"Failed to read log file: {log_path}.",
                scope="General",
            )

            await ctx.respond(
                "Unable to read the latest log file.",
                ephemeral=True,
            )
            return

        excerpt = excerpt.replace("```", "``\u200b`")

        log_notice(
            f"Latest log requested by {ctx.author} "
            f"(ID: {ctx.author.id}) in {guild.name} "
            f"(ID: {guild.id}). File: {log_path.name}.",
            scope="General",
        )

        await ctx.respond(
            f"Latest log: `{log_path.name}`\n"
            f"```text\n{excerpt}\n```",
            ephemeral=True,
        )


def setup(bot: discord.Bot) -> None:

    bot.add_cog(ModOnly(bot))

##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# core.bot #


from pathlib import Path

import discord

from otc_bot.core.constants import SERVER_IDS
from otc_bot.core.logging import (
    log_error,
    log_exception,
    log_info,
    log_notice,
    log_warning,
)


COGS_DIRECTORY = Path(__file__).resolve().parent.parent / "cogs"


class OTCBot(discord.Bot):


    def __init__(self) -> None:
        log_info(
            "Creating bot.",
            scope="Bot",
        )

        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.voice_states = True
        intents.message_content = True

        super().__init__(intents=intents)

        self._ready_once = False
        self._shutdown_started = False
        self._cogs_loaded = False
        self._commands_synced = False

        log_info(
            "Bot created successfully.",
            scope="Bot",
        )


    async def on_connect(self) -> None:
        if not self._cogs_loaded:
            await self.load_cogs()

        if not self._commands_synced:
            await self.sync_commands(force=True)
            self._commands_synced = True

            log_info(
                "Application commands synchronized.",
                scope="Bot",
            )


    async def load_cogs(self) -> None:
        log_info(
            "Loading Cogs.",
            scope="Bot",
        )

        try:
            for path in sorted(COGS_DIRECTORY.glob("*.py")):
                if path.name == "__init__.py":
                    continue

                extension = f"otc_bot.cogs.{path.stem}"

                self.load_extension(extension)

                log_info(
                    f"Loaded extension: {extension}",
                    scope="Bot",
                )

            self._cogs_loaded = True

            log_info(
                f"Configured server IDs: {SERVER_IDS}",
                scope="Bot",
            )

            log_info(
                "Loaded application commands: "
                + ", ".join(
                    command.name
                    for command in self.application_commands
                ),
                scope="Bot",
            )

            log_info(
                "All Cogs loaded successfully.",
                scope="Bot",
            )

        except Exception:
            log_exception(
                "Failed to load Cogs during startup.",
                scope="Bot",
            )
            raise


    async def on_ready(self) -> None:
        if self.user is None:
            log_warning(
                "Bot is ready but its user information is unavailable.",
                scope="Bot",
            )
            return

        if not self._ready_once:
            self._ready_once = True

            log_notice(
                f"OTCBot is ready as {self.user} "
                f"(ID: {self.user.id}).",
                scope="Bot",
            )

            for guild in self.guilds:
                log_info(
                    f"Connected to server: {guild.name} "
                    f"(ID: {guild.id}).",
                    scope="Bot",
                )

            return

        log_info(
            "Discord connection restored.",
            scope="Bot",
        )


    async def close(self) -> None:
        if self._shutdown_started:
            return

        self._shutdown_started = True

        log_notice(
            "OTCBot shutdown started.",
            scope="Bot",
        )

        try:
            await super().close()

            log_info(
                "Discord client closed successfully.",
                scope="Bot",
            )

        except Exception:
            log_exception(
                "An error occurred while closing the Discord client.",
                scope="Bot",
            )
            raise


    async def on_application_command_error(
            self,
            ctx: discord.ApplicationContext,
            error: discord.ApplicationCommandError,
        ) -> None:
        command_name = (
            ctx.command.qualified_name
            if ctx.command is not None
            else "unknown"
        )

        original_error = getattr(error, "original", error)

        log_error(
            f"Application command '/{command_name}' failed: "
            f"{type(original_error).__name__}: {original_error}",
            scope="Commands",
        )

        import traceback

        formatted_traceback = "".join(
            traceback.format_exception(
                type(original_error),
                original_error,
                original_error.__traceback__,
            )
        )

        log_error(
            f"Command traceback:\n{formatted_traceback}",
            scope="Commands",
        )

        try:
            if ctx.interaction.response.is_done():
                await ctx.followup.send(
                    "The command failed unexpectedly. "
                    "The error has been logged.",
                    ephemeral=True,
                )
            else:
                await ctx.respond(
                    "The command failed unexpectedly. "
                    "The error has been logged.",
                    ephemeral=True,
                )

        except discord.HTTPException as response_error:
            log_error(
                "Could not send an error response for "
                f"'/{command_name}': {response_error}",
                scope="Commands",
            )


def create_bot() -> OTCBot:
    return OTCBot()

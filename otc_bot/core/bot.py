##################
##              ##
##    OTCBot    ##
## ------------ ##
##################


from pathlib import Path

import discord

from otc_bot.core.logging import (
    close_logger,
    log_exception,
    log_info,
    log_notice,
    log_warning,
)


COGS_DIRECTORY = Path(__file__).resolve().parent.parent / "cogs"


class OTCBot(discord.Bot):


    def __init__(self) -> None:

        intents = discord.Intents.default()

        intents.guilds = True
        intents.guild_messages = True
        intents.voice_states = True
        intents.message_content = True

        super().__init__(intents=intents)

        self._ready_once = False
        self._shutdown_started = False


    async def setup_hook(self) -> None:

        log_info(
            "Loading Cogs.",
            scope="Bot",
        )

        try:
            for path in sorted(COGS_DIRECTORY.glob("*.py")):
                if path.name == "__init__.py":
                    continue

                extension = f"otc_bot.cogs.{path.stem}"

                await self.load_extension(extension)

                log_info(
                    f"Loaded extension: {extension}",
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
                f"OTCBot is ready as {self.user} (ID: {self.user.id}).",
                scope="Bot",
            )

            for guild in self.guilds:
                log_debug_message = (
                    f"Connected to server: {guild.name} (ID: {guild.id})."
                )

                log_info(
                    log_debug_message,
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


def create_bot() -> OTCBot:

    return OTCBot()

##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# __main__ #


import asyncio
import threading

from discord import LoginFailure

from otc_bot.core.bot import create_bot
from otc_bot.core.constants import BOT_TOKEN
from otc_bot.core.logging import (
    log_critical,
    log_info,
    log_notice,
    log_exception,
    close_logger,
)


def console_input(bot) -> None:

    while True:
        try:
            command = input()

        except EOFError:
            return

        if command.strip().lower() == "exit":
            log_notice(
                "OTCBot shutdown requested from the console.",
                scope="Bot",
            )

            asyncio.run_coroutine_threadsafe(
                bot.close(),
                bot.loop,
            )
            return


def main() -> None:

    bot_failed = False

    try:
        bot = create_bot()

        log_info(
            "Starting OTCBot.",
            scope="Bot",
        )

        input_thread = threading.Thread(
            target=console_input,
            args=(bot,),
            daemon=True,
        )
        input_thread.start()

        bot.run(BOT_TOKEN)

    except LoginFailure:
        log_critical(
            "Discord rejected the bot token. Check OTC_BOT_TOKEN.",
            scope="Bot",
        )
        bot_failed = True

    except KeyboardInterrupt:
        log_notice(
            "OTCBot shutdown requested by the user.",
            scope="Bot",
        )

    except Exception:
        log_exception(
            "OTCBot terminated because of an unexpected error.",
            scope="Bot",
        )
        bot_failed = True

    finally:
        close_logger(
            result="FAILURE" if bot_failed else "SUCCESS"
        )


if __name__ == "__main__":
    main()

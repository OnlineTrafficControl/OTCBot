
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
    log_warning,
    get_latest_log,
    flush_logger,
)


def console_input(
        shutdown_event: threading.Event,
        loop: asyncio.AbstractEventLoop,
        shutdown_requested: asyncio.Event,
    ) -> None:

    while not shutdown_event.is_set():
        try:
            print("\n>>> ", end="")
            command = input().strip().lower()

        except (EOFError, OSError):
            return

        if command == "exit":
            log_notice(
                "OTCBot shutdown requested from the console.",
                scope="Bot",
            )

            shutdown_event.set()
            loop.call_soon_threadsafe(shutdown_requested.set)
            return

        elif command == "logs":
            log_notice(
                "OTCBot logs requested from the console.",
                scope="Bot",
            )

            try:
                with open(get_latest_log(), "r") as log_file:
                    print(log_file.read())

            except OSError as error:
                log_warning(
                    f"Unable to read the latest log: {error}",
                    scope="Bot",
                )

        elif command == "log-flush":
            log_notice(
                "OTCBot log-flush requested from the console.",
                scope="Bot",
            )

            flush_logger()

        elif command == "help":
            print(
                "Available commands:\n"
                "  help         -   Display available commands\n"
                "  logs         -   Display the latest log\n"
                "  log-flush    -   Flush the latest log\n"
                "  exit         -   Shut down OTCBot"
            )

        else:
            log_warning(
                "OTCBot invalid command requested from the console.",
                scope="Bot",
            )


async def run_bot(
        bot,
        shutdown_event: threading.Event,
    ) -> None:

    loop = asyncio.get_running_loop()
    shutdown_requested = asyncio.Event()

    input_thread = threading.Thread(
        target=console_input,
        args=(
            shutdown_event,
            loop,
            shutdown_requested,
        ),
        daemon=True,
    )

    async with bot:
        bot_task = asyncio.create_task(
            bot.start(BOT_TOKEN)
        )
        ready_task = asyncio.create_task(
            bot._ready_event.wait()
        )
        shutdown_task = asyncio.create_task(
            shutdown_requested.wait()
        )

        try:
            done, _ = await asyncio.wait(
                (bot_task, ready_task, shutdown_task),
                return_when=asyncio.FIRST_COMPLETED,
            )

            if bot_task in done:
                await bot_task
                return

            if shutdown_task in done:
                bot_task.cancel()

                await asyncio.gather(
                    bot_task,
                    return_exceptions=True,
                )
                return

            # The bot is ready; the console can now accept commands.
            print("\n\nConsole ready. Type 'help' for available commands.")
            input_thread.start()

            done, _ = await asyncio.wait(
                (bot_task, shutdown_task),
                return_when=asyncio.FIRST_COMPLETED,
            )

            if shutdown_task in done:
                bot_task.cancel()

                await asyncio.gather(
                    bot_task,
                    return_exceptions=True,
                )
            else:
                await bot_task

        finally:
            shutdown_event.set()

            for task in (bot_task, ready_task, shutdown_task):
                if not task.done():
                    task.cancel()

            await asyncio.gather(
                bot_task,
                ready_task,
                shutdown_task,
                return_exceptions=True,
            )


def main() -> None:

    bot_failed = False
    shutdown_event = threading.Event()

    try:
        bot = create_bot()

        log_info(
            "Starting OTCBot.",
            scope="Bot",
        )

        asyncio.run(
            run_bot(
                bot,
                shutdown_event,
            )
        )

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
        shutdown_event.set()

        close_logger(
            result="FAILURE" if bot_failed else "SUCCESS"
        )


if __name__ == "__main__":
    main()

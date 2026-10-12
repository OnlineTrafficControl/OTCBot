##################
##              ##
##    OTCBot    ##
## ------------ ##
##################


from discord import LoginFailure

from otc_bot.core.bot import create_bot
from otc_bot.core.logging import log_critical, log_info, log_notice, log_exception, close_logger
from otc_bot.services.get_env import get_env



def main() -> None:

    bot_failed = False

    try:
        bot = create_bot()
        token = get_env("OTC_BOT_TOKEN")

        log_info(
            "Starting OTCBot.",
            scope="Bot",
        )

        bot.run(token)

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
        bot_failed = False

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

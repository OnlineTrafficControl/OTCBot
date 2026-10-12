##################
##              ##
##    OTCBot    ##
## ------------ ##
##################


from pathlib import Path
from threading import Lock
from traceback import format_exc
from typing import Any

from jarbin_toolkit_log import Log, LogLevel, LogType


LOG_DIRECTORY = Path("logs")
LOG_NAME = "otcbot"

LOG_METADATA: dict[str, Any] = {
    "application": "OTCBot",
}

_logger: Log | None = None
_logger_lock = Lock()


def get_logger() -> Log:
    """
        Get the shared OTCBot logger.

        Returns
        ----------
        Log
            The shared Jar-Log instance
    """

    global _logger

    with _logger_lock:
        if _logger is None:
            _logger = Log(
                directory=LOG_DIRECTORY,
                name=LOG_NAME,
                type=LogType.JAR_LOG,
                metadata=LOG_METADATA,
            )

        return _logger


def log_debug(
        message: str,
        *,
        scope: str = "",
    ) -> None:
    """
        Log a debug message.
    """

    get_logger().log(
        LogLevel.DEBUG,
        message,
        scope=scope,
    )


def log_info(
        message: str,
        *,
        scope: str = "",
    ) -> None:
    """
        Log an informational message.
    """

    get_logger().log(
        LogLevel.INFO,
        message,
        scope=scope,
    )


def log_notice(
        message: str,
        *,
        scope: str = "",
    ) -> None:
    """
        Log a notice message.
    """

    get_logger().log(
        LogLevel.NOTICE,
        message,
        scope=scope,
    )


def log_warning(
        message: str,
        *,
        scope: str = "",
    ) -> None:
    """
        Log a warning message.
    """

    get_logger().log(
        LogLevel.WARNING,
        message,
        scope=scope,
    )


def log_error(
        message: str,
        *,
        scope: str = "",
    ) -> None:
    """
        Log an error message.
    """

    get_logger().log(
        LogLevel.ERROR,
        message,
        scope=scope,
    )


def log_critical(
        message: str,
        *,
        scope: str = "",
    ) -> None:
    """
        Log a critical message.
    """

    get_logger().log(
        LogLevel.CRITICAL,
        message,
        scope=scope,
    )


def log_exception(
        message: str,
        *,
        scope: str = "",
    ) -> None:
    """
        Log an error with the current exception traceback.

        Must be called inside an exception handler.
    """

    traceback = format_exc()

    log_error(
        f"{message}\n{traceback}",
        scope=scope,
    )


def log_comment(
        message: str,
    ) -> None:
    """
        Add a comment to the log file.
    """

    get_logger().comment(message)


def close_logger(
        *,
        result: str = "SUCCESS",
    ) -> None:
    """
        Close the shared logger and finalize its log file.
    """

    global _logger

    with _logger_lock:
        if _logger is None:
            return

        _logger.close(result=result)
        _logger = None

##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# core.logging #


from pathlib import Path
from threading import Lock, Event, Thread
from traceback import format_exc
from typing import Any

from jarbin_toolkit_log import Log, LogLevel, LogType


LOG_DIRECTORY = Path("logs")
LOG_NAME = "otcbot"

LOG_METADATA: dict[str, Any] = {
    "application": "OTCBot",
}

LOG_FLUSH_INTERVAL: float = 10.0

_logger: Log | None = None
_logger_lock = Lock()
_flush_stop = Event()
_flush_thread: Thread | None = None


def get_logger() -> Log:

    global _logger

    with _logger_lock:
        if _logger is None:
            _logger = Log(
                directory=LOG_DIRECTORY,
                name=LOG_NAME,
                type=LogType.JAR_LOG,
                metadata=LOG_METADATA,
            )

            _flush_stop.clear()
            _flush_thread = Thread(
                target=_flush_worker,
                name="OTCBot-LogFlusher",
                daemon=True,
            )
            _flush_thread.start()

        return _logger


def log_debug(
        message: str,
        *,
        scope: str = "",
    ) -> None:

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

    traceback = format_exc()

    log_error(
        f"{message}\n{traceback}",
        scope=scope,
    )


def log_comment(
        message: str,
    ) -> None:

    get_logger().comment(message)


def close_logger(
        *,
        result: str = "SUCCESS",
    ) -> None:

    global _logger
    global _flush_thread

    _flush_stop.set()

    if _flush_thread is not None:
        _flush_thread.join(timeout=LOG_FLUSH_INTERVAL + 1)
        _flush_thread = None

    with _logger_lock:
        if _logger is None:
            return

        try:
            _logger.flush()
        finally:
            _logger.close(result=result)


def _flush_worker() -> None:
    while not _flush_stop.wait(LOG_FLUSH_INTERVAL):
        with _logger_lock:
            if _logger is None:
                continue

            try:
                _logger.flush()
            except Exception:
                pass

##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# core.logging #


from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path
from threading import Event, Lock, Thread
from traceback import format_exc
from typing import Any

from jarbin_toolkit_log import Log, LogLevel, LogType


LOG_DIRECTORY = Path("logs")
LOG_NAME = "otcbot"

LOG_METADATA: dict[str, Any] = {
    "application": "OTCBot",
}

LOG_FLUSH_INTERVAL: float = 60.0
LOG_RETENTION_DAYS: int = 7

_logger: Log | None = None
_logger_lock = Lock()
_flush_stop = Event()
_flush_thread: Thread | None = None


def get_latest_log() -> Path | None:

    log_files = list(LOG_DIRECTORY.rglob("*.jar-log"))

    if not log_files:
        return None

    return max(
        log_files,
        key=lambda path: path.stat().st_mtime,
    )


def _utc_now() -> datetime:

    return datetime.now(timezone.utc)


def _create_logger() -> Log:

    LOG_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_date = _utc_now().date()

    return Log(
        directory=LOG_DIRECTORY,
        name=f"{LOG_NAME}_{log_date.isoformat()}",
        type=LogType.JAR_LOG,
        metadata=LOG_METADATA,
    )


def _cleanup_old_logs() -> None:

    if not LOG_DIRECTORY.exists():
        return

    cutoff = _utc_now() - timedelta(
        days=LOG_RETENTION_DAYS,
    )

    for path in LOG_DIRECTORY.iterdir():
        if not path.is_file():
            continue

        if not path.name.startswith(f"{LOG_NAME}_"):
            continue

        try:
            modified_at = datetime.fromtimestamp(
                path.stat().st_mtime,
                tz=timezone.utc,
            )

            if modified_at < cutoff:
                path.unlink()

        except OSError:
            continue


def _rotate_logger() -> None:

    global _logger

    old_run_id = None

    if _logger is not None:
        old_run_id = _logger.run_id

        try:
            _logger.info(
                f"Log rotation started. "
                f"Run ID: {old_run_id} -> pending."
            )
            _logger.flush()
        finally:
            _logger.close(result="SUCCESS")

    _logger = _create_logger()

    new_run_id = _logger.run_id

    _logger.info(
        f"Log rotation completed. "
        f"Previous run ID: {old_run_id} -> "
        f"Current run ID: {new_run_id}."
    )

    _cleanup_old_logs()


def get_logger() -> Log:

    global _logger
    global _flush_thread

    with _logger_lock:
        if _logger is None:
            _cleanup_old_logs()
            _logger = _create_logger()

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
        _flush_thread.join(
            timeout=LOG_FLUSH_INTERVAL + 1,
        )
        _flush_thread = None

    with _logger_lock:
        if _logger is None:
            return

        try:
            _logger.flush()
        finally:
            _logger.close(result=result)
            _logger = None


def flush_logger(
    ) -> None:

    get_logger().flush()


def _flush_worker() -> None:

    global _logger

    while not _flush_stop.is_set():
        now = _utc_now()
        next_midnight = (
            now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            + timedelta(days=1)
        )

        seconds_until_midnight = (
            next_midnight - now
        ).total_seconds()

        wait_time = min(
            LOG_FLUSH_INTERVAL,
            seconds_until_midnight,
        )

        if _flush_stop.wait(wait_time):
            break

        with _logger_lock:
            if _logger is None:
                continue

            try:
                if _utc_now().date() != now.date():
                    _rotate_logger()
                else:
                    _logger.flush()

            except Exception:
                pass

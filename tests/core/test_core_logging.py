from threading import Event
from unittest.mock import MagicMock

import pytest

import otc_bot.core.logging as logging_module


@pytest.fixture(autouse=True)
def reset_logger_state(monkeypatch):
    monkeypatch.setattr(logging_module, "_logger", None)
    monkeypatch.setattr(logging_module, "_flush_thread", None)
    monkeypatch.setattr(logging_module, "_flush_stop", Event())


def test_get_logger_creates_logger_once(monkeypatch) -> None:
    fake_logger = MagicMock()
    fake_thread = MagicMock()

    logger_factory = MagicMock(return_value=fake_logger)
    monkeypatch.setattr(logging_module, "Log", logger_factory)
    monkeypatch.setattr(logging_module, "Thread", lambda **kwargs: fake_thread)

    first = logging_module.get_logger()
    second = logging_module.get_logger()

    assert first is fake_logger
    assert second is fake_logger
    logger_factory.assert_called_once()
    fake_thread.start.assert_called_once()


@pytest.mark.parametrize(
    ("function_name", "level_name"),
    [
        ("log_debug", "DEBUG"),
        ("log_info", "INFO"),
        ("log_notice", "NOTICE"),
        ("log_warning", "WARNING"),
        ("log_error", "ERROR"),
        ("log_critical", "CRITICAL"),
    ],
)
def test_log_wrappers(
    monkeypatch,
    function_name: str,
    level_name: str,
) -> None:
    fake_logger = MagicMock()
    monkeypatch.setattr(logging_module, "get_logger", lambda: fake_logger)

    getattr(logging_module, function_name)("message", scope="Test")

    fake_logger.log.assert_called_once_with(
        getattr(logging_module.LogLevel, level_name),
        "message",
        scope="Test",
    )


def test_log_exception_includes_traceback(monkeypatch) -> None:
    messages = []

    monkeypatch.setattr(
        logging_module,
        "format_exc",
        lambda: "Traceback: example error",
    )
    monkeypatch.setattr(
        logging_module,
        "log_error",
        lambda message, **kwargs: messages.append((message, kwargs)),
    )

    logging_module.log_exception("Operation failed", scope="Test")

    assert len(messages) == 1
    assert "Operation failed" in messages[0][0]
    assert "Traceback: example error" in messages[0][0]
    assert messages[0][1] == {"scope": "Test"}


def test_log_comment(monkeypatch) -> None:
    fake_logger = MagicMock()
    monkeypatch.setattr(logging_module, "get_logger", lambda: fake_logger)

    logging_module.log_comment("comment")

    fake_logger.comment.assert_called_once_with("comment")


def test_close_logger_without_logger() -> None:
    logging_module.close_logger()

    assert logging_module._logger is None


def test_close_logger_flushes_and_closes(monkeypatch) -> None:
    fake_logger = MagicMock()
    fake_thread = MagicMock()

    monkeypatch.setattr(logging_module, "_logger", fake_logger)
    monkeypatch.setattr(logging_module, "_flush_thread", fake_thread)

    logging_module.close_logger(result="FAILURE")

    fake_thread.join.assert_called_once()
    fake_logger.flush.assert_called_once()
    fake_logger.close.assert_called_once_with(result="FAILURE")
    assert logging_module._flush_thread is None


def test_close_logger_closes_even_if_flush_fails(monkeypatch) -> None:
    fake_logger = MagicMock()
    fake_logger.flush.side_effect = RuntimeError("flush failed")

    monkeypatch.setattr(logging_module, "_logger", fake_logger)

    with pytest.raises(RuntimeError, match="flush failed"):
        logging_module.close_logger()

    fake_logger.close.assert_called_once_with(result="SUCCESS")


def test_flush_worker_stops_when_event_is_set(monkeypatch) -> None:
    stop_event = MagicMock()
    stop_event.wait.return_value = True

    monkeypatch.setattr(logging_module, "_flush_stop", stop_event)

    logging_module._flush_worker()

    stop_event.wait.assert_called_once_with(
        logging_module.LOG_FLUSH_INTERVAL,
    )


def test_flush_worker_flushes_logger(monkeypatch) -> None:
    stop_event = MagicMock()
    stop_event.wait.side_effect = [False, True]

    fake_logger = MagicMock()
    monkeypatch.setattr(logging_module, "_flush_stop", stop_event)
    monkeypatch.setattr(logging_module, "_logger", fake_logger)

    logging_module._flush_worker()

    fake_logger.flush.assert_called_once()


def test_flush_worker_ignores_flush_error(monkeypatch) -> None:
    stop_event = MagicMock()
    stop_event.wait.side_effect = [False, True]

    fake_logger = MagicMock()
    fake_logger.flush.side_effect = RuntimeError("flush failed")

    monkeypatch.setattr(logging_module, "_flush_stop", stop_event)
    monkeypatch.setattr(logging_module, "_logger", fake_logger)

    logging_module._flush_worker()

    fake_logger.flush.assert_called_once()

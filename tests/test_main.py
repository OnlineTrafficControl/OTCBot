import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from discord import LoginFailure

from otc_bot import __main__ as main_module


class FakeBot:

    def __init__(self, *, start_error=None, ready=True):
        self.start_error = start_error
        self.ready_on_start = ready
        self._ready_event = asyncio.Event()
        self.start = AsyncMock(side_effect=self._start)
        self.entered = False
        self.exited = False
        self.exit_exception = None

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        self.exited = True
        self.exit_exception = exc
        return False

    async def _start(self, token):
        if self.start_error is not None:
            raise self.start_error

        if self.ready_on_start:
            self._ready_event.set()

        await asyncio.Event().wait()


def make_shutdown_event():
    return threading.Event()


@pytest.mark.asyncio
async def test_run_bot_starts_and_waits_for_bot(
    monkeypatch,
    capsys,
):
    bot = FakeBot()
    shutdown_event = make_shutdown_event()

    class FakeThread:

        def __init__(self, *, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon
            self.started = False

        def start(self):
            self.started = True
            shutdown_event.set()
            self.args[2].set()

    monkeypatch.setattr(
        main_module.threading,
        "Thread",
        FakeThread,
    )

    await main_module.run_bot(bot, shutdown_event)

    assert bot.entered is True
    assert bot.exited is True
    bot.start.assert_awaited_once_with(main_module.BOT_TOKEN)
    assert shutdown_event.is_set()


@pytest.mark.asyncio
async def test_run_bot_returns_if_start_finishes_before_ready():
    bot = FakeBot(ready=False)

    async def finish_start(token):
        return None

    bot.start = AsyncMock(side_effect=finish_start)
    shutdown_event = make_shutdown_event()

    await main_module.run_bot(bot, shutdown_event)

    bot.start.assert_awaited_once_with(main_module.BOT_TOKEN)
    assert bot.entered is True
    assert bot.exited is True
    assert shutdown_event.is_set()


@pytest.mark.asyncio
async def test_run_bot_propagates_start_error():
    error = RuntimeError("Discord connection failed")
    bot = FakeBot(start_error=error)
    shutdown_event = make_shutdown_event()

    with pytest.raises(RuntimeError, match="Discord connection failed"):
        await main_module.run_bot(bot, shutdown_event)

    assert bot.entered is True
    assert bot.exited is True
    assert shutdown_event.is_set()


def test_console_input_exit(monkeypatch):
    shutdown_event = threading.Event()
    loop = MagicMock()
    shutdown_requested = asyncio.Event()

    monkeypatch.setattr("builtins.input", lambda: "exit")
    monkeypatch.setattr(main_module, "log_notice", MagicMock())

    main_module.console_input(
        shutdown_event,
        loop,
        shutdown_requested,
    )

    assert shutdown_event.is_set()
    loop.call_soon_threadsafe.assert_called_once_with(
        shutdown_requested.set,
    )
    main_module.log_notice.assert_called_once()


def test_console_input_help(monkeypatch, capsys):
    shutdown_event = threading.Event()
    loop = MagicMock()
    shutdown_requested = asyncio.Event()
    commands = iter(["help", "exit"])

    monkeypatch.setattr(
        "builtins.input",
        lambda: next(commands),
    )
    monkeypatch.setattr(main_module, "log_notice", MagicMock())

    main_module.console_input(
        shutdown_event,
        loop,
        shutdown_requested,
    )

    output = capsys.readouterr().out

    assert "Available commands:" in output
    assert "log-flush" in output
    assert "exit" in output


def test_console_input_logs_latest_file(
    monkeypatch,
    capsys,
    tmp_path,
):
    log_file = tmp_path / "latest.log"
    log_file.write_text("first log line\nsecond log line")

    commands = iter(["logs", "exit"])
    monkeypatch.setattr(
        "builtins.input",
        lambda: next(commands),
    )
    monkeypatch.setattr(
        main_module,
        "get_latest_log",
        lambda: log_file,
    )
    monkeypatch.setattr(main_module, "log_notice", MagicMock())

    main_module.console_input(
        threading.Event(),
        MagicMock(),
        asyncio.Event(),
    )

    output = capsys.readouterr().out

    assert "first log line" in output
    assert "second log line" in output


def test_console_input_handles_log_read_error(monkeypatch):
    shutdown_event = threading.Event()
    warnings = []
    commands = iter(["logs", "exit"])

    monkeypatch.setattr(
        "builtins.input",
        lambda: next(commands),
    )
    monkeypatch.setattr(
        main_module,
        "get_latest_log",
        lambda: "/path/that/does/not/exist/latest.log",
    )
    monkeypatch.setattr(main_module, "log_notice", MagicMock())
    monkeypatch.setattr(
        main_module,
        "log_warning",
        lambda message, **kwargs: warnings.append(message),
    )

    main_module.console_input(
        shutdown_event,
        MagicMock(),
        asyncio.Event(),
    )

    assert warnings
    assert "Unable to read the latest log" in warnings[0]


def test_console_input_flushes_logs(monkeypatch):
    commands = iter(["log-flush", "exit"])
    flush = MagicMock()

    monkeypatch.setattr(
        "builtins.input",
        lambda: next(commands),
    )
    monkeypatch.setattr(main_module, "flush_logger", flush)
    monkeypatch.setattr(main_module, "log_notice", MagicMock())

    main_module.console_input(
        threading.Event(),
        MagicMock(),
        asyncio.Event(),
    )

    flush.assert_called_once()


def test_console_input_warns_on_invalid_command(monkeypatch):
    warnings = []
    commands = iter(["invalid", "exit"])

    monkeypatch.setattr(
        "builtins.input",
        lambda: next(commands),
    )
    monkeypatch.setattr(main_module, "log_notice", MagicMock())
    monkeypatch.setattr(
        main_module,
        "log_warning",
        lambda message, **kwargs: warnings.append(message),
    )

    main_module.console_input(
        threading.Event(),
        MagicMock(),
        asyncio.Event(),
    )

    assert len(warnings) == 1
    assert "invalid command" in warnings[0]


@pytest.mark.parametrize("exception", [EOFError, OSError])
def test_console_input_returns_on_input_error(
    monkeypatch,
    exception,
):
    monkeypatch.setattr(
        "builtins.input",
        MagicMock(side_effect=exception),
    )

    shutdown_event = threading.Event()

    main_module.console_input(
        shutdown_event,
        MagicMock(),
        asyncio.Event(),
    )

    # EOF and input errors currently stop the console thread only.
    assert not shutdown_event.is_set()


def test_main_success(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(main_module, "create_bot", lambda: bot)
    monkeypatch.setattr(
        main_module,
        "run_bot",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        main_module.asyncio,
        "run",
        lambda coroutine: coroutine.close(),
    )
    info = MagicMock()
    close = MagicMock()

    monkeypatch.setattr(main_module, "log_info", info)
    monkeypatch.setattr(main_module, "close_logger", close)

    main_module.main()

    info.assert_called_once()
    close.assert_called_once_with(result="SUCCESS")


def test_main_handles_login_failure(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "create_bot",
        lambda: FakeBot(),
    )

    async def fail(*args, **kwargs):
        raise LoginFailure("invalid token")

    monkeypatch.setattr(main_module, "run_bot", fail)

    critical = MagicMock()
    close = MagicMock()

    monkeypatch.setattr(main_module, "log_critical", critical)
    monkeypatch.setattr(main_module, "close_logger", close)

    main_module.main()

    critical.assert_called_once_with(
        "Discord rejected the bot token. Check OTC_BOT_TOKEN.",
        scope="Bot",
    )
    close.assert_called_once_with(result="FAILURE")


def test_main_handles_unexpected_error(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "create_bot",
        lambda: FakeBot(),
    )

    async def fail(*args, **kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(main_module, "run_bot", fail)

    exception_logger = MagicMock()
    close = MagicMock()

    monkeypatch.setattr(
        main_module,
        "log_exception",
        exception_logger,
    )
    monkeypatch.setattr(main_module, "close_logger", close)

    main_module.main()

    exception_logger.assert_called_once_with(
        "OTCBot terminated because of an unexpected error.",
        scope="Bot",
    )
    close.assert_called_once_with(result="FAILURE")


def test_main_handles_bot_creation_failure(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "create_bot",
        MagicMock(side_effect=RuntimeError("creation failed")),
    )

    exception_logger = MagicMock()
    close = MagicMock()
    monkeypatch.setattr(
        main_module,
        "log_exception",
        exception_logger,
    )
    monkeypatch.setattr(main_module, "close_logger", close)

    main_module.main()

    exception_logger.assert_called_once()
    close.assert_called_once_with(result="FAILURE")

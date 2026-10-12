from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import asyncio
import pytest

from otc_bot.core.bot import OTCBot


@pytest.fixture
def bot() -> OTCBot:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    instance = OTCBot()

    yield instance

    if not loop.is_closed():
        loop.close()

    asyncio.set_event_loop(None)


@pytest.mark.asyncio
async def test_on_connect_loads_and_syncs_once(bot, monkeypatch) -> None:
    async def fake_load_cogs() -> None:
        bot._cogs_loaded = True

    bot.load_cogs = AsyncMock(side_effect=fake_load_cogs)
    bot.sync_commands = AsyncMock()

    monkeypatch.setattr("otc_bot.core.bot.log_info", lambda *a, **k: None)

    await bot.on_connect()
    await bot.on_connect()

    bot.load_cogs.assert_awaited_once()
    bot.sync_commands.assert_awaited_once_with(force=True)
    assert bot._cogs_loaded is True
    assert bot._commands_synced is True


@pytest.mark.asyncio
async def test_on_connect_skips_completed_steps(bot, monkeypatch) -> None:
    bot._cogs_loaded = True
    bot._commands_synced = True
    bot.load_cogs = AsyncMock()
    bot.sync_commands = AsyncMock()

    await bot.on_connect()

    bot.load_cogs.assert_not_awaited()
    bot.sync_commands.assert_not_awaited()


@pytest.mark.asyncio
async def test_load_cogs_loads_python_extensions(
    bot,
    monkeypatch,
    tmp_path,
) -> None:
    (tmp_path / "general.py").touch()
    (tmp_path / "voice_channels.py").touch()
    (tmp_path / "__init__.py").touch()

    monkeypatch.setattr("otc_bot.core.bot.COGS_DIRECTORY", tmp_path)
    monkeypatch.setattr("otc_bot.core.bot.log_info", lambda *a, **k: None)
    monkeypatch.setattr("otc_bot.core.bot.log_exception", lambda *a, **k: None)

    loaded = []
    monkeypatch.setattr(bot, "load_extension", loaded.append)

    await bot.load_cogs()

    assert loaded == [
        "otc_bot.cogs.general",
        "otc_bot.cogs.voice_channels",
    ]
    assert bot._cogs_loaded is True


@pytest.mark.asyncio
async def test_load_cogs_logs_and_reraises_failure(
    bot,
    monkeypatch,
    tmp_path,
) -> None:
    (tmp_path / "general.py").touch()

    monkeypatch.setattr("otc_bot.core.bot.COGS_DIRECTORY", tmp_path)
    monkeypatch.setattr("otc_bot.core.bot.log_info", lambda *a, **k: None)

    errors = []
    monkeypatch.setattr(
        "otc_bot.core.bot.log_exception",
        lambda message, **kwargs: errors.append(message),
    )

    def fail_loading(extension: str) -> None:
        raise RuntimeError("extension failed")

    monkeypatch.setattr(bot, "load_extension", fail_loading)

    with pytest.raises(RuntimeError, match="extension failed"):
        await bot.load_cogs()

    assert bot._cogs_loaded is False
    assert errors


@pytest.mark.asyncio
async def test_on_ready_without_user(bot, monkeypatch) -> None:
    bot._ready_once = False
    bot._connection.user = None

    warnings = []
    monkeypatch.setattr(
        "otc_bot.core.bot.log_warning",
        lambda message, **kwargs: warnings.append(message),
    )

    await bot.on_ready()

    assert bot._ready_once is False
    assert warnings


@pytest.mark.asyncio
async def test_on_ready_logs_first_connection(bot, monkeypatch) -> None:
    bot._ready_once = False
    bot._connection._guilds = {
        456: SimpleNamespace(name="Test Server", id=456),
    }
    bot._connection.user = SimpleNamespace(id=123, __str__=lambda self: "OTCBot")

    monkeypatch.setattr("otc_bot.core.bot.log_notice", lambda *a, **k: None)

    infos = []
    monkeypatch.setattr(
        "otc_bot.core.bot.log_info",
        lambda message, **kwargs: infos.append(message),
    )

    await bot.on_ready()

    assert bot._ready_once is True
    assert any("Test Server" in message for message in infos)


@pytest.mark.asyncio
async def test_on_ready_logs_reconnection(bot, monkeypatch) -> None:
    bot._ready_once = True
    bot._connection.user = SimpleNamespace(id=123)

    infos = []
    monkeypatch.setattr(
        "otc_bot.core.bot.log_info",
        lambda message, **kwargs: infos.append(message),
    )

    await bot.on_ready()

    assert any("restored" in message.lower() for message in infos)


@pytest.mark.asyncio
async def test_close_is_idempotent(bot, monkeypatch) -> None:
    closed = []

    async def fake_close(self) -> None:
        closed.append(True)

    monkeypatch.setattr(discord.Bot, "close", fake_close)
    monkeypatch.setattr("otc_bot.core.bot.log_notice", lambda *a, **k: None)
    monkeypatch.setattr("otc_bot.core.bot.log_info", lambda *a, **k: None)

    await bot.close()
    await bot.close()

    assert len(closed) == 1
    assert bot._shutdown_started is True


@pytest.mark.asyncio
async def test_close_logs_and_reraises_failure(bot, monkeypatch) -> None:
    async def fail_close(self) -> None:
        raise RuntimeError("close failed")

    monkeypatch.setattr(discord.Bot, "close", fail_close)
    monkeypatch.setattr("otc_bot.core.bot.log_notice", lambda *a, **k: None)

    errors = []
    monkeypatch.setattr(
        "otc_bot.core.bot.log_exception",
        lambda message, **kwargs: errors.append(message),
    )

    with pytest.raises(RuntimeError, match="close failed"):
        await bot.close()

    assert errors


@pytest.mark.asyncio
async def test_command_error_uses_initial_response(bot, monkeypatch) -> None:
    ctx = MagicMock()
    ctx.command.qualified_name = "ping"
    ctx.interaction.response.is_done.return_value = False
    ctx.respond = AsyncMock()
    ctx.followup.send = AsyncMock()

    errors = []
    monkeypatch.setattr(
        "otc_bot.core.bot.log_error",
        lambda message, **kwargs: errors.append(message),
    )

    await bot.on_application_command_error(
        ctx,
        discord.ApplicationCommandError("test error"),
    )

    ctx.respond.assert_awaited_once()
    ctx.followup.send.assert_not_awaited()
    assert len(errors) == 2


@pytest.mark.asyncio
async def test_command_error_uses_followup(bot, monkeypatch) -> None:
    ctx = MagicMock()
    ctx.command.qualified_name = "ping"
    ctx.interaction.response.is_done.return_value = True
    ctx.respond = AsyncMock()
    ctx.followup.send = AsyncMock()

    monkeypatch.setattr("otc_bot.core.bot.log_error", lambda *a, **k: None)

    await bot.on_application_command_error(
        ctx,
        discord.ApplicationCommandError("test error"),
    )

    ctx.followup.send.assert_awaited_once()
    ctx.respond.assert_not_awaited()


@pytest.mark.asyncio
async def test_command_error_handles_missing_command(bot, monkeypatch) -> None:
    ctx = MagicMock()
    ctx.command = None
    ctx.interaction.response.is_done.return_value = False
    ctx.respond = AsyncMock()

    logs = []
    monkeypatch.setattr(
        "otc_bot.core.bot.log_error",
        lambda message, **kwargs: logs.append(message),
    )

    await bot.on_application_command_error(
        ctx,
        discord.ApplicationCommandError("test error"),
    )

    assert any("unknown" in message for message in logs)
    ctx.respond.assert_awaited_once()

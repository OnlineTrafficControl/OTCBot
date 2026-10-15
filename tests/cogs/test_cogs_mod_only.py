import discord
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from otc_bot.core.constants import EngineerRoles, ModRoles
from otc_bot.cogs import mod_only as mod_module
from otc_bot.cogs.mod_only import ModOnly, _format_log_excerpt


def make_discord_exception(
        exception_type,
        *,
        status,
        reason,
    ):
    response = MagicMock()
    response.status = status
    response.reason = reason

    return exception_type(
        response=response,
        message=reason,
    )


def make_author_with_roles(*role_ids):
    return SimpleNamespace(
        id=100,
        name="TestUser",
        roles=[
            SimpleNamespace(id=role_id)
            for role_id in role_ids
        ],
        guild_permissions=SimpleNamespace(
            manage_messages=True,
        ),
    )


def make_log_guild():
    guild = MagicMock()
    guild.name = "Test Server"
    guild.id = 300
    return guild


def test_format_log_excerpt_empty_file(tmp_path):
    log_file = tmp_path / "empty.log"
    log_file.write_text("", encoding="utf-8")

    assert _format_log_excerpt(log_file) == (
        "[The log file is empty.]"
    )


def test_format_log_excerpt_short_file(tmp_path):
    log_file = tmp_path / "latest.log"
    log_file.write_text(
        "first line\nsecond line\nthird line",
        encoding="utf-8",
    )

    assert _format_log_excerpt(log_file) == (
        "first line\nsecond line\nthird line"
    )


def test_format_log_excerpt_truncates_long_lines(tmp_path):
    log_file = tmp_path / "latest.log"
    log_file.write_text(
        "A" * (mod_module.LOG_MAX_LINE_CHARS + 50),
        encoding="utf-8",
    )

    excerpt = _format_log_excerpt(log_file)

    assert excerpt.endswith(" [...]")
    assert len(excerpt) <= mod_module.LOG_MAX_LINE_CHARS + len(" [...]")


def test_format_log_excerpt_keeps_head_and_tail(tmp_path):
    log_file = tmp_path / "latest.log"
    lines = [f"line {index}" for index in range(100)]
    log_file.write_text("\n".join(lines), encoding="utf-8")

    excerpt = _format_log_excerpt(log_file)

    assert "line 0" in excerpt
    assert "line 99" in excerpt
    assert "[...]" in excerpt
    assert len(excerpt) <= mod_module.LOG_MAX_CHARS


def test_format_log_excerpt_respects_character_limit(tmp_path):
    log_file = tmp_path / "latest.log"
    log_file.write_text(
        "\n".join(
            f"{index:03d} " + "x" * 200
            for index in range(100)
        ),
        encoding="utf-8",
    )

    excerpt = _format_log_excerpt(log_file)

    assert len(excerpt) <= mod_module.LOG_MAX_CHARS


def test_format_log_excerpt_handles_invalid_utf8(tmp_path):
    log_file = tmp_path / "invalid.log"
    log_file.write_bytes(b"valid line\ninvalid: \xff")

    excerpt = _format_log_excerpt(log_file)

    assert "valid line" in excerpt
    assert "invalid:" in excerpt


@pytest.mark.asyncio
async def test_logs_rejects_dm(make_context):
    cog = ModOnly(MagicMock())
    ctx = make_context(guild=None)

    await ModOnly.logs.callback(cog, ctx)

    ctx.respond.assert_awaited_once_with(
        "This command can only be used in a server.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_logs_rejects_user_without_moderator_role(make_context):
    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(),
    )

    await ModOnly.logs.callback(cog, ctx)

    ctx.respond.assert_awaited_once_with(
        "You need a moderator or engineer role to use this command.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_logs_accepts_moderator_role(
    make_context,
    monkeypatch,
    tmp_path,
):
    role_id = next(iter(ModRoles)).value.id
    log_file = tmp_path / "latest.log"
    log_file.write_text("test log entry", encoding="utf-8")

    monkeypatch.setattr(
        mod_module,
        "get_latest_log",
        lambda: log_file,
    )
    monkeypatch.setattr(mod_module, "log_notice", MagicMock())

    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(role_id),
    )

    await ModOnly.logs.callback(cog, ctx)

    ctx.respond.assert_awaited_once()
    response = ctx.respond.await_args.args[0]

    assert "latest.log" in response
    assert "test log entry" in response
    assert "```text" in response
    assert ctx.respond.await_args.kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_logs_accepts_engineer_role(
    make_context,
    monkeypatch,
    tmp_path,
):
    role_id = next(iter(EngineerRoles)).value.id
    log_file = tmp_path / "latest.log"
    log_file.write_text("engineer log entry", encoding="utf-8")

    monkeypatch.setattr(
        mod_module,
        "get_latest_log",
        lambda: log_file,
    )
    monkeypatch.setattr(mod_module, "log_notice", MagicMock())

    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(role_id),
    )

    await ModOnly.logs.callback(cog, ctx)

    assert "engineer log entry" in ctx.respond.await_args.args[0]


@pytest.mark.asyncio
async def test_logs_reports_missing_file(
    make_context,
    monkeypatch,
):
    monkeypatch.setattr(
        mod_module,
        "get_latest_log",
        lambda: None,
    )

    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(
            next(iter(ModRoles)).value.id,
        ),
    )

    await ModOnly.logs.callback(cog, ctx)

    ctx.respond.assert_awaited_once_with(
        "No log files were found.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_logs_handles_read_error(
    make_context,
    monkeypatch,
    tmp_path,
):
    log_file = tmp_path / "latest.log"
    log_file.write_text("test", encoding="utf-8")

    monkeypatch.setattr(
        mod_module,
        "get_latest_log",
        lambda: log_file,
    )
    monkeypatch.setattr(
        mod_module,
        "_format_log_excerpt",
        MagicMock(side_effect=OSError("read failed")),
    )

    exception_logger = MagicMock()
    monkeypatch.setattr(
        mod_module,
        "log_exception",
        exception_logger,
    )

    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(
            next(iter(ModRoles)).value.id,
        ),
    )

    await ModOnly.logs.callback(cog, ctx)

    exception_logger.assert_called_once()
    ctx.respond.assert_awaited_once_with(
        "Unable to read the latest log file.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_logs_escapes_code_fences(
    make_context,
    monkeypatch,
    tmp_path,
):
    log_file = tmp_path / "latest.log"
    log_file.write_text(
        "before ``` dangerous code fence ``` after",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        mod_module,
        "get_latest_log",
        lambda: log_file,
    )
    monkeypatch.setattr(mod_module, "log_notice", MagicMock())

    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(
            next(iter(ModRoles)).value.id,
        ),
    )

    await ModOnly.logs.callback(cog, ctx)

    response = ctx.respond.await_args.args[0]
    assert "``\u200b`" in response


@pytest.mark.asyncio
async def test_log_flush_rejects_dm(make_context):
    cog = ModOnly(MagicMock())
    ctx = make_context(guild=None)

    await ModOnly.log_flush.callback(cog, ctx)

    ctx.respond.assert_awaited_once_with(
        "This command can only be used in a server.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_log_flush_rejects_user_without_role(make_context):
    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(),
    )

    await ModOnly.log_flush.callback(cog, ctx)

    ctx.respond.assert_awaited_once_with(
        "You need a moderator or engineer role to use this command.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_log_flush_success(
    make_context,
    monkeypatch,
):
    flush = MagicMock()
    notice = MagicMock()

    monkeypatch.setattr(mod_module, "flush_logger", flush)
    monkeypatch.setattr(mod_module, "log_notice", notice)

    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(
            next(iter(ModRoles)).value.id,
        ),
    )

    await ModOnly.log_flush.callback(cog, ctx)

    flush.assert_called_once()
    notice.assert_called_once()
    ctx.respond.assert_awaited_once_with(
        "Buffered logs have been flushed.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_log_flush_handles_exception(
    make_context,
    monkeypatch,
):
    monkeypatch.setattr(
        mod_module,
        "flush_logger",
        MagicMock(side_effect=OSError("flush failed")),
    )

    exception_logger = MagicMock()
    monkeypatch.setattr(
        mod_module,
        "log_exception",
        exception_logger,
    )

    cog = ModOnly(MagicMock())
    ctx = make_context(
        guild=make_log_guild(),
        author=make_author_with_roles(
            next(iter(ModRoles)).value.id,
        ),
    )

    await ModOnly.log_flush.callback(cog, ctx)

    exception_logger.assert_called_once()
    ctx.respond.assert_awaited_once_with(
        "Unable to flush the logs.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_purge_logs_message_without_text(
    make_context,
    monkeypatch,
):
    cog = ModOnly(MagicMock())
    guild = make_log_guild()
    guild.me = object()

    message = SimpleNamespace(
        id=501,
        content="",
        author=SimpleNamespace(id=601, name="AttachmentAuthor"),
        created_at=MagicMock(),
    )
    message.created_at.isoformat.return_value = (
        "2026-10-15T12:00:00+00:00"
    )

    ctx = make_context(guild=guild)
    ctx.channel.permissions_for.return_value = SimpleNamespace(
        manage_messages=True,
        read_message_history=True,
    )
    ctx.channel.purge = AsyncMock(return_value=[message])

    info_messages = []
    monkeypatch.setattr(
        mod_module,
        "log_info",
        lambda message, **kwargs: info_messages.append(message),
    )
    monkeypatch.setattr(mod_module, "log_notice", MagicMock())

    await ModOnly.purge.callback(cog, ctx, amount=1)

    assert len(info_messages) == 1
    assert "No text content" in info_messages[0]
    assert "AttachmentAuthor" in info_messages[0]
    assert "2026-10-15T12:00:00+00:00" in info_messages[0]


@pytest.mark.asyncio
async def test_purge_handles_http_exception(
    make_context,
    monkeypatch,
):
    cog = ModOnly(MagicMock())
    guild = make_log_guild()
    guild.me = object()

    ctx = make_context(guild=guild)
    ctx.channel.permissions_for.return_value = SimpleNamespace(
        manage_messages=True,
        read_message_history=True,
    )
    ctx.channel.purge.side_effect = make_discord_exception(
        discord.HTTPException,
        status=500,
        reason="Internal Server Error",
    )

    exception_logger = MagicMock()
    monkeypatch.setattr(
        mod_module,
        "log_exception",
        exception_logger,
    )
    monkeypatch.setattr(mod_module, "log_notice", MagicMock())

    await ModOnly.purge.callback(cog, ctx, amount=10)

    exception_logger.assert_called_once()
    ctx.followup.send.assert_awaited_once_with(
        "An error occurred while deleting messages.",
        ephemeral=True,
    )

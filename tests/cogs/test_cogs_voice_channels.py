from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from otc_bot.core.constants import ModRoles
from otc_bot.cogs import voice_channels as voice_module
from otc_bot.cogs.voice_channels import VoiceChannels


def make_voice_cog():
    return VoiceChannels(MagicMock())


def make_guild(*, categories=None, bot_member=None):
    guild = MagicMock()
    guild.name = "Test Server"
    guild.id = 300
    guild.categories = categories or []
    guild.me = bot_member if bot_member is not None else object()
    return guild


def make_category(
    name="LFBD",
    *,
    occupied=False,
):
    member = SimpleNamespace(id=700, name="ConnectedUser")
    channel = SimpleNamespace(
        name=f"{name} - GND",
        members=[member] if occupied else [],
        mention="#test-voice-channel",
    )

    return SimpleNamespace(
        name=name,
        voice_channels=[channel],
        channels=[channel],
    )


def make_member(*, role_ids=(), manage_messages=True):
    return SimpleNamespace(
        id=100,
        name="TestUser",
        roles=[
            SimpleNamespace(id=role_id)
            for role_id in role_ids
        ],
        guild_permissions=SimpleNamespace(
            manage_messages=manage_messages,
        ),
    )


@pytest.mark.asyncio
async def test_open_rejects_dm(make_context):
    cog = make_voice_cog()
    ctx = make_context(guild=None)

    await VoiceChannels.open.callback(
        cog,
        ctx,
        airport_code="LFBD",
        position="ALL",
    )

    ctx.respond.assert_awaited_once_with(
        "This command can only be used in a server.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_open_rejects_invalid_airport_code(make_context):
    cog = make_voice_cog()
    guild = make_guild()
    ctx = make_context(guild=guild)

    await VoiceChannels.open.callback(
        cog,
        ctx,
        airport_code="BAD",
        position="ALL",
    )

    ctx.respond.assert_awaited_once()
    assert "four letters" in ctx.respond.await_args.args[0]
    ctx.defer.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_rejects_missing_bot_permission(make_context):
    cog = make_voice_cog()
    guild = make_guild()
    ctx = make_context(guild=guild)

    ctx.channel.permissions_for.return_value = SimpleNamespace(
        manage_channels=False,
    )

    await VoiceChannels.open.callback(
        cog,
        ctx,
        airport_code="LFBD",
        position="ALL",
    )

    ctx.respond.assert_awaited_once_with(
        "I need the Manage Channels permission.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_open_calls_service_and_reports_channels(
    make_context,
    monkeypatch,
):
    cog = make_voice_cog()
    guild = make_guild()
    ctx = make_context(guild=guild)

    channels = [
        SimpleNamespace(mention="#ground"),
        SimpleNamespace(mention="#tower"),
    ]

    open_mock = AsyncMock(return_value=(channels, True))
    monkeypatch.setattr(
        voice_module,
        "open_airport_channels",
        open_mock,
    )

    await VoiceChannels.open.callback(
        cog,
        ctx,
        airport_code="lfbd",
        position="ALL",
    )

    open_mock.assert_awaited_once_with(
        guild,
        "LFBD",
        "ALL",
    )

    ctx.followup.send.assert_awaited_once()
    response = ctx.followup.send.await_args.args[0]

    assert "Created the airport category." in response
    assert "LFBD" in response
    assert "#ground" in response
    assert "#tower" in response


@pytest.mark.asyncio
async def test_close_rejects_dm(make_context):
    cog = make_voice_cog()
    ctx = make_context(guild=None)

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=False,
    )

    ctx.respond.assert_awaited_once_with(
        "This command can only be used in a server.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_close_reports_missing_category(make_context):
    cog = make_voice_cog()
    guild = make_guild(categories=[])
    ctx = make_context(guild=guild)

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=False,
    )

    ctx.followup.send.assert_awaited_once_with(
        "No airport category was found for **LFBD**.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_close_refuses_occupied_airport_without_force(
    make_context,
    monkeypatch,
):
    cog = make_voice_cog()
    category = make_category(occupied=True)
    guild = make_guild(categories=[category])
    ctx = make_context(guild=guild)

    close_mock = AsyncMock(return_value=(1, True))
    monkeypatch.setattr(
        voice_module,
        "close_airport_channels",
        close_mock,
    )

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=False,
    )

    response = ctx.followup.send.await_args.args[0]

    assert "Cannot close **LFBD**" in response
    assert "1 member(s)" in response
    close_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_regular_user_cannot_force_close(
    make_context,
    monkeypatch,
):
    cog = make_voice_cog()
    category = make_category(occupied=True)
    guild = make_guild(categories=[category])
    ctx = make_context(
        guild=guild,
        author=make_member(),
    )

    close_mock = AsyncMock(return_value=(1, True))
    monkeypatch.setattr(
        voice_module,
        "close_airport_channels",
        close_mock,
    )

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=True,
    )

    ctx.followup.send.assert_awaited_once_with(
        "You need a moderator role to force-close an airport.",
        ephemeral=True,
    )
    close_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_moderator_can_force_close_occupied_airport(
    make_context,
    monkeypatch,
):
    cog = make_voice_cog()
    category = make_category(occupied=True)
    guild = make_guild(categories=[category])

    moderator_role_id = next(iter(ModRoles)).value.id
    ctx = make_context(
        guild=guild,
        author=make_member(role_ids=[moderator_role_id]),
    )

    close_mock = AsyncMock(return_value=(1, True))
    monkeypatch.setattr(
        voice_module,
        "close_airport_channels",
        close_mock,
    )

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=True,
    )

    close_mock.assert_awaited_once_with(guild, "LFBD")

    response = ctx.followup.send.await_args.args[0]
    assert "Closed **1** voice channel(s)" in response
    assert "category was deleted" in response


@pytest.mark.asyncio
async def test_regular_user_can_close_empty_airport(
    make_context,
    monkeypatch,
):
    cog = make_voice_cog()
    category = make_category(occupied=False)
    guild = make_guild(categories=[category])
    ctx = make_context(
        guild=guild,
        author=make_member(),
    )

    close_mock = AsyncMock(return_value=(1, True))
    monkeypatch.setattr(
        voice_module,
        "close_airport_channels",
        close_mock,
    )

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=False,
    )

    close_mock.assert_awaited_once_with(guild, "LFBD")
    response = ctx.followup.send.await_args.args[0]
    assert "Closed **1** voice channel(s)" in response


@pytest.mark.asyncio
async def test_close_rejects_missing_bot_permission(make_context):
    cog = make_voice_cog()
    guild = make_guild()
    ctx = make_context(guild=guild)

    ctx.channel.permissions_for.return_value = SimpleNamespace(
        manage_channels=False,
    )

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=False,
    )

    ctx.respond.assert_awaited_once_with(
        "I need the Manage Channels permission.",
        ephemeral=True,
    )
    ctx.defer.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_rejects_missing_bot_member(make_context):
    cog = make_voice_cog()
    guild = make_guild(bot_member=None)
    guild.me = None
    ctx = make_context(guild=guild)

    await VoiceChannels.open.callback(
        cog,
        ctx,
        airport_code="LFBD",
        position="ALL",
    )

    ctx.respond.assert_awaited_once_with(
        "I need the Manage Channels permission.",
        ephemeral=True,
    )
    ctx.defer.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_rejects_invalid_airport_code(make_context):
    cog = make_voice_cog()
    ctx = make_context(guild=make_guild())

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="BAD",
        force=False,
    )

    ctx.respond.assert_awaited_once()
    assert "four letters" in ctx.respond.await_args.args[0]
    ctx.defer.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_reuses_category_with_no_channels(
        make_context,
        monkeypatch,
    ):
    cog = make_voice_cog()
    guild = make_guild()
    ctx = make_context(guild=guild)

    open_mock = AsyncMock(return_value=([], False))
    monkeypatch.setattr(
        voice_module,
        "open_airport_channels",
        open_mock,
    )

    await VoiceChannels.open.callback(
        cog,
        ctx,
        airport_code="LFBD",
        position="GND",
    )

    response = ctx.followup.send.await_args.args[0]

    assert "Reused the existing airport category." in response
    assert "LFBD" in response
    assert "Channels:\n" in response


@pytest.mark.asyncio
async def test_close_reports_no_managed_channels(
        make_context,
        monkeypatch,
    ):
    cog = make_voice_cog()
    guild = make_guild(categories=[make_category()])
    ctx = make_context(guild=guild)

    close_mock = AsyncMock(return_value=(0, False))
    monkeypatch.setattr(
        voice_module,
        "close_airport_channels",
        close_mock,
    )

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=False,
    )

    ctx.followup.send.assert_awaited_once_with(
        "No managed channels were found for **LFBD**.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_close_preserves_category_with_other_channels(
        make_context,
        monkeypatch,
    ):
    cog = make_voice_cog()
    guild = make_guild(categories=[make_category()])
    ctx = make_context(guild=guild)

    monkeypatch.setattr(
        voice_module,
        "close_airport_channels",
        AsyncMock(return_value=(1, False)),
    )

    await VoiceChannels.close.callback(
        cog,
        ctx,
        airport_code="LFBD",
        force=False,
    )

    response = ctx.followup.send.await_args.args[0]

    assert "Closed **1** voice channel(s)" in response
    assert "category was preserved" in response

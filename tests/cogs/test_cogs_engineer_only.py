from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from otc_bot.cogs import engineer_only as engineer_module
from otc_bot.cogs.engineer_only import EngineerOnly


def make_engineer_cog():
    bot = MagicMock()
    bot.user = SimpleNamespace(
        display_avatar=SimpleNamespace(
            url="https://example.com/bot.png",
        ),
    )

    return EngineerOnly(bot)


def make_member(
        *,
        role_ids=(100,),
        display_name="Test Engineer",
):
    return SimpleNamespace(
        id=200,
        name=display_name,
        display_name=display_name,
        roles=[
            SimpleNamespace(id=role_id)
            for role_id in role_ids
        ],
        display_avatar=SimpleNamespace(
            url="https://example.com/member.png",
        ),
    )


def make_context(
        *,
        guild=None,
        author=None,
):
    ctx = MagicMock()
    ctx.guild = guild
    ctx.author = author or make_member()
    ctx.respond = AsyncMock()

    return ctx


def make_guild(*, channel=None):
    guild = MagicMock()
    guild.name = "Test Server"
    guild.id = 300
    guild.get_channel.return_value = channel

    return guild


def make_announcement_channel():
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 400
    channel.name = "announcements"
    channel.send = AsyncMock()

    return channel


def configure_constants(monkeypatch):
    monkeypatch.setattr(
        engineer_module,
        "EngineerRoles",
        (
            SimpleNamespace(
                value=SimpleNamespace(id=100),
            ),
        ),
    )
    monkeypatch.setattr(
        engineer_module,
        "Channels",
        SimpleNamespace(
            ANNOUNCEMENT=SimpleNamespace(
                value=SimpleNamespace(id=400),
            ),
        ),
    )
    monkeypatch.setattr(
        engineer_module,
        "ANNOUNCEMENTS",
        {
            "bot-maint": {
                "title": "Bot Maintenance",
                "description": "Maintenance is starting.",
                "funny": "Time for a little nap.",
                "color": 0x123456,
            },
            "bot-up": {
                "title": "Bot Online",
                "description": "The bot is operational.",
                "funny": "Back from the void.",
                "color": 0x234567,
            },
            "bot-down": {
                "title": "Bot Offline",
                "description": "The bot is going offline.",
                "funny": "Logging off for now.",
                "color": 0x345678,
            },
            "bot-issue": {
                "title": "Bot Issue",
                "description": "An issue has been detected.",
                "funny": "Something went sideways.",
                "color": 0x456789,
            },
            "bot-update": {
                "title": "Bot Update",
                "description": "The bot has been updated.",
                "funny": "Freshly polished code.",
                "color": 0x567890,
            },
            "bot-test": {
                "title": "Test Announcement",
                "description": "This is a test.",
                "funny": "Testing, testing, 1, 2, 3.",
                "color": 0x678901,
            },
        },
    )


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


@pytest.mark.asyncio
async def test_announcement_rejects_dm(monkeypatch):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    ctx = make_context(guild=None)

    await cog._send_announcement(
        ctx,
        "bot-up",
        None,
    )

    ctx.respond.assert_awaited_once_with(
        "I can only make announcements from inside a server. "
        "I'm not that powerful... yet.",
        ephemeral=True,
    )
    cog.bot.user.display_avatar.__str__


@pytest.mark.asyncio
async def test_announcement_requires_engineer_role(monkeypatch):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    ctx = make_context(
        guild=make_guild(),
        author=make_member(role_ids=(999,)),
    )

    await cog._send_announcement(
        ctx,
        "bot-up",
        None,
    )

    ctx.respond.assert_awaited_once_with(
        "Access denied! Nice try, but you need the Engineer role.",
        ephemeral=True,
    )
    ctx.guild.get_channel.assert_not_called()


@pytest.mark.asyncio
async def test_announcement_accepts_engineer_role(monkeypatch):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    channel = make_announcement_channel()
    ctx = make_context(
        guild=make_guild(channel=channel),
        author=make_member(role_ids=(100, 999)),
    )

    await cog._send_announcement(
        ctx,
        "bot-up",
        None,
    )

    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_announcement_handles_missing_channel(
        monkeypatch,
):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    ctx = make_context(guild=make_guild(channel=None))

    warnings = []
    monkeypatch.setattr(
        engineer_module,
        "log_warning",
        lambda message, **kwargs: warnings.append(message),
    )

    await cog._send_announcement(
        ctx,
        "bot-up",
        None,
    )

    ctx.respond.assert_awaited_once_with(
        "I can't find the announcement channel. "
        "Have you tried turning the server off and on again?",
        ephemeral=True,
    )
    assert warnings


@pytest.mark.asyncio
async def test_announcement_rejects_non_text_channel(
        monkeypatch,
):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    channel = MagicMock(spec=discord.VoiceChannel)
    ctx = make_context(guild=make_guild(channel=channel))

    warnings = []
    monkeypatch.setattr(
        engineer_module,
        "log_warning",
        lambda message, **kwargs: warnings.append(message),
    )

    await cog._send_announcement(
        ctx,
        "bot-up",
        None,
    )

    ctx.respond.assert_awaited_once_with(
        "I can't find the announcement channel. "
        "Have you tried turning the server off and on again?",
        ephemeral=True,
    )
    assert warnings


@pytest.mark.asyncio
async def test_announcement_sends_expected_embed(
        monkeypatch,
):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    channel = make_announcement_channel()
    ctx = make_context(
        guild=make_guild(channel=channel),
        author=make_member(),
    )

    notices = []
    monkeypatch.setattr(
        engineer_module,
        "log_notice",
        lambda message, **kwargs: notices.append(message),
    )

    await cog._send_announcement(
        ctx,
        "bot-up",
        "  Everything is working!  ",
    )

    channel.send.assert_awaited_once()
    kwargs = channel.send.await_args.kwargs

    embed = kwargs["embed"]

    assert embed.title == "Bot Online"
    assert embed.description == "The bot is operational."
    assert embed.color.value == 0x234567
    assert embed.author.name == "OTCBot"
    assert embed.author.icon_url == "https://example.com/bot.png"
    assert embed.thumbnail.url == "https://example.com/bot.png"
    assert embed.footer.text == "Requested by Test Engineer"
    assert embed.footer.icon_url == "https://example.com/member.png"
    assert embed.timestamp is not None

    assert [
        (field.name, field.value, field.inline)
        for field in embed.fields
    ] == [
        (
            "Additional Information",
            "Everything is working!",
            False,
        ),
        (
            "OTCBot says",
            "*Back from the void.*",
            False,
        ),
    ]

    assert kwargs["allowed_mentions"].everyone is False
    assert kwargs["allowed_mentions"].users is False
    assert kwargs["allowed_mentions"].roles is False

    ctx.respond.assert_awaited_once_with(
        "Announcement sent to #announcements. "
        "My public-speaking career is thriving.",
        ephemeral=True,
    )
    assert notices


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message",
    [
        None,
        "",
        "   ",
    ],
)
async def test_announcement_omits_empty_additional_information(
        monkeypatch,
        message,
):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    channel = make_announcement_channel()
    ctx = make_context(guild=make_guild(channel=channel))

    await cog._send_announcement(
        ctx,
        "bot-test",
        message,
    )

    embed = channel.send.await_args.kwargs["embed"]

    assert len(embed.fields) == 1
    assert embed.fields[0].name == "OTCBot says"


@pytest.mark.asyncio
async def test_announcement_works_without_bot_user(
        monkeypatch,
):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    cog.bot.user = None

    channel = make_announcement_channel()
    ctx = make_context(guild=make_guild(channel=channel))

    await cog._send_announcement(
        ctx,
        "bot-test",
        None,
    )

    embed = channel.send.await_args.kwargs["embed"]

    assert embed.author is None
    assert embed.thumbnail is None
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_announcement_handles_forbidden_error(
        monkeypatch,
):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    channel = make_announcement_channel()
    channel.send.side_effect = make_discord_exception(
        discord.Forbidden,
        status=403,
        reason="Forbidden",
    )
    ctx = make_context(guild=make_guild(channel=channel))

    warnings = []
    monkeypatch.setattr(
        engineer_module,
        "log_warning",
        lambda message, **kwargs: warnings.append(message),
    )

    await cog._send_announcement(
        ctx,
        "bot-up",
        None,
    )

    ctx.respond.assert_awaited_once_with(
        "I can't post there! I need permission to send messages "
        "and embed links in the announcement channel.",
        ephemeral=True,
    )
    assert warnings


@pytest.mark.asyncio
async def test_announcement_handles_http_error(
        monkeypatch,
):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    channel = make_announcement_channel()
    channel.send.side_effect = make_discord_exception(
        discord.HTTPException,
        status=500,
        reason="Server error",
    )
    ctx = make_context(guild=make_guild(channel=channel))

    errors = []
    monkeypatch.setattr(
        engineer_module,
        "log_exception",
        lambda message, **kwargs: errors.append(message),
    )

    await cog._send_announcement(
        ctx,
        "bot-up",
        None,
    )

    ctx.respond.assert_awaited_once_with(
        "Discord refused my announcement. "
        "I'll take it personally.",
        ephemeral=True,
    )
    assert errors


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "command_name"),
    [
        ("announce_maint", "bot-maint"),
        ("announce_up", "bot-up"),
        ("announce_down", "bot-down"),
        ("announce_issue", "bot-issue"),
        ("announce_update", "bot-update"),
        ("announce_test", "bot-test"),
    ],
)
async def test_slash_commands_forward_correct_announcement(
        monkeypatch,
        method_name,
        command_name,
):
    configure_constants(monkeypatch)
    cog = make_engineer_cog()
    ctx = make_context(guild=make_guild())

    calls = []

    async def fake_send_announcement(
            context,
            name,
            message,
    ):
        calls.append((context, name, message))

    monkeypatch.setattr(
        cog,
        "_send_announcement",
        fake_send_announcement,
    )

    command = getattr(EngineerOnly, method_name)

    await command.callback(
        cog,
        ctx,
        "Extra details",
    )

    assert calls == [
        (ctx, command_name, "Extra details"),
    ]


def test_setup_adds_engineer_cog():
    bot = MagicMock()

    engineer_module.setup(bot)

    bot.add_cog.assert_called_once()
    assert isinstance(
        bot.add_cog.call_args.args[0],
        EngineerOnly,
    )

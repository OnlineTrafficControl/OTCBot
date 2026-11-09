import os
from datetime import UTC, datetime

import jardiscordengine as JDE

from otc_bot.constants import (
    ANNOUNCEMENTS,
    BOT_NAME,
)
from otc_bot.services.generic_helpers import (
    log_error,
    log_info,
)

webhook = None


def _get_announcement_webhook() -> JDE.Entities.JDEEntityWebhook | None:
    global webhook

    if webhook is not None:
        return webhook

    try:
        webhook_url = JDE.Systems.JDEEnv("WEBHOOK_ANNOUNCEMENT")

        if not webhook_url:
            log_error(
                "Announcement webhook configuration",
                "WEBHOOK_ANNOUNCEMENT is missing or empty.",
            )
            return None

        webhook = JDE.Entities.JDEEntityWebhook(webhook_url)

        log_info(
            "Announcement webhook configuration",
            "Webhook successfully initialized.",
        )

        return webhook

    except Exception as error:
        log_error(
            "Announcement webhook configuration",
            f"Failed to initialize webhook: {error}",
        )
        return None


async def _send_announcement(
        command_name: str,
        arguments: list[str],
    ) -> None:

    log_info(
        "Announcement command",
        f"Executing /{command_name} with {len(arguments)} argument(s).",
    )

    announcement_webhook = _get_announcement_webhook()

    if announcement_webhook is None:
        return

    announcement = ANNOUNCEMENTS[command_name]

    additional_message = " ".join(arguments).strip()

    embed = JDE.Entities.JDEEntityWebhookEmbed(
        title=str(announcement["title"]),
        description=str(announcement["description"]),
        color=int(announcement["color"]),
        timestamp=datetime.now(UTC),
    )

    if additional_message:
        embed.add_field(
            name="Additional Information",
            value=additional_message[:1024],
            inline=False,
        )

    embed.add_field(
        name=f"{BOT_NAME} says",
        value=f"*{announcement['funny']}*",
        inline=False,
    )

    embed.set_author(name=BOT_NAME)
    embed.set_footer(text="OTCBot Announcement")

    try:
        log_info(
            "Announcement delivery",
            f"Sending /{command_name} announcement.",
        )

        await announcement_webhook.send(
            embed=embed,
            allowed_mentions=JDE.Interns.Externs.DiscordExtern.AllowedMentions.none(),
        )

        log_info(
            "Announcement sent",
            f"Successfully sent /{command_name} announcement.",
        )

    except Exception as error:
        log_error(
            "Announcement delivery failed",
            f"Failed to send /{command_name} announcement: {error}",
        )

@JDE.Terminals.terminal_command(
    ".maint",
    "Announces the start of bot maintenance.",
    ("message", "Optional additional announcement text."),
)
async def announce_maint(arguments: list[str]) -> None:

    await _send_announcement(
        "maint",
        arguments,
    )

@JDE.Terminals.terminal_command(
    ".up",
    "Announces that the bot is operational.",
    ("message", "Optional additional announcement text."),
)
async def announce_up(arguments: list[str]) -> None:

    await _send_announcement(
        "up",
        arguments,
    )

@JDE.Terminals.terminal_command(
    ".down",
    "Announces that the bot is going offline.",
    ("message", "Optional additional announcement text."),
)
async def announce_down(arguments: list[str]) -> None:

    await _send_announcement(
        "down",
        arguments,
    )

@JDE.Terminals.terminal_command(
    ".issue",
    "Announces a bot issue.",
    ("message", "Optional additional announcement text."),
)
async def announce_issue(arguments: list[str]) -> None:

    await _send_announcement(
        "issue",
        arguments,
    )

@JDE.Terminals.terminal_command(
    ".update",
    "Announces a bot update.",
    ("message", "Optional additional announcement text."),
)
async def announce_update(arguments: list[str]) -> None:

    await _send_announcement(
        "update",
        arguments,
    )

@JDE.Terminals.terminal_command(
    ".test",
    "Sends a test announcement.",
    ("message", "Optional additional announcement text."),
)
async def announce_test(arguments: list[str]) -> None:

    await _send_announcement(
        "test",
        arguments,
    )

def register_terminal_commands(terminal: JDE.Terminals.JDETerminal):
    terminal.register_commands(
        announce_maint,
        announce_up,
        announce_down,
        announce_issue,
        announce_update,
        announce_test,
    )

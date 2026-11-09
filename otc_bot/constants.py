import re
from typing import Final

BOT_NAME: Final[str] = "OTCBot"

AIRPORT_ICAO_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z0-9]{4}$"
)

AIRPORT_CHANNEL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^([A-Z0-9]{4})\s+-\s+(GND|TWR|DEP|APP|CTR)$",
    re.IGNORECASE,
)

AIRPORT_POSITIONS: Final[tuple[str, ...]] = (
    "GND",
    "TWR",
    "DEP",
    "APP",
    "CTR",
)

ALL_POSITION: Final[str] = "ALL"

AIRPORT_CATEGORY_SUFFIX: Final[str] = " Airport"

ANNOUNCEMENTS: Final[dict[str, dict[str, str | int]]] = {
    "maint": {
        "title": "Scheduled Maintenance",
        "description": "OTCBot is going into maintenance mode.",
        "funny": "I'm off to the workshop. Please don't feed the hamsters.",
        "color": 0xF1C40F,
    },
    "up": {
        "title": "All Systems Operational",
        "description": "OTCBot is online and ready for duty.",
        "funny": "I'm awake! Did you miss me?",
        "color": 0x2ECC71,
    },
    "down": {
        "title": "Bot Going Offline",
        "description": "OTCBot is shutting down for now.",
        "funny": "I'm going to sleep. Don't let the servers eat my homework.",
        "color": 0xE74C3C,
    },
    "issue": {
        "title": "Technical Difficulties",
        "description": "OTCBot is experiencing an issue.",
        "funny": "Something is on fire. Probably just a metaphor. Hopefully.",
        "color": 0xE67E22,
    },
    "update": {
        "title": "Bot Updated",
        "description": "OTCBot has received an update.",
        "funny": "New tricks installed. Same questionable personality.",
        "color": 0x3498DB,
    },
    "test": {
        "title": "Test Announcement",
        "description": "This is a test announcement from OTCBot.",
        "funny": "Testing, testing... Is this thing on?",
        "color": 0x9B59B6,
    },
}

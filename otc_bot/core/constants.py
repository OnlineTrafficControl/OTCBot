##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# core.constants #


from enum import Enum, StrEnum

from otc_bot.core.models import Server, Role, Owner, Category, Seconds, Channel
from otc_bot.core.env import get_env_id, get_env


class Servers(Enum):
    OTC = Server(
        id = get_env_id("OTC_SERVER_ID"),
        name = "online traffic control"
    )
    TEST = Server(
        id = get_env_id("TEST_SERVER_ID"),
        name = "test server"
    )


class ModRoles(Enum):
    OWNER = Role(
        id = get_env_id("OWNER_ROLE_ID"),
        name = "Owner"
    )
    CO_OWNER = Role(
        id = get_env_id("CO_OWNER_ROLE_ID"),
        name = "co-owner"
    )
    EXEC_ADMIN = Role(
        id = get_env_id("EXEC_ADMIN_ROLE_ID"),
        name = "executive administrator"
    )
    ADMIN = Role(
        id = get_env_id("ADMIN_ROLE_ID"),
        name = "administrator"
    )
    EXEC_MOD = Role(
        id = get_env_id("EXEC_MOD_ROLE_ID"),
        name = "executive moderator"
    )
    MOD = Role(
        id = get_env_id("MOD_ROLE_ID"),
        name = "moderator"
    )


class EngineerRoles(Enum):
    ENGINEER = Role(
        id = get_env_id("ENGINEER_ROLE_ID"),
        name = "engineer"
    )


class Owners(Enum):
    OWNER = Owner(
        id = get_env_id("OWNER_USER_ID")
    )


class Categories(Enum):
    TICKETS = Category(
        id = get_env_id("TICKET_CATEGORY_ID"),
        name = "tickets"
    )


class Channels(Enum):
    TICKET = Channel(
        id = get_env_id("TICKET_CHANNEL_ID"),
        name = "ticket",
        category = Categories.TICKETS.value,
        type = "TEXT"
    )
    ANNOUNCEMENT = Channel(
        id = get_env_id("ANNOUNCEMENT_CHANNEL_ID"),
        name = "announcement",
        category = None,
        type = "ANNOUNCEMENT"
    )
    AIRPORT_STATUS = Channel(
        id = get_env_id("AIRPORT_STATUS_CHANNEL_ID"),
        name = "airport-status",
        category = None,
        type = "TEXT"
    )


class AirportPositions(StrEnum):
    GROUND = "GND"
    TOWER = "TWR"
    DEPARTURE = "DEP"
    APPROACH = "APP"
    CENTER = "CTR"


ALL_AIRPORT_POSITIONS = tuple(AirportPositions)

BOT_TOKEN = get_env("OTC_BOT_TOKEN")

AIRPORT_CATEGORY_NAME_FORMAT: str = "{airport_code}"
AIRPORT_VOICE_CHANNEL_NAME_FORMAT: str = "{airport_code} - {position}"

SERVER_IDS: tuple[int, ...] = tuple(
    server.value.id
    for server in Servers
)

INACTIVE_CHANNEL_CHECK_INTERVAL: Seconds = Seconds(300)
INACTIVE_CHANNEL_DELETION_THRESHOLD: Seconds = Seconds(7200)

TICKET_FIRST_MESSAGE: str = "Please describe your issue below and a member of the mod team will respond asap!"

GREETINGS: tuple[str, ...] = (
    "hi",
    "hello",
    "hey",
    "hiya",
    "heya",
    "howdy",
    "hallo",
    "bonjour",
)
ANNOUNCEMENTS: dict[str, dict[str, str | int]] = {
    "bot-maint": {
        "title": "Scheduled Maintenance",
        "description": "OTCBot is going into maintenance mode.",
        "funny": "I'm off to the workshop. Please don't feed the hamsters.",
        "color": 0xF1C40F,
    },
    "bot-up": {
        "title": "All Systems Operational",
        "description": "OTCBot is online and ready for duty.",
        "funny": "I'm awake! Did you miss me?",
        "color": 0x2ECC71,
    },
    "bot-down": {
        "title": "Bot Going Offline",
        "description": "OTCBot is shutting down for now.",
        "funny": "I'm going to sleep. Don't let the servers eat my homework.",
        "color": 0xE74C3C,
    },
    "bot-issue": {
        "title": "Technical Difficulties",
        "description": "OTCBot is experiencing an issue.",
        "funny": "Something is on fire. Probably just a metaphor. Hopefully.",
        "color": 0xE67E22,
    },
    "bot-update": {
        "title": "Bot Updated",
        "description": "OTCBot has received an update.",
        "funny": "New tricks installed. Same questionable personality.",
        "color": 0x3498DB,
    },
    "bot-test": {
        "title": "Test Announcement",
        "description": "This is a test announcement from OTCBot.",
        "funny": "Testing, testing... Is this thing on?",
        "color": 0x9B59B6,
    },
}
BOT_LOGO_URL: str = "https://cdn.discordapp.com/icons/1426009085991588002/a661e87ddd2c439eb28b19a2fc5ccd5e.jpg"


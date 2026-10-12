##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# core.constants #


from dotenv import load_dotenv
from enum import Enum, StrEnum

from otc_bot.core.models import Server, Role, Owner, Category, Seconds
from otc_bot.services.env import get_env_id, get_env


load_dotenv()


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


class Owners(Enum):
    OWNER = Owner(
        id = get_env_id("OWNER_USER_ID")
    )


class Categories(Enum):
    TICKETS = Category(
        id = get_env_id("TICKET_CATEGORY_ID"),
        name = get_env("TICKET_CATEGORY_NAME")
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

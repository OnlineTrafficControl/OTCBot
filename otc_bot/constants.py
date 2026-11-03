import re
from typing import Final

BOT_NAME: Final[str] = "OTCBot"

AIRPORT_ICAO_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z0-9]{4}$"
)

AIRPORT_CHANNEL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^([A-Z0-9]{4})-(GND|TWR|DEP|APP|CTR)$",
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

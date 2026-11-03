from dataclasses import dataclass, field
from typing import Any


@dataclass
class AirportResources:

    guild_id: int
    icao: str
    category: Any | None = None
    channels: list[Any] = field(default_factory=list)

OPEN_AIRPORTS: dict[tuple[int, str], AirportResources] = {}

TRACKED_CATEGORIES: list[Any] = []
TRACKED_CHANNELS: list[Any] = []

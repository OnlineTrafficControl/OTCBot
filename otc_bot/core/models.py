##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# core.models #


from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True, slots=True)
class Server:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Role:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Owner:
    id: int


@dataclass(frozen=True, slots=True)
class Category:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Channel:
    id: int
    name: str
    category: Optional[Category]
    type: Literal["TEXT", "VOICE"]


@dataclass(frozen=True, slots=True)
class Seconds:
    sec: float | int

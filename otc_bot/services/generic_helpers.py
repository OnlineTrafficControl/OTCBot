import shutil
from pathlib import Path

import jardiscordengine as JDE

from otc_bot.constants import (
    AIRPORT_CATEGORY_SUFFIX,
    AIRPORT_ICAO_PATTERN,
    AIRPORT_POSITIONS,
    ALL_POSITION,
)


def log_info(title: str, description: str) -> None:
    JDE.Interns.Logs.log("INFO", title, description)

def log_warning(title: str, description: str) -> None:
    JDE.Interns.Logs.log("WARN", title, description)

def log_error(title: str, description: str) -> None:
    JDE.Interns.Logs.log("ERROR", title, description)

def normalize_icao(value: str) -> str:
    icao = value.strip().upper()

    if not AIRPORT_ICAO_PATTERN.fullmatch(icao):
        raise ValueError(
            "The airport must be a four-character ICAO code "
            "containing only letters or digits."
        )

    return icao

def get_positions(position: str) -> tuple[str, ...]:
    normalized = position.strip().upper()

    if normalized == ALL_POSITION:
        return AIRPORT_POSITIONS

    if normalized not in AIRPORT_POSITIONS:
        raise ValueError(
            "Invalid position. Choose GND, TWR, DEP, APP, CTR, or ALL."
        )

    return (normalized,)

def airport_category_name(icao: str) -> str:
    return f"{icao}{AIRPORT_CATEGORY_SUFFIX}"

def airport_channel_name(icao: str, position: str) -> str:
    return f"{icao.lower()}-{position.lower()}"

def move_logs(jde_log_directory: Path, log_directory: Path):
    log_directory.mkdir(parents=True, exist_ok=True)

    if jde_log_directory.is_dir():
        for log_file in jde_log_directory.glob("*.jar-log"):
            shutil.move(
                str(log_file),
                str(log_directory / log_file.name),
            )

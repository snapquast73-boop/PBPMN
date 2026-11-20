"""Verified official MLB play-by-play archive and plain-text formatter.

The package talks to exactly one host, ``statsapi.mlb.com``, over HTTPS, and accepts a
response only when it is successful JSON that carries MLB Advanced Media's provenance
notice. It never invents, estimates or repairs a value.
"""

from .client import (
    COPYRIGHT_MARKER,
    GAME_TYPES,
    MIN_DATE,
    OFFICIAL_HOST,
    OFFICIAL_ORIGIN,
    SPORT_ID,
    MLBClient,
    OfficialDataError,
    OfficialResponse,
    game_url,
    qualifying_games,
    schedule_url,
)

__version__ = "1.0.0"

__all__ = [
    "COPYRIGHT_MARKER",
    "GAME_TYPES",
    "MIN_DATE",
    "OFFICIAL_HOST",
    "OFFICIAL_ORIGIN",
    "SPORT_ID",
    "MLBClient",
    "OfficialDataError",
    "OfficialResponse",
    "game_url",
    "qualifying_games",
    "schedule_url",
    "__version__",
]

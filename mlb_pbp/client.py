"""Official-host client: allowlist, retries, throttling and response validation.

Requests used (verified live against the official API; see COORDINATION.md §4):

    GET https://statsapi.mlb.com/api/v1/schedule
        ?sportId=1&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&gameTypes=R,F,D,L,W&hydrate=linescore
    GET https://statsapi.mlb.com/api/v1.1/game/{gamePk}/feed/live

A response is accepted only if:

1. the URL is HTTPS on the exact host ``statsapi.mlb.com``;
2. the response is successful JSON;
3. it carries MLB Advanced Media's provenance notice; and
4. a game feed's returned ``gamePk`` matches the requested ``gamePk``.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

OFFICIAL_ORIGIN = "https://statsapi.mlb.com"
OFFICIAL_HOST = "statsapi.mlb.com"
COPYRIGHT_MARKER = "MLB Advanced Media, L.P."
SPORT_ID = 1
GAME_TYPES: tuple[str, ...] = ("R", "F", "D", "L", "W")
MIN_DATE = date(2014, 1, 1)
USER_AGENT = "mlb-pbp/1.0 (+https://github.com/snapquast73-boop/PBPMN)"
RETRIABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class OfficialDataError(RuntimeError):
    """Raised when a response may not be used as official data."""

    def __init__(self, code: str, message: str, url: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.url = url


@dataclass(frozen=True)
class OfficialResponse:
    """One accepted official response, with the exact bytes that were accepted."""

    url: str
    text: str
    json: Mapping[str, Any]
    copyright: str
    fetched_at: str
    sha256: str

    def raw_bytes(self, compress: bool = False) -> bytes:
        """The exact response body, optionally gzip-compressed without changing its content."""
        body = self.text.encode("utf-8")
        return gzip.compress(body, mtime=0) if compress else body

    @property
    def meta(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "fetchedAt": self.fetched_at,
            "sha256": self.sha256,
            "copyright": self.copyright,
        }


def _iso(day: date) -> str:
    return day.isoformat()


def schedule_url(start: date, end: date) -> str:
    """Official schedule URL for an inclusive date range."""
    if end < start:
        raise ValueError("end date precedes start date")
    query = urllib.parse.urlencode(
        {
            "sportId": SPORT_ID,
            "startDate": _iso(start),
            "endDate": _iso(end),
            "gameTypes": ",".join(GAME_TYPES),
            "hydrate": "linescore",
        }
    )
    return f"{OFFICIAL_ORIGIN}/api/v1/schedule?{query}"


def game_url(game_pk: int | str) -> str:
    """Official live-feed URL for one game."""
    text = str(game_pk)
    if not text.isdigit():
        raise OfficialDataError("BAD_GAMEPK", f"gamePk must be numeric: {text!r}")
    return f"{OFFICIAL_ORIGIN}/api/v1.1/game/{text}/feed/live"


def assert_official_url(url: str) -> urllib.parse.SplitResult:
    """Reject anything that is not HTTPS on the exact official host."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https":
        raise OfficialDataError("OFFICIAL_HOST", f"Only HTTPS is permitted: {url}", url)
    if parts.hostname != OFFICIAL_HOST:
        raise OfficialDataError("OFFICIAL_HOST", f"Only {OFFICIAL_HOST} is permitted: {url}", url)
    return parts


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def qualifying_games(schedule: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Flatten ``dates[].games[]`` and keep only the documented game types."""
    games: list[Mapping[str, Any]] = []
    for day in schedule.get("dates") or []:
        for game in day.get("games") or []:
            if game.get("gameType") in GAME_TYPES:
                games.append(game)
    return games


class MLBClient:
    """Throttled, retrying client restricted to the official host."""

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        retries: int = 4,
        request_delay: float = 0.2,
        opener: Callable[..., Any] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.timeout = timeout
        self.retries = max(0, retries)
        self.request_delay = max(0.0, request_delay)
        self._opener = opener or urllib.request.urlopen
        self._sleep = sleep
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._last_request = 0.0
        self.request_count = 0

    # -- transport ---------------------------------------------------------

    def _throttle(self) -> None:
        if self.request_delay <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        remaining = self.request_delay - elapsed
        if remaining > 0:
            self._sleep(remaining)

    def _get_bytes(self, url: str) -> bytes:
        assert_official_url(url)
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )
        attempt = 0
        while True:
            attempt += 1
            self._throttle()
            try:
                with self._opener(request, timeout=self.timeout) as response:
                    status = getattr(response, "status", 200)
                    if status and status >= 400:
                        raise OfficialDataError("HTTP", f"Official endpoint returned HTTP {status}: {url}", url)
                    self._last_request = time.monotonic()
                    self.request_count += 1
                    return response.read()
            except urllib.error.HTTPError as error:
                self._last_request = time.monotonic()
                if error.code in RETRIABLE_STATUS and attempt <= self.retries:
                    self._backoff(attempt)
                    continue
                raise OfficialDataError(
                    "HTTP", f"Official endpoint returned HTTP {error.code}: {url}", url
                ) from error
            except (urllib.error.URLError, socket.timeout, TimeoutError) as error:
                self._last_request = time.monotonic()
                if attempt <= self.retries:
                    self._backoff(attempt)
                    continue
                raise OfficialDataError(
                    "NETWORK", f"Official endpoint could not be reached: {url} ({error})", url
                ) from error

    def _backoff(self, attempt: int) -> None:
        self._sleep(min(8.0, 0.5 * (2 ** (attempt - 1))))

    # -- accepted responses ------------------------------------------------

    def get(self, url: str) -> OfficialResponse:
        """Fetch and validate one official URL."""
        body = self._get_bytes(url)
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as error:
            raise OfficialDataError("JSON", f"Response was not UTF-8: {url}", url) from error
        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            raise OfficialDataError("JSON", f"Response was not JSON: {url}", url) from error
        if not isinstance(document, Mapping):
            raise OfficialDataError("JSON", f"Response was not a JSON object: {url}", url)
        notice = document.get("copyright")
        if not isinstance(notice, str) or COPYRIGHT_MARKER not in notice:
            raise OfficialDataError(
                "COPYRIGHT",
                f"Response does not carry the MLB Advanced Media notice: {url}",
                url,
            )
        return OfficialResponse(
            url=url,
            text=text,
            json=document,
            copyright=notice,
            fetched_at=self._clock().strftime("%Y-%m-%dT%H:%M:%SZ"),
            sha256=sha256_hex(body),
        )

    def schedule(self, start: date, end: date) -> OfficialResponse:
        """Official schedule response for an inclusive range, validated."""
        response = self.get(schedule_url(start, end))
        if not isinstance(response.json.get("dates"), list):
            raise OfficialDataError("SCHEMA", "Schedule response has no dates[] array", response.url)
        return response

    def game(self, game_pk: int | str) -> OfficialResponse:
        """Official live feed for one game, with the gamePk identity check."""
        response = self.get(game_url(game_pk))
        returned = response.json.get("gamePk")
        if str(returned) != str(game_pk):
            raise OfficialDataError(
                "GAMEPK",
                f"Feed returned gamePk {returned!r} but {game_pk!r} was requested: {response.url}",
                response.url,
            )
        game_data = response.json.get("gameData") or {}
        declared = (game_data.get("game") or {}).get("pk")
        if declared is not None and str(declared) != str(game_pk):
            raise OfficialDataError(
                "GAMEPK",
                f"Feed declared gameData.game.pk {declared!r} but {game_pk!r} was requested",
                response.url,
            )
        if "gameData" not in response.json or "liveData" not in response.json:
            raise OfficialDataError("SCHEMA", "Feed has no gameData/liveData", response.url)
        return response


def iter_games(
    client: MLBClient,
    start: date,
    end: date,
    *,
    windows: Sequence[tuple[date, date]] | None = None,
    logger: Callable[[str], None] | None = None,
) -> Iterator[Mapping[str, Any]]:
    """Yield every qualifying official game in a range, window by window."""
    log = logger or (lambda message: None)
    for window_start, window_end in windows or [(start, end)]:
        response = client.schedule(window_start, window_end)
        games = qualifying_games(response.json)
        log(f"schedule {window_start}..{window_end}: {len(games)} qualifying game(s)")
        for game in games:
            yield game

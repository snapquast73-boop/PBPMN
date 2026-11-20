"""Discovery, resume, storage, manifests and verification for the bulk archive.

Layout produced under ``--output``::

    archive/
    ├── manifest.ndjson
    ├── errors.ndjson                         # only present when something failed
    ├── schedules/
    │   ├── manifest.ndjson
    │   └── 2026-08-01_2026-08-11.json.gz     # exact schedule response
    ├── games/2026/08/05/824646.txt           # readable report
    ├── raw/2026/08/05/824646.json.gz         # complete official response
    └── events/2026/08/05/824646.ndjson       # streaming records

Every manifest record keeps the official URL, the response notice, the retrieval time and
the SHA-256 of the exact response body, so a stored file can be re-checked later.
"""

from __future__ import annotations

import calendar
import gzip
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

from .client import (
    GAME_TYPES,
    MIN_DATE,
    MLBClient,
    OfficialDataError,
    OfficialResponse,
    qualifying_games,
)
from .formatter import format_events_ndjson, format_plain_text

MANIFEST_NAME = "manifest.ndjson"
ERRORS_NAME = "errors.ndjson"
SCHEDULE_DIR = "schedules"
FORMATS: tuple[str, ...] = ("text", "raw", "events")
MEDIA_TYPES = {
    "text": "text/plain; charset=utf-8",
    "raw": "application/json",
    "events": "application/x-ndjson",
}


# ---------------------------------------------------------------- helpers


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def month_windows(start: date, end: date) -> list[tuple[date, date]]:
    """Split an inclusive range into calendar-month windows."""
    if end < start:
        raise ValueError("end date precedes start date")
    windows: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        last_day = calendar.monthrange(cursor.year, cursor.month)[1]
        month_end = date(cursor.year, cursor.month, last_day)
        windows.append((cursor, min(month_end, end)))
        cursor = month_end + timedelta(days=1)
    return windows


def default_end(today: date | None = None) -> date:
    return today or datetime.now(timezone.utc).date()


@dataclass
class ArchiveConfig:
    """Everything that makes a run reproducible."""

    output: Path
    start: date = MIN_DATE
    end: date | None = None
    formats: Sequence[str] = FORMATS
    workers: int = 2
    request_delay: float = 0.2
    refresh: bool = False
    gzip_raw: bool = True
    limit: int | None = None

    def __post_init__(self) -> None:
        self.output = Path(self.output)
        unknown = [name for name in self.formats if name not in FORMATS]
        if unknown:
            raise ValueError(f"unknown format(s): {', '.join(unknown)}")
        self.formats = tuple(self.formats)
        self.workers = max(1, int(self.workers))

    @property
    def effective_end(self) -> date:
        return self.end or default_end()


# ---------------------------------------------------------------- manifest


def _append_ndjson(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n")


def read_manifest(path: Path) -> dict[str, dict[str, Any]]:
    """Read a manifest keyed by gamePk; malformed lines are ignored, not repaired."""
    records: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, Mapping) and record.get("gamePk") is not None:
                records[str(record["gamePk"])] = dict(record)
    return records


def write_manifest(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(dict(record), ensure_ascii=False, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


# ---------------------------------------------------------------- paths


def game_paths(root: Path, official_date: str, game_pk: Any, formats: Sequence[str], gzip_raw: bool) -> dict[str, Path]:
    try:
        day = date.fromisoformat(official_date)
    except (TypeError, ValueError):
        day = date(1970, 1, 1)
    base = Path(f"{day.year:04d}") / f"{day.month:02d}" / f"{day.day:02d}"
    paths: dict[str, Path] = {}
    if "text" in formats:
        paths["text"] = root / "games" / base / f"{game_pk}.txt"
    if "raw" in formats:
        suffix = ".json.gz" if gzip_raw else ".json"
        paths["raw"] = root / "raw" / base / f"{game_pk}{suffix}"
    if "events" in formats:
        paths["events"] = root / "events" / base / f"{game_pk}.ndjson"
    return paths


def _write_bytes(path: Path, body: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return sha256_hex(body)


# ---------------------------------------------------------------- one game


def archive_game(client: MLBClient, game: Mapping[str, Any], config: ArchiveConfig) -> dict[str, Any]:
    """Fetch one official game and store every requested representation."""
    game_pk = game.get("gamePk")
    response: OfficialResponse = client.game(game_pk)
    feed = response.json
    official_date = (
        str(game.get("officialDate"))
        or str((feed.get("gameData") or {}).get("datetime", {}).get("officialDate"))
    )
    meta = response.meta

    record: dict[str, Any] = {
        "gamePk": str(game_pk),
        "officialDate": official_date,
        "season": (game.get("season") or str(official_date)[:4]),
        "gameType": game.get("gameType"),
        "status": ((game.get("status") or {}).get("detailedState")),
        "away": {
            "id": ((game.get("teams") or {}).get("away") or {}).get("team", {}).get("id"),
            "name": ((game.get("teams") or {}).get("away") or {}).get("team", {}).get("name"),
            "score": ((game.get("teams") or {}).get("away") or {}).get("score"),
        },
        "home": {
            "id": ((game.get("teams") or {}).get("home") or {}).get("team", {}).get("id"),
            "name": ((game.get("teams") or {}).get("home") or {}).get("team", {}).get("name"),
            "score": ((game.get("teams") or {}).get("home") or {}).get("score"),
        },
        "sourceUrl": response.url,
        "notice": response.copyright,
        "retrievedAt": response.fetched_at,
        "sourceSha256": response.sha256,
        "files": [],
    }

    paths = game_paths(config.output, official_date, game_pk, config.formats, config.gzip_raw)
    for name, path in paths.items():
        if name == "raw":
            body = response.raw_bytes(compress=config.gzip_raw)
            digest = _write_bytes(path, body)
            record["files"].append(
                {
                    "path": str(path.relative_to(config.output)),
                    "mediaType": MEDIA_TYPES["raw"],
                    "encoding": "gzip" if config.gzip_raw else "identity",
                    "sha256": digest,
                }
            )
        elif name == "text":
            body = format_plain_text(feed, meta).encode("utf-8")
            digest = _write_bytes(path, body)
            record["files"].append(
                {
                    "path": str(path.relative_to(config.output)),
                    "mediaType": MEDIA_TYPES["text"],
                    "encoding": "identity",
                    "sha256": digest,
                }
            )
        elif name == "events":
            body = format_events_ndjson(feed, meta).encode("utf-8")
            digest = _write_bytes(path, body)
            record["files"].append(
                {
                    "path": str(path.relative_to(config.output)),
                    "mediaType": MEDIA_TYPES["events"],
                    "encoding": "identity",
                    "sha256": digest,
                }
            )
    return record


# ---------------------------------------------------------------- run


@dataclass
class ArchiveSummary:
    discovered: int = 0
    archived: int = 0
    skipped: int = 0
    failed: int = 0
    failures: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "discovered": self.discovered,
            "archived": self.archived,
            "skipped": self.skipped,
            "failed": self.failed,
        }


def run_archive(
    config: ArchiveConfig,
    *,
    client: MLBClient | None = None,
    logger: Callable[[str], None] = print,
) -> ArchiveSummary:
    """Enumerate every qualifying game in the range and archive each one."""
    client = client or MLBClient(request_delay=config.request_delay)
    root = config.output
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / MANIFEST_NAME
    errors_path = root / ERRORS_NAME
    existing = read_manifest(manifest_path)
    summary = ArchiveSummary()

    end = config.effective_end
    if end < config.start:
        raise ValueError("end date precedes start date")

    discovered: list[Mapping[str, Any]] = []
    for window_start, window_end in month_windows(config.start, end):
        try:
            response = client.schedule(window_start, window_end)
        except OfficialDataError as error:
            summary.failed += 1
            summary.failures.append({"url": error.url, "code": error.code, "message": str(error)})
            _append_ndjson(errors_path, {"at": utc_now(), "code": error.code, "message": str(error), "url": error.url})
            logger(f"error: {error}")
            continue
        games = qualifying_games(response.json)
        logger(f"schedule {window_start}..{window_end}: {len(games)} qualifying game(s)")
        schedule_rel = Path(SCHEDULE_DIR) / f"{window_start.isoformat()}_{window_end.isoformat()}.json.gz"
        schedule_path = root / schedule_rel
        body = gzip.compress(response.text.encode("utf-8"), mtime=0)
        digest = _write_bytes(schedule_path, body)
        _append_ndjson(
            root / SCHEDULE_DIR / "manifest.ndjson",
            {
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
                "url": response.url,
                "fetchedAt": response.fetched_at,
                "sourceSha256": response.sha256,
                "path": str(schedule_rel),
                "fileSha256": digest,
                "encoding": "gzip",
                "games": len(games),
            },
        )
        discovered.extend(games)

    summary.discovered = len(discovered)
    if config.limit is not None:
        discovered = discovered[: config.limit]

    pending: list[Mapping[str, Any]] = []
    for game in discovered:
        key = str(game.get("gamePk"))
        if not config.refresh and key in existing:
            summary.skipped += 1
            continue
        pending.append(game)

    def work(game: Mapping[str, Any]) -> dict[str, Any]:
        return archive_game(client, game, config)

    if config.workers == 1:
        for game in pending:
            try:
                record = work(game)
            except OfficialDataError as error:
                summary.failed += 1
                summary.failures.append({"gamePk": game.get("gamePk"), "code": error.code, "message": str(error)})
                _append_ndjson(
                    errors_path,
                    {"at": utc_now(), "gamePk": game.get("gamePk"), "code": error.code, "message": str(error), "url": error.url},
                )
                logger(f"error gamePk={game.get('gamePk')}: {error}")
                continue
            existing[str(record["gamePk"])] = record
            summary.archived += 1
            _append_ndjson(manifest_path, record)
    else:
        worker_client = MLBClient(request_delay=config.request_delay)
        with ThreadPoolExecutor(max_workers=config.workers) as pool:
            futures = {pool.submit(archive_game, worker_client, game, config): game for game in pending}
            for future in as_completed(futures):
                game = futures[future]
                try:
                    record = future.result()
                except OfficialDataError as error:
                    summary.failed += 1
                    summary.failures.append({"gamePk": game.get("gamePk"), "code": error.code, "message": str(error)})
                    _append_ndjson(
                        errors_path,
                        {"at": utc_now(), "gamePk": game.get("gamePk"), "code": error.code, "message": str(error), "url": error.url},
                    )
                    logger(f"error gamePk={game.get('gamePk')}: {error}")
                    continue
                existing[str(record["gamePk"])] = record
                summary.archived += 1
                _append_ndjson(manifest_path, record)

    logger(
        f"done: discovered={summary.discovered} archived={summary.archived} "
        f"skipped={summary.skipped} failed={summary.failed}"
    )
    return summary


# ---------------------------------------------------------------- verification


@dataclass
class VerifyReport:
    records: int = 0
    files_checked: int = 0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def as_dict(self) -> dict[str, Any]:
        return {"records": self.records, "filesChecked": self.files_checked, "problems": self.problems, "ok": self.ok}


def _decompress(path: Path) -> bytes:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as handle:
            return handle.read()
    return path.read_bytes()


def verify_archive(root: Path) -> VerifyReport:
    """Check every stored digest, and each raw body against the source digest."""
    root = Path(root)
    report = VerifyReport()
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.exists():
        report.problems.append(f"manifest not found: {manifest_path}")
        return report

    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                report.problems.append(f"{MANIFEST_NAME}:{line_number}: not JSON")
                continue
            report.records += 1
            for entry in record.get("files") or []:
                path = root / str(entry.get("path"))
                if not path.exists():
                    report.problems.append(f"missing file: {entry.get('path')}")
                    continue
                digest = sha256_hex(path.read_bytes())
                if digest != entry.get("sha256"):
                    report.problems.append(f"digest mismatch: {entry.get('path')}")
                report.files_checked += 1
                if entry.get("mediaType") == MEDIA_TYPES["raw"]:
                    source_digest = record.get("sourceSha256")
                    if source_digest and sha256_hex(_decompress(path)) != source_digest:
                        report.problems.append(
                            f"source digest mismatch: {entry.get('path')} (stored body differs from retrieval)"
                        )
    return report

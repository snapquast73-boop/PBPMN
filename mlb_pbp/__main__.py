"""Command line entry point: ``python -m mlb_pbp`` / ``mlb-pbp``.

    mlb-pbp game 746865 --format text --output 746865.txt
    mlb-pbp game 746865 --format raw --output 746865.json
    mlb-pbp game 746865 --format events --output 746865.events.ndjson
    mlb-pbp archive --start 2014-01-01 --end 2026-08-11 --output archive \\
                    --formats text,raw,events --workers 2 --request-delay 0.2
    mlb-pbp verify archive

For compatibility with older notes the archive flags may be given without the ``archive``
subcommand, e.g. ``python -m mlb_pbp --start 2014-01-01 --end 2026-08-11``.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

from . import __version__
from .archive import FORMATS, ArchiveConfig, run_archive, verify_archive
from .client import MIN_DATE, MLBClient, OfficialDataError
from .formatter import format_events_ndjson, format_plain_text


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {value!r}") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mlb-pbp",
        description="Verified official MLB play-by-play archive and plain-text formatter.",
        epilog="The only origin contacted is https://statsapi.mlb.com.",
    )
    parser.add_argument("--version", action="version", version=f"mlb-pbp {__version__}")
    sub = parser.add_subparsers(dest="command")

    game = sub.add_parser("game", help="write one game in one format")
    game.add_argument("game_pk", help="official gamePk, e.g. 746865")
    game.add_argument("--format", dest="fmt", choices=list(FORMATS), default="text")
    game.add_argument("--output", type=Path, help="file to write (default: standard output)")
    game.add_argument("--request-delay", type=float, default=0.2)
    game.add_argument("--raw-uncompressed", action="store_true", help="ignored for --format raw here; the body is written as returned")

    archive = sub.add_parser("archive", help="archive a complete requested date range")
    archive.add_argument("--start", type=_parse_date, default=MIN_DATE)
    archive.add_argument("--end", type=_parse_date, default=None, help="default: today (UTC)")
    archive.add_argument("--output", type=Path, default=Path("archive"))
    archive.add_argument("--formats", default="text,raw,events")
    archive.add_argument("--workers", type=int, default=2)
    archive.add_argument("--request-delay", type=float, default=0.2)
    archive.add_argument("--refresh", action="store_true", help="re-fetch games already in the manifest")
    archive.add_argument("--raw-uncompressed", action="store_true", help="store raw responses as .json instead of .json.gz")
    archive.add_argument("--limit", type=int, default=None, help="stop after N games (smoke test)")

    verify = sub.add_parser("verify", help="check every stored digest in an archive")
    verify.add_argument("path", type=Path)

    return parser


def _cmd_game(args: argparse.Namespace) -> int:
    client = MLBClient(request_delay=args.request_delay)
    try:
        response = client.game(args.game_pk)
    except OfficialDataError as error:
        print(f"error [{error.code}]: {error}", file=sys.stderr)
        return 1
    if args.fmt == "raw":
        body = response.raw_bytes(compress=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(body)
            print(f"wrote {args.output} ({len(body)} bytes)")
        else:
            sys.stdout.write(response.text)
        return 0
    if args.fmt == "events":
        text = format_events_ndjson(response.json, response.meta)
    else:
        text = format_plain_text(response.json, response.meta)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        sys.stdout.write(text)
    return 0


def _cmd_archive(args: argparse.Namespace) -> int:
    formats = tuple(name.strip() for name in args.formats.split(",") if name.strip())
    try:
        config = ArchiveConfig(
            output=args.output,
            start=args.start,
            end=args.end,
            formats=formats,
            workers=args.workers,
            request_delay=args.request_delay,
            refresh=args.refresh,
            gzip_raw=not args.raw_uncompressed,
            limit=args.limit,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    try:
        summary = run_archive(config)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0 if summary.failed == 0 else 1


def _cmd_verify(args: argparse.Namespace) -> int:
    report = verify_archive(args.path)
    for problem in report.problems:
        print(f"problem: {problem}", file=sys.stderr)
    print(f"records={report.records} files={report.files_checked} ok={report.ok}")
    return 0 if report.ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if argv and argv[0].startswith("-") and argv[0] not in {"--version", "-h", "--help"}:
        # Legacy invocation without a subcommand: treat the flags as archive options.
        argv = ["archive", *argv]
    args = parser.parse_args(argv)
    if args.command == "game":
        return _cmd_game(args)
    if args.command == "archive":
        return _cmd_archive(args)
    if args.command == "verify":
        return _cmd_verify(args)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

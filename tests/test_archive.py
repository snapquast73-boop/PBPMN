"""Archive behaviour: windows, storage, manifest resume and digest verification.

Fixtures are SYNTHETIC test scaffolding, never published baseball data.
"""

from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from mlb_pbp.archive import (
    ArchiveConfig,
    archive_game,
    month_windows,
    read_manifest,
    run_archive,
    verify_archive,
)
from mlb_pbp.client import OfficialResponse

from .test_formatter import NOTICE, synthetic_feed


def make_response(url: str, payload: dict) -> OfficialResponse:
    text = json.dumps(payload)
    import hashlib

    return OfficialResponse(
        url=url,
        text=text,
        json=payload,
        copyright=payload["copyright"],
        fetched_at="2026-11-20T00:00:00Z",
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


class FakeClient:
    """Serves synthetic official-shaped responses without touching the network."""

    def __init__(self, game_pks=(999001, 999002)):
        self.game_pks = tuple(game_pks)
        self.game_calls: list[str] = []
        self.schedule_calls: list[tuple[date, date]] = []

    def schedule(self, start, end):
        self.schedule_calls.append((start, end))
        games = [
            {
                "gamePk": game_pk,
                "gameType": "R",
                "season": "2026",
                "officialDate": "2026-04-01",
                "status": {"detailedState": "Final"},
                "teams": {
                    "away": {"team": {"id": 9001, "name": "Synthetic Away"}, "score": 1},
                    "home": {"team": {"id": 9002, "name": "Synthetic Home"}, "score": 0},
                },
            }
            for game_pk in self.game_pks
        ]
        return make_response(
            "https://statsapi.mlb.com/api/v1/schedule?synthetic=1",
            {"copyright": NOTICE, "dates": [{"date": "2026-04-01", "games": games}]},
        )

    def game(self, game_pk):
        self.game_calls.append(str(game_pk))
        feed = synthetic_feed()
        feed["gamePk"] = int(game_pk)
        feed["gameData"]["game"]["pk"] = int(game_pk)
        return make_response(
            f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live",
            feed,
        )


class MonthWindowTests(unittest.TestCase):
    def test_single_month(self):
        self.assertEqual(month_windows(date(2026, 8, 1), date(2026, 8, 11)), [(date(2026, 8, 1), date(2026, 8, 11))])

    def test_year_boundary(self):
        windows = month_windows(date(2014, 12, 20), date(2015, 2, 2))
        self.assertEqual(
            windows,
            [
                (date(2014, 12, 20), date(2014, 12, 31)),
                (date(2015, 1, 1), date(2015, 1, 31)),
                (date(2015, 2, 1), date(2015, 2, 2)),
            ],
        )

    def test_reversed_range_rejected(self):
        with self.assertRaises(ValueError):
            month_windows(date(2026, 5, 2), date(2026, 5, 1))


class ArchiveGameTests(unittest.TestCase):
    def test_writes_all_requested_formats_and_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = ArchiveConfig(output=root, start=date(2026, 4, 1), end=date(2026, 4, 1))
            client = FakeClient()
            game = client.schedule(date(2026, 4, 1), date(2026, 4, 1)).json["dates"][0]["games"][0]
            record = archive_game(client, game, config)

            self.assertEqual(record["gamePk"], "999001")
            self.assertEqual(record["officialDate"], "2026-04-01")
            self.assertEqual(record["sourceUrl"], "https://statsapi.mlb.com/api/v1.1/game/999001/feed/live")
            self.assertIn("MLB Advanced Media, L.P.", record["notice"])
            self.assertEqual(len(record["files"]), 3)

            for entry in record["files"]:
                self.assertTrue((root / entry["path"]).exists(), entry["path"])

            report = verify_archive(root)
            self.assertEqual(report.records, 0)  # nothing written to the manifest yet
            (root / "manifest.ndjson").write_text(json.dumps(record) + "\n", encoding="utf-8")
            report = verify_archive(root)
            self.assertTrue(report.ok, report.problems)
            self.assertEqual(report.files_checked, 3)

            raw_entry = [entry for entry in record["files"] if entry["mediaType"] == "application/json"][0]
            raw_bytes = gzip.decompress((root / raw_entry["path"]).read_bytes())
            self.assertIn(b"MLB Advanced Media, L.P.", raw_bytes)

    def test_verification_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = ArchiveConfig(output=root, start=date(2026, 4, 1), end=date(2026, 4, 1))
            client = FakeClient()
            game = client.schedule(date(2026, 4, 1), date(2026, 4, 1)).json["dates"][0]["games"][0]
            record = archive_game(client, game, config)
            (root / "manifest.ndjson").write_text(json.dumps(record) + "\n", encoding="utf-8")

            text_entry = [entry for entry in record["files"] if entry["mediaType"].startswith("text/plain")][0]
            target = root / text_entry["path"]
            target.write_text(target.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")

            report = verify_archive(root)
            self.assertFalse(report.ok)
            self.assertTrue(any("digest mismatch" in problem for problem in report.problems))

    def test_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = ArchiveConfig(output=root, start=date(2026, 4, 1), end=date(2026, 4, 1))
            client = FakeClient()
            game = client.schedule(date(2026, 4, 1), date(2026, 4, 1)).json["dates"][0]["games"][0]
            record = archive_game(client, game, config)
            (root / "manifest.ndjson").write_text(json.dumps(record) + "\n", encoding="utf-8")
            (root / record["files"][0]["path"]).unlink()
            report = verify_archive(root)
            self.assertFalse(report.ok)
            self.assertTrue(any("missing file" in problem for problem in report.problems))


class RunArchiveTests(unittest.TestCase):
    def test_archives_then_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = ArchiveConfig(output=root, start=date(2026, 4, 1), end=date(2026, 4, 1), workers=1)
            client = FakeClient()
            summary = run_archive(config, client=client, logger=lambda _m: None)
            self.assertEqual(summary.discovered, 2)
            self.assertEqual(summary.archived, 2)
            self.assertEqual(summary.failed, 0)

            manifest = read_manifest(root / "manifest.ndjson")
            self.assertEqual(sorted(manifest), ["999001", "999002"])
            self.assertTrue((root / "schedules" / "manifest.ndjson").exists())
            self.assertTrue((root / "schedules" / "2026-04-01_2026-04-01.json.gz").exists())

            second = FakeClient()
            summary = run_archive(config, client=second, logger=lambda _m: None)
            self.assertEqual(summary.archived, 0)
            self.assertEqual(summary.skipped, 2)
            self.assertEqual(second.game_calls, [])

            refreshed = FakeClient()
            config.refresh = True
            summary = run_archive(config, client=refreshed, logger=lambda _m: None)
            self.assertEqual(summary.archived, 2)
            self.assertEqual(len(refreshed.game_calls), 2)

    def test_limit_stops_early(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = ArchiveConfig(output=root, start=date(2026, 4, 1), end=date(2026, 4, 1), workers=1, limit=1)
            client = FakeClient()
            summary = run_archive(config, client=client, logger=lambda _m: None)
            self.assertEqual(summary.archived, 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

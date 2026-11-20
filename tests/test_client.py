"""Client behaviour: official-host allowlist, validation, retries and identity checks.

Every JSON document in this file is SYNTHETIC test scaffolding. Nothing here is baseball
data and nothing here is published.
"""

from __future__ import annotations

import io
import json
import unittest
import urllib.error
from datetime import date

from mlb_pbp.client import (
    COPYRIGHT_MARKER,
    GAME_TYPES,
    OFFICIAL_HOST,
    MLBClient,
    OfficialDataError,
    game_url,
    qualifying_games,
    schedule_url,
)

NOTICE = "Copyright 2026 MLB Advanced Media, L.P.  Synthetic test fixture."


class FakeResponse(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def opener_for(body: str, *, status: int = 200, calls: list | None = None):
    def opener(request, timeout=None):
        if calls is not None:
            calls.append(request.full_url)
        response = FakeResponse(body.encode("utf-8"))
        response.status = status
        return response

    return opener


class ScheduleUrlTests(unittest.TestCase):
    def test_uses_official_host_and_documented_parameters(self):
        url = schedule_url(date(2024, 4, 1), date(2024, 4, 1))
        self.assertTrue(url.startswith("https://statsapi.mlb.com/api/v1/schedule?"))
        self.assertIn("sportId=1", url)
        self.assertIn("startDate=2024-04-01", url)
        self.assertIn("endDate=2024-04-01", url)
        self.assertIn("gameTypes=R%2CF%2CD%2CL%2CW", url)
        self.assertIn("hydrate=linescore", url)
        self.assertEqual(GAME_TYPES, ("R", "F", "D", "L", "W"))

    def test_game_url(self):
        self.assertEqual(game_url(746170), "https://statsapi.mlb.com/api/v1.1/game/746170/feed/live")
        with self.assertRaises(OfficialDataError):
            game_url("746170x")

    def test_range_must_be_ordered(self):
        with self.assertRaises(ValueError):
            schedule_url(date(2024, 4, 2), date(2024, 4, 1))


class AllowlistTests(unittest.TestCase):
    def test_rejects_foreign_host_without_calling_opener(self):
        calls: list = []
        client = MLBClient(opener=opener_for("{}", calls=calls))
        with self.assertRaises(OfficialDataError) as caught:
            client.get("https://example.com/api/v1/schedule")
        self.assertEqual(caught.exception.code, "OFFICIAL_HOST")
        self.assertEqual(calls, [])

    def test_rejects_plain_http_on_official_host(self):
        client = MLBClient(opener=opener_for("{}"))
        with self.assertRaises(OfficialDataError) as caught:
            client.get("http://statsapi.mlb.com/api/v1/sports/1")
        self.assertEqual(caught.exception.code, "OFFICIAL_HOST")

    def test_rejects_suffix_host(self):
        client = MLBClient(opener=opener_for("{}"))
        with self.assertRaises(OfficialDataError) as caught:
            client.get("https://statsapi.mlb.com.evil.example/api/v1/sports/1")
        self.assertEqual(caught.exception.code, "OFFICIAL_HOST")
        self.assertEqual(OFFICIAL_HOST, "statsapi.mlb.com")


class ValidationTests(unittest.TestCase):
    def test_requires_mlb_notice(self):
        body = json.dumps({"copyright": "Copyright someone else", "sports": []})
        client = MLBClient(opener=opener_for(body), request_delay=0)
        with self.assertRaises(OfficialDataError) as caught:
            client.get("https://statsapi.mlb.com/api/v1/sports/1")
        self.assertEqual(caught.exception.code, "COPYRIGHT")

    def test_accepts_documented_notice_and_records_digest(self):
        body = json.dumps({"copyright": NOTICE, "sports": [{"id": 1}]})
        client = MLBClient(opener=opener_for(body), request_delay=0)
        response = client.get("https://statsapi.mlb.com/api/v1/sports/1")
        self.assertIn(COPYRIGHT_MARKER, response.copyright)
        self.assertEqual(len(response.sha256), 64)
        self.assertEqual(response.text, body)

    def test_rejects_non_json(self):
        client = MLBClient(opener=opener_for("<html>nope</html>"), request_delay=0)
        with self.assertRaises(OfficialDataError) as caught:
            client.get("https://statsapi.mlb.com/api/v1/sports/1")
        self.assertEqual(caught.exception.code, "JSON")

    def test_http_error_is_not_accepted(self):
        def opener(request, timeout=None):
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

        client = MLBClient(opener=opener, request_delay=0, sleep=lambda _s: None)
        with self.assertRaises(OfficialDataError) as caught:
            client.get("https://statsapi.mlb.com/api/v1/sports/1")
        self.assertEqual(caught.exception.code, "HTTP")

    def test_retries_transient_failures(self):
        attempts = {"n": 0}
        body = json.dumps({"copyright": NOTICE, "sports": []})

        def opener(request, timeout=None):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise urllib.error.URLError("temporary")
            return FakeResponse(body.encode("utf-8"))

        client = MLBClient(opener=opener, request_delay=0, retries=4, sleep=lambda _s: None)
        response = client.get("https://statsapi.mlb.com/api/v1/sports/1")
        self.assertEqual(attempts["n"], 3)
        self.assertEqual(response.json["copyright"], NOTICE)

    def test_gives_up_after_retries(self):
        def opener(request, timeout=None):
            raise urllib.error.URLError("down")

        client = MLBClient(opener=opener, request_delay=0, retries=2, sleep=lambda _s: None)
        with self.assertRaises(OfficialDataError) as caught:
            client.get("https://statsapi.mlb.com/api/v1/sports/1")
        self.assertEqual(caught.exception.code, "NETWORK")


class GameIdentityTests(unittest.TestCase):
    def test_game_pk_mismatch_is_rejected(self):
        body = json.dumps({"copyright": NOTICE, "gamePk": 111, "gameData": {}, "liveData": {}})
        client = MLBClient(opener=opener_for(body), request_delay=0)
        with self.assertRaises(OfficialDataError) as caught:
            client.game(222)
        self.assertEqual(caught.exception.code, "GAMEPK")

    def test_matching_game_is_accepted(self):
        body = json.dumps(
            {"copyright": NOTICE, "gamePk": 111, "gameData": {"game": {"pk": 111}}, "liveData": {}}
        )
        client = MLBClient(opener=opener_for(body), request_delay=0)
        response = client.game(111)
        self.assertEqual(response.json["gamePk"], 111)
        self.assertEqual(response.url, "https://statsapi.mlb.com/api/v1.1/game/111/feed/live")

    def test_schedule_requires_dates_array(self):
        body = json.dumps({"copyright": NOTICE})
        client = MLBClient(opener=opener_for(body), request_delay=0)
        with self.assertRaises(OfficialDataError) as caught:
            client.schedule(date(2024, 4, 1), date(2024, 4, 1))
        self.assertEqual(caught.exception.code, "SCHEMA")


class QualifyingGamesTests(unittest.TestCase):
    def test_keeps_only_documented_types(self):
        schedule = {
            "dates": [
                {
                    "games": [
                        {"gamePk": 1, "gameType": "R"},
                        {"gamePk": 2, "gameType": "S"},
                        {"gamePk": 3, "gameType": "W"},
                        {"gamePk": 4, "gameType": "E"},
                    ]
                }
            ]
        }
        self.assertEqual([game["gamePk"] for game in qualifying_games(schedule)], [1, 3])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

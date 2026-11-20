"""Formatter behaviour on a SYNTHETIC feed.

The fixture below is deliberately synthetic and obviously labelled (SYN / HOM, invented
names). It is test scaffolding, never published baseball data. Its shape mirrors the fields
verified live against the official API (see COORDINATION.md §4, V4–V14).
"""

from __future__ import annotations

import json
import unittest

from mlb_pbp.formatter import NOT_SUPPLIED, format_events_ndjson, format_plain_text

NOTICE = "Copyright 2026 MLB Advanced Media, L.P.  Synthetic test fixture."


def synthetic_feed(with_decisions: bool = True) -> dict:
    play = {
        "about": {
            "atBatIndex": 0,
            "inning": 1,
            "halfInning": "top",
            "isComplete": True,
            "isScoringPlay": False,
            "hasReview": False,
        },
        "result": {
            "type": "atBat",
            "event": "Single",
            "eventType": "single",
            "description": "Synthetic Batter singles on a ground ball to left field.",
            "rbi": 0,
            "awayScore": 0,
            "homeScore": 0,
            "isOut": False,
        },
        "count": {"balls": 1, "strikes": 2, "outs": 0},
        "matchup": {
            "batter": {"id": 100001, "fullName": "Synthetic Batter"},
            "pitcher": {"id": 200002, "fullName": "Synthetic Pitcher"},
        },
        "playEvents": [
            {
                "index": 0,
                "isPitch": True,
                "type": "pitch",
                "details": {
                    "call": {"code": "C", "description": "Called Strike"},
                    "description": "Called Strike",
                    "code": "C",
                    "isInPlay": False,
                    "isStrike": True,
                    "isBall": False,
                    "type": {"code": "FF", "description": "Four-Seam Fastball"},
                },
                "pitchData": {
                    "startSpeed": 95.2,
                    "endSpeed": 86.1,
                    "zone": 5,
                    "coordinates": {"pX": -0.22, "pZ": 2.45},
                },
            },
            {
                "index": 1,
                "isPitch": True,
                "type": "pitch",
                "details": {
                    "call": {"code": "X", "description": "In play, no out"},
                    "description": "In play, no out",
                    "code": "X",
                    "isInPlay": True,
                    "type": {"code": "SI", "description": "Sinker"},
                },
                "pitchData": {"startSpeed": 94.0, "zone": 8},
                "hitData": {
                    "launchSpeed": 99.8,
                    "launchAngle": 12.0,
                    "totalDistance": 210.0,
                    "trajectory": "line_drive",
                    "hardness": "medium",
                },
            },
        ],
        "runners": [
            {
                "movement": {"originBase": None, "start": None, "end": "1B", "isOut": False, "outBase": None, "outNumber": None},
                "details": {
                    "event": "Single",
                    "eventType": "single",
                    "runner": {"fullName": "Synthetic Batter"},
                    "isScoringEvent": False,
                },
            }
        ],
    }

    return {
        "copyright": NOTICE,
        "gamePk": 999001,
        "metaData": {"wait": 10, "timeStamp": "20260401_000000"},
        "gameData": {
            "game": {"pk": 999001, "type": "R", "season": "2026", "gameNumber": 1, "doubleHeader": "N"},
            "datetime": {
                "dateTime": "2026-04-01T23:05:00Z",
                "officialDate": "2026-04-01",
                "dayNight": "night",
            },
            "status": {"abstractGameState": "Final", "detailedState": "Final"},
            "teams": {
                "away": {"id": 9001, "name": "Synthetic Away", "abbreviation": "SYN"},
                "home": {"id": 9002, "name": "Synthetic Home", "abbreviation": "HOM"},
            },
            "venue": {"id": 1, "name": "Synthetic Park"},
        },
        "liveData": {
            "linescore": {
                "currentInning": 1,
                "inningState": "Bottom",
                "innings": [
                    {"num": 1, "ordinalNum": "1st", "away": {"runs": 1, "hits": 1, "errors": 0, "leftOnBase": 0},
                     "home": {"runs": 0, "hits": 0, "errors": 0, "leftOnBase": 0}}
                ],
                "teams": {
                    "away": {"runs": 1, "hits": 1, "errors": 0, "leftOnBase": 0},
                    "home": {"runs": 0, "hits": 0, "errors": 1, "leftOnBase": 0},
                },
                "note": "Synthetic note.",
            },
            "decisions": (
                {"winner": {"id": 1, "fullName": "Synthetic Winner"}, "loser": {"id": 2, "fullName": "Synthetic Loser"}}
                if with_decisions
                else {}
            ),
            "plays": {"allPlays": [play]},
            "boxscore": {
                "teams": {
                    "away": {
                        "team": {"name": "Synthetic Away", "abbreviation": "SYN"},
                        "battingOrder": [100001],
                        "pitchers": [200003],
                        "players": {
                            "ID100001": {
                                "person": {"fullName": "Synthetic Batter"},
                                "position": {"abbreviation": "LF"},
                                "battingOrder": "100",
                                "stats": {"batting": {"atBats": 4, "runs": 1, "hits": 2, "rbi": 1,
                                                      "baseOnBalls": 0, "strikeOuts": 1}},
                                "seasonStats": {"batting": {"avg": ".318"}},
                            },
                            "ID200003": {
                                "person": {"fullName": "Synthetic Starter"},
                                "position": {"abbreviation": "P"},
                                "stats": {"pitching": {"inningsPitched": "6.0", "hits": 4, "runs": 1,
                                                       "earnedRuns": 1, "baseOnBalls": 2, "strikeOuts": 7,
                                                       "era": "2.84", "note": "(W, 1-0)"}},
                            },
                        },
                    },
                    "home": {"team": {"name": "Synthetic Home"}, "battingOrder": [], "pitchers": [], "players": {}},
                }
            },
        },
    }


META = {
    "url": "https://statsapi.mlb.com/api/v1.1/game/999001/feed/live",
    "fetchedAt": "2026-11-20T00:00:00Z",
    "sha256": "0" * 64,
    "copyright": NOTICE,
}


class PlainTextTests(unittest.TestCase):
    def setUp(self):
        self.text = format_plain_text(synthetic_feed(), META)

    def test_header_and_provenance(self):
        self.assertIn("MLB PLAINTEXT PLAY-BY-PLAY", self.text)
        self.assertIn("SYN at HOM  — 1-0 | Final", self.text)
        self.assertIn("sourceUrl: " + META["url"], self.text)
        self.assertIn("sourceSha256: " + ("0" * 64), self.text)
        self.assertIn("MLB Advanced Media, L.P.", self.text)
        self.assertIn("copyright:", self.text)

    def test_game_section(self):
        self.assertIn("officialDate: 2026-04-01", self.text)
        self.assertIn("venue: Synthetic Park", self.text)
        self.assertIn("away: Synthetic Away (9001)", self.text)

    def test_line_score(self):
        self.assertIn("LINE SCORE", self.text)
        self.assertIn("note: Synthetic note.", self.text)

    def test_decisions(self):
        self.assertIn("W:  Synthetic Winner", self.text)
        self.assertIn("L:  Synthetic Loser", self.text)
        self.assertIn("SV: (none supplied by MLB)", self.text)

    def test_play_by_play(self):
        self.assertIn("-- TOP 1st --", self.text)
        self.assertIn("[000] Single | 1-2 | Synthetic Batter singles", self.text)
        self.assertIn("batter=Synthetic Batter (100001)", self.text)
        self.assertIn("pitch_type=Four-Seam Fastball", self.text)
        self.assertIn("start_mph=95.2", self.text)
        self.assertIn("exit_mph=99.8", self.text)
        self.assertIn("RUNNER 00 | Synthetic Batter | batter -> 1B", self.text)

    def test_box_score_uses_season_average(self):
        self.assertIn("BOX SCORE", self.text)
        self.assertIn(".318", self.text)
        self.assertIn("(W, 1-0)", self.text)

    def test_missing_decisions_are_stated_not_invented(self):
        text = format_plain_text(synthetic_feed(with_decisions=False), META)
        self.assertIn(f"{NOT_SUPPLIED} (no decisions in the official feed)", text)

    def test_empty_plays_are_stated(self):
        feed = synthetic_feed()
        feed["liveData"]["plays"]["allPlays"] = []
        text = format_plain_text(feed, META)
        self.assertIn(f"{NOT_SUPPLIED} (no plays in the official feed for this game status)", text)

    def test_empty_innings_are_stated(self):
        feed = synthetic_feed()
        feed["liveData"]["linescore"]["innings"] = []
        text = format_plain_text(feed, META)
        self.assertIn(f"{NOT_SUPPLIED} (no innings in the official feed)", text)

    def test_absent_provenance_is_marked(self):
        text = format_plain_text(synthetic_feed(), {})
        self.assertIn("(not recorded)", text)


class NdjsonTests(unittest.TestCase):
    def test_record_sequence(self):
        text = format_events_ndjson(synthetic_feed(), META)
        lines = [json.loads(line) for line in text.strip().split("\n")]
        self.assertEqual(lines[0]["recordType"], "metadata")
        self.assertEqual(lines[0]["gamePk"], 999001)
        self.assertEqual(lines[0]["sourceSha256"], "0" * 64)
        self.assertEqual([line["recordType"] for line in lines], ["metadata", "play", "event", "event"])
        self.assertTrue(all(line["gamePk"] == 999001 for line in lines))
        self.assertEqual(lines[1]["atBatIndex"], 0)
        self.assertFalse(lines[2]["isPitch"] is None)
        self.assertEqual(lines[3]["hitData"]["launchAngle"], 12.0)

    def test_every_line_is_one_object(self):
        text = format_events_ndjson(synthetic_feed(), META)
        for line in text.strip().split("\n"):
            self.assertIsInstance(json.loads(line), dict)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

"""Deterministic text and NDJSON projections of an official MLB feed.

Every value is read from a field of the official response. A missing field is reported as
``not supplied by MLB`` — it is never defaulted, estimated or repaired.

The rendered report has the same sections and the same source fields as the browser's
``docs/js/format.js``:

    MLB PLAINTEXT PLAY-BY-PLAY
    <AWAY> at <HOME>  — <away>-<home> | <status>
    PROVENANCE   gamePk, sourceUrl, fetchedAt, source SHA-256, copyright
    GAME         officialDate, scheduled, type, number, season, venue, status, clubs
    LINE SCORE   innings + R/H/E/LOB
    DECISIONS    W / L / SV when supplied
    PLAY-BY-PLAY one block per at-bat with every pitch/action and runner movement
    BOX SCORE    batters AB,R,H,…,AVG and pitchers IP,H,R,ER,…,ERA
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, Sequence

NOT_SUPPLIED = "not supplied by MLB"


def _text(value: Any, fallback: str = NOT_SUPPLIED) -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _num(value: Any, fallback: str = NOT_SUPPLIED) -> str:
    return fallback if value is None else str(value)


def _pad(value: Any, width: int) -> str:
    return str(value).ljust(width)


def _pad_left(value: Any, width: int) -> str:
    return str(value).rjust(width)


def _dig(value: Any, *path: str) -> Any:
    cursor: Any = value
    for key in path:
        if not isinstance(cursor, Mapping):
            return None
        cursor = cursor.get(key)
    return cursor


def _ordinal(number: Any) -> str:
    try:
        value = int(number)
    except (TypeError, ValueError):
        return str(number)
    if 11 <= value % 100 <= 13:
        return f"{value}th"
    return f"{value}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th') }"


def _half(half: Any) -> str:
    if half == "top":
        return "TOP"
    if half == "bottom":
        return "BOTTOM"
    return str(half or "").upper()


def _abbr(game_data: Mapping[str, Any], side: str) -> str:
    team = _dig(game_data, "teams", side) or {}
    return str(team.get("abbreviation") or team.get("teamCode") or team.get("name") or side.upper())


def header_line(feed: Mapping[str, Any]) -> str:
    game_data = feed.get("gameData") or {}
    status = game_data.get("status") or {}
    away = _abbr(game_data, "away")
    home = _abbr(game_data, "home")
    linescore = _dig(feed, "liveData", "linescore") or {}
    runs = _dig(linescore, "teams") or {}
    away_runs = _dig(runs, "away", "runs")
    home_runs = _dig(runs, "home", "runs")
    state = _text(status.get("detailedState") or status.get("abstractGameState"), "")
    if away_runs is not None and home_runs is not None:
        return f"{away} at {home}  — {away_runs}-{home_runs} | {state}"
    return f"{away} at {home}  — {state}"


def line_score_block(feed: Mapping[str, Any]) -> list[str]:
    game_data = feed.get("gameData") or {}
    linescore = _dig(feed, "liveData", "linescore") or {}
    innings = linescore.get("innings") or []
    lines = ["LINE SCORE"]
    if not innings:
        return lines + [f"  {NOT_SUPPLIED} (no innings in the official feed)"]

    head = _pad("TEAM", 6) + "".join(_pad_left(inning.get("num"), 3) for inning in innings)
    head += _pad_left("R", 4) + _pad_left("H", 3) + _pad_left("E", 3) + _pad_left("LOB", 5)
    lines.append("  " + head)

    for side in ("away", "home"):
        totals = _dig(linescore, "teams", side) or {}
        row = _pad(_abbr(game_data, side), 6)
        for inning in innings:
            cell = inning.get(side) or {}
            row += _pad_left(_num(cell.get("runs"), "-"), 3)
        row += (
            _pad_left(_num(totals.get("runs")), 4)
            + _pad_left(_num(totals.get("hits")), 3)
            + _pad_left(_num(totals.get("errors")), 3)
            + _pad_left(_num(totals.get("leftOnBase")), 5)
        )
        lines.append("  " + row)

    if linescore.get("note"):
        lines.append(f"  note: {linescore['note']}")
    if linescore.get("currentInning") is not None:
        half = _half(linescore.get("inningState") or linescore.get("inningHalf"))
        lines.append(f"  through: {half} {_ordinal(linescore.get('currentInning'))}")
    return lines


def decision_lines(feed: Mapping[str, Any]) -> list[str]:
    decisions = _dig(feed, "liveData", "decisions") or {}
    lines = ["DECISIONS"]
    if not any(decisions.get(key) for key in ("winner", "loser", "save")):
        return lines + [f"  {NOT_SUPPLIED} (no decisions in the official feed)"]
    for label, key in (("W: ", "winner"), ("L: ", "loser"), ("SV:", "save")):
        person = decisions.get(key)
        name = _text((person or {}).get("fullName"), "(none supplied by MLB)")
        lines.append(f"  {label} {name}")
    return lines


def _event_line(entry: Mapping[str, Any], index: int) -> str:
    details = entry.get("details") or {}
    pitch = entry.get("pitchData") or {}
    hit = entry.get("hitData") or {}
    parts = [
        f"EVENT {index:02d}",
        f"type={_text(entry.get('type'), 'unknown')}",
        f"pitch={'yes' if entry.get('isPitch') else 'no'}",
        f"description={_text(details.get('description'), '(no description supplied)')}",
    ]
    call = details.get("call") or {}
    if call.get("code"):
        parts.append(f"code={call['code']}")
    pitch_type = details.get("type") or {}
    if pitch_type.get("description"):
        parts.append(f"pitch_type={pitch_type['description']}")
    if pitch.get("startSpeed") is not None:
        parts.append(f"start_mph={pitch['startSpeed']}")
    if pitch.get("endSpeed") is not None:
        parts.append(f"end_mph={pitch['endSpeed']}")
    if pitch.get("zone") is not None:
        parts.append(f"zone={pitch['zone']}")
    coordinates = pitch.get("coordinates") or {}
    if coordinates.get("pX") is not None:
        parts.append(f"plate_x={round(float(coordinates['pX']), 2)}")
    if coordinates.get("pZ") is not None:
        parts.append(f"plate_z={round(float(coordinates['pZ']), 2)}")
    for key, label in (
        ("launchSpeed", "exit_mph"),
        ("launchAngle", "launch_angle"),
        ("totalDistance", "distance_ft"),
        ("trajectory", "trajectory"),
        ("hardness", "hardness"),
    ):
        if hit.get(key) is not None:
            parts.append(f"{label}={hit[key]}")
    return "    " + " | ".join(parts)


def _runner_line(runner: Mapping[str, Any], index: int) -> str:
    movement = runner.get("movement") or {}
    details = runner.get("details") or {}
    name = _text(_dig(details, "runner", "fullName"), "(runner not supplied)")
    origin = movement.get("originBase") or "batter"
    if movement.get("isOut"):
        destination = f"out@{_text(movement.get('outBase'), '?')}"
    else:
        destination = _text(movement.get("end"), "held")
    parts = [f"RUNNER {index:02d}", name, f"{origin} -> {destination}"]
    if movement.get("outNumber") is not None:
        parts.append(f"out={movement['outNumber']}")
    if details.get("event"):
        parts.append(f"event={details['event']}")
    if details.get("isScoringEvent"):
        parts.append("scoring=yes")
    return "    " + " | ".join(parts)


def plays_block(feed: Mapping[str, Any]) -> list[str]:
    plays = _dig(feed, "liveData", "plays", "allPlays") or []
    lines = ["PLAY-BY-PLAY"]
    if not plays:
        return lines + [f"  {NOT_SUPPLIED} (no plays in the official feed for this game status)"]

    current: tuple[Any, Any] | None = None
    for play in plays:
        about = play.get("about") or {}
        marker = (about.get("inning"), about.get("halfInning"))
        if marker != current:
            current = marker
            lines.append("")
            lines.append(f"-- {_half(about.get('halfInning'))} {_ordinal(about.get('inning'))} --")
        result = play.get("result") or {}
        count = play.get("count") or {}
        index = about.get("atBatIndex") or 0
        lines.append(
            f"[{index:03d}] {_text(result.get('event'))} | "
            f"{_num(count.get('balls'), '?')}-{_num(count.get('strikes'), '?')} | "
            f"{_text(result.get('description'), '(no description supplied)')}"
        )
        batter = _dig(play, "matchup", "batter") or {}
        pitcher = _dig(play, "matchup", "pitcher") or {}
        lines.append(
            "    batter=" + _text(batter.get("fullName")) + f" ({_num(batter.get('id'))})"
            " | pitcher=" + _text(pitcher.get("fullName")) + f" ({_num(pitcher.get('id'))})"
            f" | score={_num(result.get('awayScore'))}-{_num(result.get('homeScore'))}"
            f" | scoring={'yes' if about.get('isScoringPlay') else 'no'}"
            f" | complete={'yes' if about.get('isComplete') else 'no'}"
        )
        for position, entry in enumerate(play.get("playEvents") or []):
            lines.append(_event_line(entry, position))
        for position, runner in enumerate(play.get("runners") or []):
            lines.append(_runner_line(runner, position))
    return lines


def _season_avg(player: Mapping[str, Any]) -> Any:
    return _dig(player, "seasonStats", "batting", "avg")


def _box_block(game_data: Mapping[str, Any], boxscore: Mapping[str, Any], side: str) -> list[str]:
    team_block = _dig(boxscore, "teams", side) or {}
    lines = [_abbr(game_data, side)]
    if not team_block:
        return lines + [f"  {NOT_SUPPLIED}"]

    players = team_block.get("players") or {}
    order = team_block.get("battingOrder") or []
    pitchers = team_block.get("pitchers") or []

    lines.append(
        "  " + _pad("BATTERS", 24) + _pad_left("AB", 4) + _pad_left("R", 3) + _pad_left("H", 3)
        + _pad_left("RBI", 4) + _pad_left("BB", 4) + _pad_left("SO", 4) + _pad_left("AVG", 6)
    )
    if not order:
        lines.append(f"  {NOT_SUPPLIED} (no batting order in the official box score)")
    for person_id in order:
        player = players.get(f"ID{person_id}")
        if not player:
            continue
        batting = _dig(player, "stats", "batting") or {}
        name = _text(_dig(player, "person", "fullName"), "(name not supplied)")
        position = _text(_dig(player, "position", "abbreviation"), "")
        label = name + (f" {position}" if position else "")
        lines.append(
            "  " + _pad(label, 24)
            + _pad_left(_num(batting.get("atBats")), 4)
            + _pad_left(_num(batting.get("runs")), 3)
            + _pad_left(_num(batting.get("hits")), 3)
            + _pad_left(_num(batting.get("rbi")), 4)
            + _pad_left(_num(batting.get("baseOnBalls")), 4)
            + _pad_left(_num(batting.get("strikeOuts")), 4)
            + _pad_left(_season_avg(player) or "--", 6)
        )

    lines.append("")
    lines.append(
        "  " + _pad("PITCHERS", 24) + _pad_left("IP", 6) + _pad_left("H", 3) + _pad_left("R", 3)
        + _pad_left("ER", 4) + _pad_left("BB", 4) + _pad_left("SO", 4) + _pad_left("ERA", 7)
    )
    if not pitchers:
        lines.append(f"  {NOT_SUPPLIED} (no pitchers in the official box score)")
    for person_id in pitchers:
        player = players.get(f"ID{person_id}")
        if not player:
            continue
        pitching = _dig(player, "stats", "pitching") or {}
        name = _text(_dig(player, "person", "fullName"), "(name not supplied)")
        note = _text(pitching.get("note"), "")
        label = name + (f" {note}" if note else "")
        lines.append(
            "  " + _pad(label, 24)
            + _pad_left(_num(pitching.get("inningsPitched")), 6)
            + _pad_left(_num(pitching.get("hits")), 3)
            + _pad_left(_num(pitching.get("runs")), 3)
            + _pad_left(_num(pitching.get("earnedRuns")), 4)
            + _pad_left(_num(pitching.get("baseOnBalls")), 4)
            + _pad_left(_num(pitching.get("strikeOuts")), 4)
            + _pad_left(pitching.get("era") or "--", 7)
        )
    return lines


def box_score_block(feed: Mapping[str, Any]) -> list[str]:
    game_data = feed.get("gameData") or {}
    boxscore = _dig(feed, "liveData", "boxscore") or {}
    lines = ["BOX SCORE"]
    if not boxscore.get("teams"):
        return lines + [f"  {NOT_SUPPLIED} (no box score in the official feed)"]
    lines.append("")
    lines.extend(_box_block(game_data, boxscore, "away"))
    lines.append("")
    lines.extend(_box_block(game_data, boxscore, "home"))
    return lines


def format_plain_text(feed: Mapping[str, Any], meta: Mapping[str, Any] | None = None) -> str:
    """Render the complete readable report for one official feed."""
    provenance = meta or {}
    game_data = feed.get("gameData") or {}
    game = game_data.get("game") or {}
    when = game_data.get("datetime") or {}
    status = game_data.get("status") or {}
    venue = game_data.get("venue") or {}

    lines = ["MLB PLAINTEXT PLAY-BY-PLAY", header_line(feed), ""]

    lines += [
        "PROVENANCE",
        f"  gamePk: {_num(feed.get('gamePk'))}",
        f"  sourceUrl: {_text(provenance.get('url'))}",
        f"  fetchedAt: {_text(provenance.get('fetchedAt'))}",
        f"  sourceSha256: {_text(provenance.get('sha256'), '(not recorded)')}",
        f"  copyright: {_text(provenance.get('copyright'), _text(feed.get('copyright')))}",
        "",
        "GAME",
        f"  officialDate: {_text(when.get('officialDate'))}",
        f"  scheduled: {_text(when.get('dateTime'))}",
        f"  type: {_text(game.get('type'))}",
        f"  number: {_num(game.get('gameNumber'))}",
        f"  season: {_text(game.get('season'))}",
        f"  venue: {_text(venue.get('name'))}",
        f"  status: {_text(status.get('detailedState') or status.get('abstractGameState'))}",
        f"  away: {_text(_dig(game_data, 'teams', 'away', 'name'))}"
        f" ({_num(_dig(game_data, 'teams', 'away', 'id'))})",
        f"  home: {_text(_dig(game_data, 'teams', 'home', 'name'))}"
        f" ({_num(_dig(game_data, 'teams', 'home', 'id'))})",
        "",
    ]

    lines += line_score_block(feed)
    lines.append("")
    lines += decision_lines(feed)
    lines.append("")
    lines += plays_block(feed)
    lines.append("")
    lines += box_score_block(feed)
    lines.append("")
    return "\n".join(lines)


def format_events_ndjson(feed: Mapping[str, Any], meta: Mapping[str, Any] | None = None) -> str:
    """One JSON record per line: metadata, then each play, then each play event."""
    provenance = meta or {}
    records: list[str] = []
    records.append(
        json.dumps(
            {
                "recordType": "metadata",
                "gamePk": feed.get("gamePk"),
                "sourceUrl": provenance.get("url"),
                "fetchedAt": provenance.get("fetchedAt"),
                "sourceSha256": provenance.get("sha256"),
                "copyright": provenance.get("copyright") or feed.get("copyright"),
                "gameData": feed.get("gameData"),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    for play in _dig(feed, "liveData", "plays", "allPlays") or []:
        about = play.get("about") or {}
        records.append(
            json.dumps(
                {
                    "recordType": "play",
                    "gamePk": feed.get("gamePk"),
                    "atBatIndex": about.get("atBatIndex"),
                    "result": play.get("result"),
                    "about": about,
                    "count": play.get("count"),
                    "matchup": play.get("matchup"),
                    "runners": play.get("runners") or [],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        for entry in play.get("playEvents") or []:
            records.append(
                json.dumps(
                    {
                        "recordType": "event",
                        "gamePk": feed.get("gamePk"),
                        "atBatIndex": about.get("atBatIndex"),
                        "eventIndex": entry.get("index"),
                        "isPitch": bool(entry.get("isPitch")),
                        "type": entry.get("type"),
                        "details": entry.get("details"),
                        "pitchData": entry.get("pitchData"),
                        "hitData": entry.get("hitData"),
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
    return "\n".join(records) + "\n"

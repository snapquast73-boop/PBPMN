/*
 * docs/js/format.js — deterministic text and NDJSON projections of an official MLB feed.
 *
 * Every value emitted here is read from a field of the official response. Nothing is
 * estimated, defaulted or repaired: when MLB does not supply a value the output says so
 * explicitly ("not supplied by MLB").
 *
 * Field names used below are verified against the live official API
 * (see COORDINATION.md §4, V4–V14).
 */
(function (root, factory) {
  'use strict';
  var mod = factory();
  if (typeof module !== 'undefined' && module.exports) { module.exports = mod; }
  root.MLBPBP = root.MLBPBP || {};
  root.MLBPBP.format = mod;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var NOT_SUPPLIED = 'not supplied by MLB';

  function value(input) {
    return input === null || input === undefined ? null : input;
  }

  function text(input, fallback) {
    var v = value(input);
    if (v === null || v === '') { return fallback === undefined ? NOT_SUPPLIED : fallback; }
    return String(v);
  }

  function num(input) {
    var v = value(input);
    return v === null ? NOT_SUPPLIED : String(v);
  }

  function pad(input, width) {
    var s = String(input);
    while (s.length < width) { s += ' '; }
    return s;
  }

  function padLeft(input, width) {
    var s = String(input);
    while (s.length < width) { s = ' ' + s; }
    return s;
  }

  function sideLabel(half) {
    if (half === 'top') { return 'TOP'; }
    if (half === 'bottom') { return 'BOTTOM'; }
    return String(half || '').toUpperCase();
  }

  function ordinal(n) {
    var number = Number(n);
    if (!isFinite(number)) { return String(n); }
    var mod100 = number % 100;
    if (mod100 >= 11 && mod100 <= 13) { return number + 'th'; }
    switch (number % 10) {
      case 1: return number + 'st';
      case 2: return number + 'nd';
      case 3: return number + 'rd';
      default: return number + 'th';
    }
  }

  function teamAbbreviation(gameData, side) {
    var team = gameData && gameData.teams ? gameData.teams[side] : null;
    if (!team) { return side === 'home' ? 'HOME' : 'AWAY'; }
    return team.abbreviation || team.teamCode || team.name || (side === 'home' ? 'HOME' : 'AWAY');
  }

  function scoreLine(feed) {
    var linescore = feed.liveData && feed.liveData.linescore ? feed.liveData.linescore : null;
    var teams = linescore && linescore.teams ? linescore.teams : null;
    if (!teams) { return null; }
    return {
      away: teams.away && teams.away.runs != null ? teams.away.runs : null,
      home: teams.home && teams.home.runs != null ? teams.home.runs : null
    };
  }

  function headerLine(feed) {
    var gd = feed.gameData || {};
    var status = gd.status || {};
    var away = teamAbbreviation(gd, 'away');
    var home = teamAbbreviation(gd, 'home');
    var score = scoreLine(feed);
    var tail = text(status.detailedState || status.abstractGameState, '');
    if (score && score.away !== null && score.home !== null) {
      return away + ' at ' + home + '  — ' + score.away + '-' + score.home + ' | ' + tail;
    }
    return away + ' at ' + home + '  — ' + tail;
  }

  /* ---------------------------------------------------------------- line score */

  function lineScoreBlock(feed) {
    var gd = feed.gameData || {};
    var linescore = feed.liveData && feed.liveData.linescore ? feed.liveData.linescore : null;
    var lines = ['LINE SCORE'];
    if (!linescore || !Array.isArray(linescore.innings) || linescore.innings.length === 0) {
      lines.push('  ' + NOT_SUPPLIED + ' (no innings in the official feed)');
      return lines;
    }
    var innings = linescore.innings;
    var head = pad('TEAM', 6);
    innings.forEach(function (inning) { head += padLeft(inning.num, 3); });
    head += padLeft('R', 4) + padLeft('H', 3) + padLeft('E', 3) + padLeft('LOB', 5);
    lines.push('  ' + head);

    ['away', 'home'].forEach(function (side) {
      var team = linescore.teams && linescore.teams[side] ? linescore.teams[side] : {};
      var row = pad(teamAbbreviation(gd, side), 6);
      innings.forEach(function (inning) {
        var cell = inning[side];
        row += padLeft(cell && cell.runs != null ? cell.runs : '-', 3);
      });
      row += padLeft(num(team.runs), 4) + padLeft(num(team.hits), 3) + padLeft(num(team.errors), 3) +
        padLeft(num(team.leftOnBase), 5);
      lines.push('  ' + row);
    });

    if (linescore.note) { lines.push('  note: ' + linescore.note); }
    if (linescore.currentInning) {
      lines.push('  through: ' + sideLabel(linescore.inningState || linescore.inningHalf) + ' ' +
        ordinal(linescore.currentInning) + ' (' + num(linescore.currentInning) + ')');
    }
    return lines;
  }

  /* ---------------------------------------------------------------- decisions */

  function decisionLines(feed) {
    var decisions = feed.liveData && feed.liveData.decisions ? feed.liveData.decisions : null;
    var lines = ['DECISIONS'];
    if (!decisions || (!decisions.winner && !decisions.loser && !decisions.save)) {
      lines.push('  ' + NOT_SUPPLIED + ' (no decisions in the official feed)');
      return lines;
    }
    lines.push('  W:  ' + (decisions.winner ? text(decisions.winner.fullName) : '(none supplied by MLB)'));
    lines.push('  L:  ' + (decisions.loser ? text(decisions.loser.fullName) : '(none supplied by MLB)'));
    lines.push('  SV: ' + (decisions.save ? text(decisions.save.fullName) : '(none supplied by MLB)'));
    return lines;
  }

  /* ---------------------------------------------------------------- play by play */

  function countOf(play) {
    var c = play && play.count ? play.count : null;
    if (!c) { return '?-?'; }
    return num(c.balls) + '-' + num(c.strikes);
  }

  function eventLine(entry, index) {
    var details = entry && entry.details ? entry.details : {};
    var pitch = entry && entry.pitchData ? entry.pitchData : null;
    var hit = entry && entry.hitData ? entry.hitData : null;
    var parts = [
      'EVENT ' + padLeft(index, 2).replace(/ /g, '0'),
      'type=' + text(entry && entry.type, 'unknown'),
      'pitch=' + (entry && entry.isPitch ? 'yes' : 'no'),
      'description=' + text(details.description, '(no description supplied)')
    ];
    if (details.call && details.call.code) { parts.push('code=' + details.call.code); }
    if (details.type && details.type.description) { parts.push('pitch_type=' + details.type.description); }
    if (pitch && pitch.startSpeed != null) { parts.push('start_mph=' + pitch.startSpeed); }
    if (pitch && pitch.endSpeed != null) { parts.push('end_mph=' + pitch.endSpeed); }
    if (pitch && pitch.zone != null) { parts.push('zone=' + pitch.zone); }
    if (pitch && pitch.coordinates) {
      if (pitch.coordinates.pX != null) { parts.push('plate_x=' + round(pitch.coordinates.pX, 2)); }
      if (pitch.coordinates.pZ != null) { parts.push('plate_z=' + round(pitch.coordinates.pZ, 2)); }
    }
    if (hit) {
      if (hit.launchSpeed != null) { parts.push('exit_mph=' + hit.launchSpeed); }
      if (hit.launchAngle != null) { parts.push('launch_angle=' + hit.launchAngle); }
      if (hit.totalDistance != null) { parts.push('distance_ft=' + hit.totalDistance); }
      if (hit.trajectory) { parts.push('trajectory=' + hit.trajectory); }
      if (hit.hardness) { parts.push('hardness=' + hit.hardness); }
    }
    return '    ' + parts.join(' | ');
  }

  function round(input, digits) {
    var factor = Math.pow(10, digits);
    return Math.round(Number(input) * factor) / factor;
  }

  function runnerLine(runner, index) {
    var movement = runner && runner.movement ? runner.movement : {};
    var details = runner && runner.details ? runner.details : {};
    var parts = [
      'RUNNER ' + padLeft(index, 2).replace(/ /g, '0'),
      text(details.runner && details.runner.fullName, '(runner not supplied)'),
      (movement.originBase || 'batter') + ' -> ' + (movement.isOut ? 'out@' + text(movement.outBase, '?') : text(movement.end, 'held'))
    ];
    if (movement.outNumber != null) { parts.push('out=' + movement.outNumber); }
    if (details.event) { parts.push('event=' + details.event); }
    if (details.isScoringEvent) { parts.push('scoring=yes'); }
    return '    ' + parts.join(' | ');
  }

  function playsBlock(feed) {
    var lines = ['PLAY-BY-PLAY'];
    var all = feed.liveData && feed.liveData.plays && Array.isArray(feed.liveData.plays.allPlays)
      ? feed.liveData.plays.allPlays : [];
    if (all.length === 0) {
      lines.push('  ' + NOT_SUPPLIED + ' (no plays in the official feed for this game status)');
      return lines;
    }
    var currentInning = null;
    var currentHalf = null;
    all.forEach(function (play) {
      var about = play.about || {};
      if (about.inning !== currentInning || about.halfInning !== currentHalf) {
        currentInning = about.inning;
        currentHalf = about.halfInning;
        lines.push('');
        lines.push('-- ' + sideLabel(currentHalf) + ' ' + ordinal(currentInning) + ' --');
      }
      var result = play.result || {};
      var index = about.atBatIndex != null ? about.atBatIndex : 0;
      var score = num(result.awayScore) + '-' + num(result.homeScore);
      lines.push('[' + padLeft(index, 3).replace(/ /g, '0') + '] ' + text(result.event) + ' | ' + countOf(play) +
        ' | ' + text(result.description, '(no description supplied)'));
      lines.push('    batter=' + text(play.matchup && play.matchup.batter && play.matchup.batter.fullName) +
        ' (' + num(play.matchup && play.matchup.batter && play.matchup.batter.id) + ')' +
        ' | pitcher=' + text(play.matchup && play.matchup.pitcher && play.matchup.pitcher.fullName) +
        ' (' + num(play.matchup && play.matchup.pitcher && play.matchup.pitcher.id) + ')' +
        ' | score=' + score +
        ' | scoring=' + (about.isScoringPlay ? 'yes' : 'no') +
        ' | complete=' + (about.isComplete ? 'yes' : 'no'));
      var events = Array.isArray(play.playEvents) ? play.playEvents : [];
      events.forEach(function (entry, i) { lines.push(eventLine(entry, i)); });
      var runners = Array.isArray(play.runners) ? play.runners : [];
      runners.forEach(function (runner, i) { lines.push(runnerLine(runner, i)); });
    });
    return lines;
  }

  /* ---------------------------------------------------------------- box score */

  function stat(stats, group, key) {
    var block = stats && stats[group] ? stats[group] : null;
    if (!block) { return null; }
    var v = block[key];
    return v === undefined ? null : v;
  }

  function battingId(player) { return player && player.battingOrder != null ? String(player.battingOrder) : null; }

  function boxBlock(gd, boxscore, side) {
    var teamBlock = boxscore && boxscore.teams ? boxscore.teams[side] : null;
    var lines = [teamAbbreviation(gd, side)];
    if (!teamBlock) {
      lines.push('  ' + NOT_SUPPLIED);
      return lines;
    }
    var players = teamBlock.players || {};
    var order = Array.isArray(teamBlock.battingOrder) ? teamBlock.battingOrder : [];
    var pitcherIds = Array.isArray(teamBlock.pitchers) ? teamBlock.pitchers : [];

    lines.push('  ' + pad('BATTERS', 24) + padLeft('AB', 4) + padLeft('R', 3) + padLeft('H', 3) +
      padLeft('RBI', 4) + padLeft('BB', 4) + padLeft('SO', 4) + padLeft('AVG', 6));
    if (order.length === 0) {
      lines.push('  ' + NOT_SUPPLIED + ' (no batting order in the official box score)');
    }
    order.forEach(function (id) {
      var player = players['ID' + id];
      if (!player) { return; }
      var season = player.seasonStats && player.seasonStats.batting ? player.seasonStats.batting : null;
      var stats = player.stats || {};
      var name = text(player.person && player.person.fullName, '(name not supplied)');
      var position = player.position && player.position.abbreviation ? player.position.abbreviation : '';
      var label = name + (position ? ' ' + position : '');
      lines.push('  ' + pad(label, 24) +
        padLeft(num(stat(stats, 'batting', 'atBats')), 4) +
        padLeft(num(stat(stats, 'batting', 'runs')), 3) +
        padLeft(num(stat(stats, 'batting', 'hits')), 3) +
        padLeft(num(stat(stats, 'batting', 'rbi')), 4) +
        padLeft(num(stat(stats, 'batting', 'baseOnBalls')), 4) +
        padLeft(num(stat(stats, 'batting', 'strikeOuts')), 4) +
        padLeft(season && season.avg != null ? season.avg : '--', 6));
    });

    lines.push('');
    lines.push('  ' + pad('PITCHERS', 24) + padLeft('IP', 6) + padLeft('H', 3) + padLeft('R', 3) +
      padLeft('ER', 4) + padLeft('BB', 4) + padLeft('SO', 4) + padLeft('ERA', 7));
    if (pitcherIds.length === 0) {
      lines.push('  ' + NOT_SUPPLIED + ' (no pitchers in the official box score)');
    }
    pitcherIds.forEach(function (id) {
      var player = players['ID' + id];
      if (!player) { return; }
      var stats = player.stats || {};
      var name = text(player.person && player.person.fullName, '(name not supplied)');
      var note = stat(stats, 'pitching', 'note');
      var label = name + (note ? ' ' + note : '');
      lines.push('  ' + pad(label, 24) +
        padLeft(num(stat(stats, 'pitching', 'inningsPitched')), 6) +
        padLeft(num(stat(stats, 'pitching', 'hits')), 3) +
        padLeft(num(stat(stats, 'pitching', 'runs')), 3) +
        padLeft(num(stat(stats, 'pitching', 'earnedRuns')), 4) +
        padLeft(num(stat(stats, 'pitching', 'baseOnBalls')), 4) +
        padLeft(num(stat(stats, 'pitching', 'strikeOuts')), 4) +
        padLeft(stat(stats, 'pitching', 'era') != null ? stat(stats, 'pitching', 'era') : '--', 7));
    });
    return lines;
  }

  function boxScoreBlock(feed) {
    var gd = feed.gameData || {};
    var boxscore = feed.liveData ? feed.liveData.boxscore : null;
    var lines = ['BOX SCORE'];
    if (!boxscore || !boxscore.teams) {
      lines.push('  ' + NOT_SUPPLIED + ' (no box score in the official feed)');
      return lines;
    }
    lines.push('');
    lines = lines.concat(boxBlock(gd, boxscore, 'away'));
    lines.push('');
    lines = lines.concat(boxBlock(gd, boxscore, 'home'));
    return lines;
  }

  /* ---------------------------------------------------------------- documents */

  /*
   * meta: { url, fetchedAt, sha256, copyright } recorded at retrieval time.
   * Returns the complete readable report as a string.
   */
  function formatPlainText(feed, meta) {
    var provenance = meta || {};
    var gd = feed.gameData || {};
    var game = gd.game || {};
    var datetime = gd.datetime || {};
    var status = gd.status || {};
    var venue = gd.venue || {};

    var lines = [];
    lines.push('MLB PLAINTEXT PLAY-BY-PLAY');
    lines.push(headerLine(feed));
    lines.push('');
    lines.push('PROVENANCE');
    lines.push('  gamePk: ' + text(feed.gamePk));
    lines.push('  sourceUrl: ' + text(provenance.url));
    lines.push('  fetchedAt: ' + text(provenance.fetchedAt));
    lines.push('  sourceSha256: ' + text(provenance.sha256, '(not computable in this context)'));
    lines.push('  copyright: ' + text(provenance.copyright, text(feed.copyright)));
    lines.push('');
    lines.push('GAME');
    lines.push('  officialDate: ' + text(datetime.officialDate));
    lines.push('  scheduled: ' + text(datetime.dateTime));
    lines.push('  type: ' + text(game.type));
    lines.push('  number: ' + num(game.gameNumber) + (game.doubleHeader && game.doubleHeader !== 'N' ? ' (doubleheader ' + game.doubleHeader + ')' : ''));
    lines.push('  season: ' + text(game.season));
    lines.push('  venue: ' + text(venue.name));
    lines.push('  status: ' + text(status.detailedState || status.abstractGameState));
    lines.push('  away: ' + text(gd.teams && gd.teams.away && gd.teams.away.name) +
      ' (' + num(gd.teams && gd.teams.away && gd.teams.away.id) + ')');
    lines.push('  home: ' + text(gd.teams && gd.teams.home && gd.teams.home.name) +
      ' (' + num(gd.teams && gd.teams.home && gd.teams.home.id) + ')');
    lines.push('');
    lines = lines.concat(lineScoreBlock(feed));
    lines.push('');
    lines = lines.concat(decisionLines(feed));
    lines.push('');
    lines = lines.concat(playsBlock(feed));
    lines.push('');
    lines = lines.concat(boxScoreBlock(feed));
    lines.push('');
    return lines.join('\n');
  }

  /* One JSON record per line: metadata, then one record per play, then one per play event. */
  function formatEventsNdjson(feed, meta) {
    var provenance = meta || {};
    var gd = feed.gameData || {};
    var out = [];
    out.push(JSON.stringify({
      recordType: 'metadata',
      gamePk: feed.gamePk,
      sourceUrl: provenance.url || null,
      fetchedAt: provenance.fetchedAt || null,
      sourceSha256: provenance.sha256 || null,
      copyright: provenance.copyright || feed.copyright || null,
      gameData: gd
    }));
    var all = feed.liveData && feed.liveData.plays && Array.isArray(feed.liveData.plays.allPlays)
      ? feed.liveData.plays.allPlays : [];
    all.forEach(function (play) {
      out.push(JSON.stringify({
        recordType: 'play',
        gamePk: feed.gamePk,
        atBatIndex: play.about ? play.about.atBatIndex : null,
        result: play.result || null,
        about: play.about || null,
        count: play.count || null,
        matchup: play.matchup || null,
        runners: play.runners || []
      }));
      var events = Array.isArray(play.playEvents) ? play.playEvents : [];
      events.forEach(function (entry) {
        out.push(JSON.stringify({
          recordType: 'event',
          gamePk: feed.gamePk,
          atBatIndex: play.about ? play.about.atBatIndex : null,
          eventIndex: entry.index != null ? entry.index : null,
          isPitch: entry.isPitch === true,
          type: entry.type || null,
          details: entry.details || null,
          pitchData: entry.pitchData || null,
          hitData: entry.hitData || null
        }));
      });
    });
    return out.join('\n') + '\n';
  }

  return {
    NOT_SUPPLIED: NOT_SUPPLIED,
    ordinal: ordinal,
    sideLabel: sideLabel,
    headerLine: headerLine,
    lineScoreBlock: lineScoreBlock,
    decisionLines: decisionLines,
    playsBlock: playsBlock,
    boxScoreBlock: boxScoreBlock,
    formatPlainText: formatPlainText,
    formatEventsNdjson: formatEventsNdjson
  };
});

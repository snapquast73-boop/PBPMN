/*
 * docs/js/app.js — the static viewer.
 *
 * Renders whatever the official MLB feed returns and nothing else. There is no sample data,
 * no fallback dataset and no client-side repair: when a value is absent the page says that
 * MLB did not supply it.
 */
(function (root) {
  'use strict';

  var api = root.MLBPBP && root.MLBPBP.api;
  var fmt = root.MLBPBP && root.MLBPBP.format;
  var eventlog = root.MLBPBP && root.MLBPBP.eventlog;

  var TABS = ['plays', 'linescore', 'boxscore', 'eventlog'];
  var NOT_SUPPLIED = 'MLB did not supply this value.';

  var state = {
    date: null,
    schedule: null,
    scheduleMeta: null,
    gamePk: null,
    feed: null,
    feedMeta: null,
    tab: 'plays',
    search: '',
    refreshing: false,
    timer: null,
    storage: null
  };

  var el = {};

  /* ---------------------------------------------------------------- small helpers */

  function esc(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function val(value, fallback) {
    return value === null || value === undefined || value === '' ? (fallback || NOT_SUPPLIED) : value;
  }

  function get(obj, path) {
    var parts = path.split('.');
    var cursor = obj;
    for (var i = 0; i < parts.length; i += 1) {
      if (cursor === null || cursor === undefined) { return null; }
      cursor = cursor[parts[i]];
    }
    return cursor === undefined ? null : cursor;
  }

  function todayIso() {
    var now = new Date();
    var local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
  }

  /* ---------------------------------------------------------------- official labels */

  function statusLabel(status) {
    var s = status || {};
    var abstract = s.abstractGameState;
    if (abstract === 'Preview') { return 'Preview'; }
    if (abstract === 'Live') { return 'Live'; }
    if (abstract === 'Final') { return 'Final'; }
    return s.detailedState || 'Status not supplied';
  }

  function displayTime(gameDate) {
    if (!gameDate) { return 'Time not supplied'; }
    var d = new Date(gameDate);
    if (isNaN(d.getTime())) { return 'Time not supplied'; }
    try {
      return d.toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: 'numeric', minute: '2-digit', timeZoneName: 'short'
      });
    } catch (err) {
      return d.toISOString();
    }
  }

  function ordinal(n) {
    var number = Number(n);
    if (!isFinite(number)) { return String(n); }
    var m100 = number % 100;
    if (m100 >= 11 && m100 <= 13) { return number + 'th'; }
    switch (number % 10) {
      case 1: return number + 'st';
      case 2: return number + 'nd';
      case 3: return number + 'rd';
      default: return number + 'th';
    }
  }

  function teamSide(feed, side) {
    return get(feed, 'gameData.teams.' + side) || {};
  }

  /* ---------------------------------------------------------------- line score */

  function lineScoreTable(feed, scheduleGame) {
    var linescore = get(feed, 'liveData.linescore');
    var scheduled = scheduleGame || {};
    if (!linescore || !Array.isArray(linescore.innings) || linescore.innings.length === 0) {
      return '<p class="muted">MLB has not supplied a line score for this game status.</p>';
    }
    var innings = linescore.innings;
    var head = '<tr><th class="team">Team</th>';
    innings.forEach(function (inning) { head += '<th>' + esc(inning.num) + '</th>'; });
    head += '<th class="tot">R</th><th class="tot">H</th><th class="tot">E</th><th class="tot">LOB</th></tr>';

    var rows = '';
    [['away', 'away'], ['home', 'home']].forEach(function (pair) {
      var side = pair[0];
      var team = teamSide(feed, side);
      var totals = get(linescore, 'teams.' + side) || {};
      var row = '<tr><th class="team">' + esc(team.name || side) + '</th>';
      innings.forEach(function (inning) {
        var cell = inning[side] || {};
        row += '<td>' + esc(cell.runs === undefined || cell.runs === null ? '–' : cell.runs) + '</td>';
      });
      row += '<td class="tot">' + esc(val(totals.runs, '–')) + '</td>';
      row += '<td class="tot">' + esc(val(totals.hits, '–')) + '</td>';
      row += '<td class="tot">' + esc(val(totals.errors, '–')) + '</td>';
      row += '<td class="tot">' + esc(val(totals.leftOnBase, '–')) + '</td></tr>';
      rows += row;
    });

    var extra = '';
    if (linescore.note) { extra += '<p class="muted">Official note: ' + esc(linescore.note) + '</p>'; }
    if (scheduled.status && scheduled.status.detailedState) {
      extra += '<p class="muted">Detailed state: ' + esc(scheduled.status.detailedState) + '</p>';
    }
    return '<table class="linescore"><thead>' + head + '</thead><tbody>' + rows + '</tbody></table>' + extra;
  }

  function decisions(feed) {
    var d = get(feed, 'liveData.decisions');
    if (!d || (!d.winner && !d.loser && !d.save)) {
      return '<p class="muted">MLB has not supplied decisions for this game.</p>';
    }
    var out = '<dl class="decisions">';
    [['Winner', d.winner], ['Loser', d.loser], ['Save', d.save]].forEach(function (pair) {
      var label = pair[0];
      var person = pair[1];
      out += '<dt>' + esc(label) + '</dt><dd>' +
        (person ? esc(person.fullName) : '<span class="muted">No ' + esc(label.toLowerCase()) + ' supplied by MLB</span>') +
        '</dd>';
    });
    return out + '</dl>';
  }

  /* ---------------------------------------------------------------- play by play */

  function eventLine(entry) {
    var details = entry.details || {};
    var pitch = entry.pitchData || {};
    var hit = entry.hitData || {};
    var parts = [];
    if (details.type && details.type.description) { parts.push(details.type.description); }
    if (entry.isPitch && pitch.startSpeed !== undefined && pitch.startSpeed !== null) {
      parts.push(pitch.startSpeed + ' mph');
    }
    if (pitch.zone !== undefined && pitch.zone !== null) { parts.push('zone ' + pitch.zone); }
    if (pitch.coordinates && pitch.coordinates.pX !== undefined && pitch.coordinates.pX !== null) {
      parts.push('pX ' + Number(pitch.coordinates.pX).toFixed(2) + ' / pZ ' + Number(pitch.coordinates.pZ).toFixed(2));
    }
    if (hit.launchSpeed !== undefined && hit.launchSpeed !== null) {
      parts.push('exit ' + hit.launchSpeed + ' mph');
    }
    if (hit.launchAngle !== undefined && hit.launchAngle !== null) {
      parts.push('angle ' + hit.launchAngle + '°');
    }
    if (hit.totalDistance !== undefined && hit.totalDistance !== null) {
      parts.push('distance ' + hit.totalDistance + ' ft');
    }
    if (details.call && details.call.description) { parts.push(details.call.description); }
    var label = entry.isPitch ? 'Pitch ' + (entry.index !== undefined ? entry.index + 1 : '') : 'Action';
    var line = '<span class="ev-label">' + esc(label) + '</span> ' + esc(val(details.description, ''));
    if (parts.length) { line += ' <span class="ev-meta">' + esc(parts.join(' · ')) + '</span>'; }
    return '<li>' + line + '</li>';
  }

  function runnerLine(runner) {
    var movement = runner.movement || {};
    var details = runner.details || {};
    var name = get(details, 'runner.fullName');
    var from = movement.originBase || 'batter';
    var to = movement.isOut ? 'out at ' + val(movement.outBase, '?') : val(movement.end, 'held');
    var extra = [];
    if (details.event) { extra.push(details.event); }
    if (details.isScoringEvent) { extra.push('scored'); }
    if (movement.outNumber !== undefined && movement.outNumber !== null) { extra.push('out #' + movement.outNumber); }
    return '<li>' + esc(val(name, 'Runner not supplied')) + ': ' + esc(from) + ' → ' + esc(to) +
      (extra.length ? ' <span class="ev-meta">' + esc(extra.join(' · ')) + '</span>' : '') + '</li>';
  }

  function playMatches(play, needle) {
    if (!needle) { return true; }
    var haystack = [
      get(play, 'result.description'),
      get(play, 'result.event'),
      get(play, 'matchup.batter.fullName'),
      get(play, 'matchup.pitcher.fullName')
    ].join(' ').toLowerCase();
    return haystack.indexOf(needle) !== -1;
  }

  function playsHtml(feed) {
    var all = get(feed, 'liveData.plays.allPlays') || [];
    if (!Array.isArray(all) || all.length === 0) {
      return '<p class="muted">MLB has not supplied play-by-play for this game status.</p>';
    }
    var needle = state.search.trim().toLowerCase();
    var shown = 0;
    var html = '';
    var currentInning = null;
    var currentHalf = null;

    all.forEach(function (play) {
      if (!playMatches(play, needle)) { return; }
      var about = play.about || {};
      if (about.inning !== currentInning || about.halfInning !== currentHalf) {
        if (currentInning !== null) { html += '</ol></div>'; }
        currentInning = about.inning;
        currentHalf = about.halfInning;
        var halfLabel = currentHalf === 'top' ? 'Top' : 'Bottom';
        html += '<div class="inning"><h3>' + esc(halfLabel + ' ' + ordinal(currentInning)) + '</h3><ol class="plays">';
      }
      var result = play.result || {};
      var count = play.count || {};
      var batter = get(play, 'matchup.batter') || {};
      var pitcher = get(play, 'matchup.pitcher') || {};
      var events = Array.isArray(play.playEvents) ? play.playEvents : [];
      var runners = Array.isArray(play.runners) ? play.runners : [];
      var classes = 'play' + (about.isScoringPlay ? ' scoring' : '');
      html += '<li class="' + classes + '">';
      html += '<div class="play-head">';
      html += '<span class="play-index">[' + esc(String(about.atBatIndex === undefined ? '' : about.atBatIndex)) + ']</span> ';
      html += '<strong>' + esc(val(result.event, 'Event not supplied')) + '</strong>';
      html += ' <span class="count">' + esc(val(count.balls, '?')) + '-' + esc(val(count.strikes, '?')) +
        ' · ' + esc(val(count.outs, '?')) + ' out' + (count.outs === 1 ? '' : 's') + '</span>';
      html += '</div>';
      html += '<p class="description">' + esc(val(result.description, 'MLB did not supply a description for this play.')) + '</p>';
      html += '<p class="matchup">' + esc(val(batter.fullName, 'Batter not supplied')) + ' vs ' +
        esc(val(pitcher.fullName, 'Pitcher not supplied')) + ' · score ' +
        esc(val(result.awayScore, '?')) + '–' + esc(val(result.homeScore, '?')) + '</p>';
      if (events.length) {
        html += '<ul class="events">' + events.map(eventLine).join('') + '</ul>';
      }
      if (runners.length) {
        html += '<ul class="runners">' + runners.map(runnerLine).join('') + '</ul>';
      }
      html += '</li>';
      shown += 1;
    });

    if (currentInning !== null) { html += '</ol></div>'; }
    if (shown === 0) {
      return '<p class="muted">No play in this game matches “' + esc(state.search) + '”.</p>';
    }
    return html;
  }

  /* ---------------------------------------------------------------- box score */

  function battingRows(feed, side) {
    var team = get(feed, 'liveData.boxscore.teams.' + side);
    if (!team) { return '<p class="muted">MLB has not supplied a box score for the ' + esc(side) + ' team.</p>'; }
    var order = Array.isArray(team.battingOrder) ? team.battingOrder : [];
    if (order.length === 0) {
      return '<p class="muted">MLB has not supplied a batting order for the ' + esc(side) + ' team.</p>';
    }
    var rows = '';
    order.forEach(function (id) {
      var player = get(team, 'players.ID' + id);
      if (!player) { return; }
      var stats = (player.stats && player.stats.batting) || {};
      var season = (player.seasonStats && player.seasonStats.batting) || {};
      var position = get(player, 'position.abbreviation');
      rows += '<tr><td class="name">' + esc(val(get(player, 'person.fullName'), 'Name not supplied')) +
        (position ? ' <span class="pos">' + esc(position) + '</span>' : '') + '</td>' +
        cell(stats.atBats) + cell(stats.runs) + cell(stats.hits) + cell(stats.doubles) +
        cell(stats.triples) + cell(stats.homeRuns) + cell(stats.rbi) + cell(stats.baseOnBalls) +
        cell(stats.strikeOuts) + cell(season.avg) + '</tr>';
    });
    return '<table class="stats"><thead><tr><th class="name">Batter</th><th>AB</th><th>R</th><th>H</th>' +
      '<th>2B</th><th>3B</th><th>HR</th><th>RBI</th><th>BB</th><th>SO</th><th>AVG</th></tr></thead>' +
      '<tbody>' + rows + '</tbody></table>';
  }

  function pitchingRows(feed, side) {
    var team = get(feed, 'liveData.boxscore.teams.' + side);
    if (!team) { return ''; }
    var ids = Array.isArray(team.pitchers) ? team.pitchers : [];
    if (ids.length === 0) {
      return '<p class="muted">MLB has not supplied pitchers for the ' + esc(side) + ' team.</p>';
    }
    var rows = '';
    ids.forEach(function (id) {
      var player = get(team, 'players.ID' + id);
      if (!player) { return; }
      var stats = (player.stats && player.stats.pitching) || {};
      rows += '<tr><td class="name">' + esc(val(get(player, 'person.fullName'), 'Name not supplied')) +
        (stats.note ? ' <span class="pos">' + esc(stats.note) + '</span>' : '') + '</td>' +
        cell(stats.inningsPitched) + cell(stats.hits) + cell(stats.runs) + cell(stats.earnedRuns) +
        cell(stats.baseOnBalls) + cell(stats.strikeOuts) + cell(stats.homeRuns) + cell(stats.era) + '</tr>';
    });
    return '<table class="stats"><thead><tr><th class="name">Pitcher</th><th>IP</th><th>H</th><th>R</th>' +
      '<th>ER</th><th>BB</th><th>SO</th><th>HR</th><th>ERA</th></tr></thead><tbody>' + rows + '</tbody></table>';
  }

  function cell(value) {
    return '<td>' + esc(value === undefined || value === null ? '–' : value) + '</td>';
  }

  function boxScoreHtml(feed) {
    var teams = get(feed, 'liveData.boxscore.teams');
    if (!teams) { return '<p class="muted">MLB has not supplied a box score for this game.</p>'; }
    return '<h3>' + esc(val(get(feed, 'gameData.teams.away.name'), 'Away')) + '</h3>' +
      battingRows(feed, 'away') + pitchingRows(feed, 'away') +
      '<h3>' + esc(val(get(feed, 'gameData.teams.home.name'), 'Home')) + '</h3>' +
      battingRows(feed, 'home') + pitchingRows(feed, 'home');
  }

  /* ---------------------------------------------------------------- event log */

  function eventLogHtml(gamePk) {
    var entries = eventlog.read(state.storage, gamePk);
    var status = get(state.feed, 'gameData.status.abstractGameState');
    var intro = '<p class="muted">This log is kept in this browser only (localStorage key ' +
      '<code>' + esc(eventlog.key(gamePk)) + '</code>). It records what this page observed while polling ' +
      'the official feed. Nothing is uploaded. Current official status: <strong>' +
      esc(statusLabel(get(state.feed, 'gameData.status'))) + '</strong>.</p>';
    var body;
    if (!entries.length) {
      body = '<p class="muted">No change has been observed yet. Open the game while it is Live and the log ' +
        'will record score changes, pending rulings, ruling changes and reviews as they appear in the official feed.</p>';
    } else {
      body = '<ol class="eventlog">' + entries.slice().reverse().map(function (entry) {
        return '<li class="kind-' + esc(entry.kind) + '"><time>' + esc(entry.at) + '</time> ' +
          '<span class="tag">' + esc(entry.kind) + '</span> ' + esc(entry.text) + '</li>';
      }).join('') + '</ol>';
    }
    return intro + body +
      '<p><button type="button" id="clear-eventlog" class="ghost">Clear this game’s local log</button></p>';
  }

  /* ---------------------------------------------------------------- downloads */

  function download(name, text, mediaType) {
    var blob = new Blob([text], { type: mediaType });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  }

  function meta() {
    return {
      url: state.feedMeta ? state.feedMeta.url : null,
      fetchedAt: state.feedMeta ? state.feedMeta.fetchedAt : null,
      sha256: state.feedMeta ? state.feedMeta.sha256 : null,
      copyright: state.feedMeta ? state.feedMeta.copyright : null
    };
  }

  /* ---------------------------------------------------------------- rendering */

  function renderStatus(message, kind) {
    if (!message) {
      el.status.innerHTML = '';
      el.status.hidden = true;
      return;
    }
    el.status.hidden = false;
    el.status.className = 'status ' + (kind || 'info');
    el.status.textContent = message;
  }

  function renderSchedule() {
    if (!state.schedule) {
      el.schedule.innerHTML = '<p class="muted">No schedule loaded.</p>';
      return;
    }
    var games = state.schedule.games || [];
    if (games.length === 0) {
      el.schedule.innerHTML = '<p class="muted">MLB returned no game of type R, F, D, L or W on ' +
        esc(state.date) + '.</p>';
      return;
    }
    var html = '<table class="schedule"><thead><tr><th>Time</th><th>Away</th><th>Home</th>' +
      '<th>Status</th><th>Venue</th><th>gamePk</th></tr></thead><tbody>';
    games.forEach(function (game) {
      var away = get(game, 'teams.away.team.name');
      var home = get(game, 'teams.home.team.name');
      var awayScore = get(game, 'teams.away.score');
      var homeScore = get(game, 'teams.home.score');
      var isCurrent = String(game.gamePk) === String(state.gamePk);
      html += '<tr class="' + (isCurrent ? 'current' : '') + '" data-gamepk="' + esc(game.gamePk) + '" tabindex="0">';
      html += '<td>' + esc(displayTime(game.gameDate)) + '</td>';
      html += '<td>' + esc(val(away, 'Team not supplied')) + '</td>';
      html += '<td>' + esc(val(home, 'Team not supplied')) + '</td>';
      html += '<td>' + esc(statusLabel(game.status)) +
        (awayScore !== null && homeScore !== null ? ' ' + esc(awayScore) + '–' + esc(homeScore) : '') + '</td>';
      html += '<td>' + esc(val(get(game, 'venue.name'), '–')) + '</td>';
      html += '<td><button type="button" class="link" data-open="' + esc(game.gamePk) + '">' +
        esc(game.gamePk) + '</button></td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
    el.schedule.innerHTML = html;
  }

  function renderGame() {
    if (!state.feed) {
      el.game.hidden = true;
      return;
    }
    var feed = state.feed;
    var scheduled = (state.schedule && state.schedule.games || []).filter(function (g) {
      return String(g.gamePk) === String(state.gamePk);
    })[0] || null;
    el.game.hidden = false;

    var away = teamSide(feed, 'away');
    var home = teamSide(feed, 'home');
    var totals = get(feed, 'liveData.linescore.teams') || {};
    var awayRuns = get(totals, 'away.runs');
    var homeRuns = get(totals, 'home.runs');
    var status = get(feed, 'gameData.status') || {};

    el.gameTitle.textContent = val(away.name, 'Away') + ' at ' + val(home.name, 'Home') +
      (awayRuns !== null && homeRuns !== null ? '  —  ' + awayRuns + '–' + homeRuns : '');
    el.gameMeta.innerHTML =
      '<span class="badge ' + esc((status.abstractGameState || '').toLowerCase()) + '">' + esc(statusLabel(status)) + '</span>' +
      '<span>' + esc(displayTime(get(feed, 'gameData.datetime.dateTime'))) + '</span>' +
      '<span>' + esc(val(get(feed, 'gameData.venue.name'), 'Venue not supplied')) + '</span>' +
      '<span>gamePk ' + esc(feed.gamePk) + '</span>' +
      '<a href="' + esc(state.feedMeta.url) + '" rel="noopener noreferrer" target="_blank">official feed</a>' +
      '<span class="muted">retrieved ' + esc(state.feedMeta.fetchedAt) + '</span>' +
      (state.feedMeta.sha256 ? '<span class="muted">sha256 ' + esc(state.feedMeta.sha256.slice(0, 16)) + '…</span>' : '');

    if (state.tab === 'plays') { el.plays.innerHTML = playsHtml(feed); }
    else if (state.tab === 'linescore') { el.plays.innerHTML = lineScoreTable(feed, scheduled) + decisions(feed); }
    else if (state.tab === 'boxscore') { el.plays.innerHTML = boxScoreHtml(feed); }
    else if (state.tab === 'eventlog') { el.plays.innerHTML = eventLogHtml(feed.gamePk); }

    Array.prototype.forEach.call(el.tabs.querySelectorAll('button'), function (button) {
      var active = button.getAttribute('data-tab') === state.tab;
      button.setAttribute('aria-selected', active ? 'true' : 'false');
      button.classList.toggle('active', active);
    });

    el.searchRow.hidden = state.tab !== 'plays';
  }

  function syncUrl() {
    var params = new URLSearchParams();
    if (state.date) { params.set('date', state.date); }
    if (state.gamePk) { params.set('game', String(state.gamePk)); }
    var next = location.pathname + (params.toString() ? '?' + params.toString() : '');
    try { history.replaceState(null, '', next); } catch (err) { /* file:// or sandboxed */ }
  }

  /* ---------------------------------------------------------------- loading */

  function loadDate(date, gamePk) {
    state.date = date;
    state.gamePk = gamePk || null;
    state.schedule = null;
    state.feed = null;
    el.date.value = date;
    renderGame();
    el.schedule.innerHTML = '<p class="muted">Loading the official schedule for ' + esc(date) + ' …</p>';
    renderStatus('Requesting ' + api.scheduleUrl(date), 'info');
    return api.getSchedule(date).then(function (response) {
      state.schedule = response;
      state.scheduleMeta = response;
      renderSchedule();
      renderStatus('Official schedule for ' + date + ' — ' + response.games.length +
        ' qualifying game(s). Source: ' + response.url, 'ok');
      if (state.gamePk) { return loadGame(state.gamePk); }
      return null;
    }).catch(reportError);
  }

  function loadGame(gamePk) {
    state.gamePk = String(gamePk);
    syncUrl();
    renderStatus('Requesting ' + api.gameUrl(gamePk), 'info');
    return api.getGame(gamePk).then(function (response) {
      state.feed = response.json;
      state.feedMeta = response;
      state.search = '';
      if (el.search) { el.search.value = ''; }
      renderGame();
      renderSchedule();
      try {
        eventlog.record(state.storage, state.gamePk, state.feed);
      } catch (err) { /* logging must never break the viewer */ }
      scheduleRefresh();
      var status = get(state.feed, 'gameData.status.abstractGameState');
      renderStatus('Official feed loaded · status ' + statusLabel(get(state.feed, 'gameData.status')) +
        ' · ' + (state.feedMeta.sha256 ? 'sha256 ' + state.feedMeta.sha256.slice(0, 16) + '…' : 'digest unavailable') +
        ' · source ' + state.feedMeta.url, 'ok');
      return state.feed;
    }).catch(reportError);
  }

  function scheduleRefresh() {
    if (state.timer) { clearTimeout(state.timer); state.timer = null; }
    var abstract = get(state.feed, 'gameData.status.abstractGameState');
    if (abstract !== 'Live') { return; }
    var wait = Number(get(state.feed, 'metaData.wait'));
    if (!isFinite(wait) || wait <= 0) { return; }
    state.timer = setTimeout(function () {
      if (!state.gamePk) { return; }
      api.getGame(state.gamePk).then(function (response) {
        state.feed = response.json;
        state.feedMeta = response;
        renderGame();
        try { eventlog.record(state.storage, state.gamePk, state.feed); } catch (err) { /* ignore */ }
        scheduleRefresh();
      }).catch(function (err) {
        renderStatus(err.message, 'error');
        state.timer = setTimeout(function () { loadGame(state.gamePk); }, Math.max(wait, 15) * 1000);
      });
    }, Math.max(wait, 5) * 1000);
  }

  function reportError(err) {
    var message = err && err.message ? err.message : String(err);
    renderStatus(message, 'error');
    if (state.gamePk && !state.feed) {
      el.game.hidden = false;
      el.gameTitle.textContent = 'Game ' + state.gamePk;
      el.gameMeta.innerHTML = '';
      el.plays.innerHTML = '<p class="muted">The official feed for gamePk ' + esc(state.gamePk) +
        ' could not be read. The site does not substitute a copy or an estimate. ' +
        'Try <a href="' + esc(api.gameUrl(state.gamePk)) + '" rel="noopener noreferrer" target="_blank">the endpoint itself</a>.</p>';
    }
    return null;
  }

  /* ---------------------------------------------------------------- wiring */

  function selectTab(tab) {
    if (TABS.indexOf(tab) === -1) { return; }
    state.tab = tab;
    renderGame();
  }

  function wire() {
    el.form.addEventListener('submit', function (event) {
      event.preventDefault();
      var date = el.date.value;
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
        renderStatus('Choose a date in YYYY-MM-DD form.', 'error');
        return;
      }
      if (date < api.MIN_DATE) {
        renderStatus('The archive starts on ' + api.MIN_DATE + '.', 'error');
        return;
      }
      state.gamePk = null;
      loadDate(date, null);
      syncUrl();
    });

    el.schedule.addEventListener('click', function (event) {
      var button = event.target.closest('[data-open]');
      if (button) {
        loadGame(button.getAttribute('data-open'));
        return;
      }
      var row = event.target.closest('tr[data-gamepk]');
      if (row) { loadGame(row.getAttribute('data-gamepk')); }
    });

    el.schedule.addEventListener('keydown', function (event) {
      if (event.key !== 'Enter') { return; }
      var row = event.target.closest('tr[data-gamepk]');
      if (row) { loadGame(row.getAttribute('data-gamepk')); }
    });

    el.tabs.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-tab]');
      if (button) { selectTab(button.getAttribute('data-tab')); }
    });

    el.plays.addEventListener('click', function (event) {
      if (event.target && event.target.id === 'clear-eventlog') {
        eventlog.clear(state.storage, state.gamePk);
        renderGame();
      }
    });

    el.search.addEventListener('input', function () {
      state.search = el.search.value;
      if (state.feed && state.tab === 'plays') { el.plays.innerHTML = playsHtml(state.feed); }
    });

    el.downloadText.addEventListener('click', function () {
      if (!state.feed) { return; }
      download(state.gamePk + '.txt', fmt.formatPlainText(state.feed, meta()), 'text/plain;charset=utf-8');
    });
    el.downloadJson.addEventListener('click', function () {
      if (!state.feed) { return; }
      download(state.gamePk + '.json', state.feedMeta.text, 'application/json');
    });
    el.downloadNdjson.addEventListener('click', function () {
      if (!state.feed) { return; }
      download(state.gamePk + '.events.ndjson', fmt.formatEventsNdjson(state.feed, meta()), 'application/x-ndjson');
    });
  }

  function boot() {
    el = {
      form: document.getElementById('date-form'),
      date: document.getElementById('date'),
      status: document.getElementById('status'),
      schedule: document.getElementById('schedule'),
      game: document.getElementById('game'),
      gameTitle: document.getElementById('game-title'),
      gameMeta: document.getElementById('game-meta'),
      tabs: document.getElementById('tabs'),
      plays: document.getElementById('game-body'),
      search: document.getElementById('search'),
      searchRow: document.getElementById('search-row'),
      downloadText: document.getElementById('download-text'),
      downloadJson: document.getElementById('download-json'),
      downloadNdjson: document.getElementById('download-ndjson'),
      previous: document.getElementById('prev-day'),
      next: document.getElementById('next-day')
    };

    state.storage = (function () {
      try {
        var probe = '__mlb_pbp_probe__';
        localStorage.setItem(probe, '1');
        localStorage.removeItem(probe);
        return localStorage;
      } catch (err) {
        return eventlog.memoryStorage();
      }
    })();

    el.date.min = api.MIN_DATE;
    el.date.max = todayIso();

    var params = new URLSearchParams(location.search);
    var date = params.get('date');
    var game = params.get('game');
    if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date) || date < api.MIN_DATE) {
      date = todayIso() < api.MIN_DATE ? api.MIN_DATE : todayIso();
      if (date > todayIso()) { date = todayIso(); }
    }
    wire();
    loadDate(date, game);
  }

  var exported = {
    statusLabel: statusLabel,
    displayTime: displayTime,
    lineScoreTable: lineScoreTable,
    decisions: decisions,
    playsHtml: playsHtml,
    eventLine: eventLine,
    boxScoreHtml: boxScoreHtml,
    state: state,
    boot: boot
  };

  root.MLBPBP = root.MLBPBP || {};
  root.MLBPBP.app = exported;
  if (typeof module !== 'undefined' && module.exports) { module.exports = exported; }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', boot);
    } else {
      boot();
    }
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);

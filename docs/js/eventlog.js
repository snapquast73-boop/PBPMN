/*
 * docs/js/eventlog.js — the per-game local Event log.
 *
 * While a game is Live the page polls the official feed. Each poll is reduced to a small
 * snapshot; comparing the previous snapshot with the new one produces log entries for:
 *
 *   game-state       official status changed (Preview → Live → Final, delayed, suspended …)
 *   score            a side's run total in liveData.linescore.teams changed
 *   scoring-pending  a play appeared whose about.isComplete is false (ruling not final)
 *   ruling-resolved  that play later became about.isComplete = true
 *   ruling-change    an already-existing play's result.event / eventType / description changed
 *   review-open      a play gained about.hasReview with reviewDetails.inProgress = true
 *   review-decided   that review closed (reviewDetails.isOverturned true = overturned)
 *
 * Everything written comes from the official response; nothing is inferred beyond the
 * comparison itself. Entries live in the browser (localStorage) and are never transmitted.
 * The storage object is injected so this file can be unit-tested in Node.
 */
(function (root, factory) {
  'use strict';
  var mod = factory();
  if (typeof module !== 'undefined' && module.exports) { module.exports = mod; }
  root.MLBPBP = root.MLBPBP || {};
  root.MLBPBP.eventlog = mod;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var PREFIX = 'mlb-pbp:eventlog:v1:';
  var MAX_ENTRIES = 500;

  function key(gamePk) {
    return PREFIX + String(gamePk);
  }

  function playReview(play) {
    if (play && play.reviewDetails) { return play.reviewDetails; }
    var events = play && Array.isArray(play.playEvents) ? play.playEvents : [];
    for (var i = 0; i < events.length; i += 1) {
      if (events[i] && events[i].reviewDetails) { return events[i].reviewDetails; }
    }
    return null;
  }

  /* Reduce a full official feed to the minimum needed to detect changes between polls. */
  function snapshot(feed) {
    var linescore = feed && feed.liveData && feed.liveData.linescore ? feed.liveData.linescore : {};
    var teams = linescore.teams || {};
    var plays = {};
    var all = feed && feed.liveData && feed.liveData.plays && Array.isArray(feed.liveData.plays.allPlays)
      ? feed.liveData.plays.allPlays : [];
    all.forEach(function (play) {
      var about = play.about || {};
      var result = play.result || {};
      var review = playReview(play);
      plays[String(about.atBatIndex)] = {
        event: result.event || null,
        eventType: result.eventType || null,
        description: result.description || null,
        isScoringPlay: about.isScoringPlay === true,
        isComplete: about.isComplete === true,
        hasReview: about.hasReview === true,
        reviewType: review && review.reviewType ? review.reviewType : null,
        inProgress: review ? review.inProgress === true : null,
        isOverturned: review ? review.isOverturned === true : null,
        inning: about.inning != null ? about.inning : null,
        halfInning: about.halfInning || null
      };
    });
    var status = feed && feed.gameData && feed.gameData.status ? feed.gameData.status : {};
    return {
      status: status.detailedState || status.abstractGameState || null,
      abstractState: status.abstractGameState || null,
      awayRuns: teams.away && teams.away.runs != null ? teams.away.runs : null,
      homeRuns: teams.home && teams.home.runs != null ? teams.home.runs : null,
      currentInning: linescore.currentInning != null ? linescore.currentInning : null,
      inningState: linescore.inningState || null,
      plays: plays
    };
  }

  function describePlay(play) {
    var where = '';
    if (play.inning != null && play.halfInning) {
      where = play.halfInning === 'top' ? 'top ' : 'bottom ';
      where += play.inning;
      where += ' — ';
    }
    return where + (play.event || play.eventType || 'play');
  }

  /*
   * Compare two snapshots and return the entries that describe what changed.
   * at: ISO timestamp to stamp on the entries.
   */
  function diff(previous, next, at) {
    var entries = [];
    if (!next) { return entries; }
    var stamp = at || new Date().toISOString();

    function push(kind, text, extra) {
      var entry = { at: stamp, kind: kind, text: text };
      if (extra) {
        Object.keys(extra).forEach(function (k) { entry[k] = extra[k]; });
      }
      entries.push(entry);
    }

    if (!previous) {
      push('game-state', 'Watching began — official status: ' + (next.status || 'unknown'));
      /* A game joined mid-review or mid-ruling should still say what it found. */
      Object.keys(next.plays).forEach(function (index) {
        var play = next.plays[index];
        if (play.isComplete === false) {
          push('scoring-pending', 'Ruling pending — ' + describePlay(play) +
            ' (official about.isComplete = false)', { atBatIndex: Number(index) });
        }
        if (play.hasReview && play.inProgress === true) {
          push('review-open', 'Review opened — ' + describePlay(play) +
            ' (reviewType ' + (play.reviewType || 'not supplied') + ')', { atBatIndex: Number(index) });
        }
      });
      return entries;
    }

    if (previous.status !== next.status) {
      push('game-state', 'Status changed: ' + (previous.status || 'unknown') + ' → ' + (next.status || 'unknown'));
    }

    if (previous.awayRuns !== next.awayRuns || previous.homeRuns !== next.homeRuns) {
      push('score', 'Score changed: ' + fmt(previous.awayRuns) + '-' + fmt(previous.homeRuns) +
        ' → ' + fmt(next.awayRuns) + '-' + fmt(next.homeRuns) + ' (away-home)', {
        awayRuns: next.awayRuns,
        homeRuns: next.homeRuns
      });
    }

    Object.keys(next.plays).forEach(function (index) {
      var now = next.plays[index];
      var before = previous.plays[index];
      var where = describePlay(now);

      if (!before) {
        if (now.isComplete === false) {
          push('scoring-pending', 'Ruling pending — ' + where + ' (official about.isComplete = false)', { atBatIndex: Number(index) });
        }
        if (now.hasReview && now.inProgress === true) {
          push('review-open', 'Review opened — ' + where + ' (reviewType ' + (now.reviewType || 'not supplied') + ')', { atBatIndex: Number(index) });
        }
        return;
      }

      if (before.isComplete === false && now.isComplete === true) {
        push('ruling-resolved', 'Ruling resolved — ' + where, { atBatIndex: Number(index) });
      }
      if (before.event !== now.event || before.eventType !== now.eventType || before.description !== now.description) {
        var was = before.event || before.eventType || 'none';
        var is = now.event || now.eventType || 'none';
        if (was !== is) {
          push('ruling-change', 'Official ruling changed — ' + where + ': ' + was + ' → ' + is, { atBatIndex: Number(index) });
        } else {
          push('ruling-change', 'Official description changed — ' + where, { atBatIndex: Number(index) });
        }
      }
      if (now.hasReview && now.inProgress === true && !(before.hasReview && before.inProgress === true)) {
        push('review-open', 'Review opened — ' + where + ' (reviewType ' + (now.reviewType || 'not supplied') + ')', { atBatIndex: Number(index) });
      }
      if (before.inProgress === true && now.inProgress === false) {
        push('review-decided', 'Review closed — ' + where + ': ' +
          (now.isOverturned === true ? 'overturned' : 'confirmed') +
          ' (reviewType ' + (now.reviewType || 'not supplied') + ')', { atBatIndex: Number(index) });
      }
    });

    return entries;
  }

  function fmt(v) {
    return v === null || v === undefined ? '–' : String(v);
  }

  /* ---------------------------------------------------------------- storage */

  function memoryStorage() {
    var data = {};
    return {
      getItem: function (k) { return Object.prototype.hasOwnProperty.call(data, k) ? data[k] : null; },
      setItem: function (k, v) { data[k] = String(v); },
      removeItem: function (k) { delete data[k]; }
    };
  }

  function read(storage, gamePk) {
    if (!storage) { return []; }
    try {
      var raw = storage.getItem(key(gamePk));
      if (!raw) { return []; }
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
      return [];
    }
  }

  function write(storage, gamePk, entries) {
    if (!storage) { return; }
    try {
      var capped = entries.slice(Math.max(0, entries.length - MAX_ENTRIES));
      storage.setItem(key(gamePk), JSON.stringify(capped));
    } catch (err) {
      /* A full or blocked store must never break the page. */
    }
  }

  /*
   * Record one poll of a game. Returns { entries, last } where entries are the new rows.
   * The previous snapshot is kept beside the entries so a reload continues the comparison.
   */
  function record(storage, gamePk, feed, at) {
    var snapshotKey = key(gamePk) + ':snapshot';
    var previous = null;
    try {
      var raw = storage ? storage.getItem(snapshotKey) : null;
      if (raw) { previous = JSON.parse(raw); }
    } catch (err) {
      previous = null;
    }
    var next = snapshot(feed);
    var entries = diff(previous, next, at);
    if (entries.length) {
      var all = read(storage, gamePk).concat(entries);
      write(storage, gamePk, all);
    }
    if (storage) {
      try { storage.setItem(snapshotKey, JSON.stringify(next)); } catch (err) { /* ignore */ }
    }
    return { entries: entries, snapshot: next };
  }

  function clear(storage, gamePk) {
    if (!storage) { return; }
    try {
      storage.removeItem(key(gamePk));
      storage.removeItem(key(gamePk) + ':snapshot');
    } catch (err) { /* ignore */ }
  }

  return {
    PREFIX: PREFIX,
    MAX_ENTRIES: MAX_ENTRIES,
    key: key,
    snapshot: snapshot,
    diff: diff,
    read: read,
    write: write,
    record: record,
    clear: clear,
    memoryStorage: memoryStorage
  };
});

/*
 * docs/js/api.js — access to MLB's official Stats API.
 *
 * The only permitted origin is https://statsapi.mlb.com. A response is accepted only when:
 *   1. the URL is HTTPS on the exact host statsapi.mlb.com;
 *   2. the response is successful JSON;
 *   3. it carries MLB Advanced Media's provenance notice; and
 *   4. a game feed's returned gamePk equals the requested gamePk.
 *
 * Nothing here invents, repairs or estimates a value. If the official endpoint does not
 * supply a field, the field stays absent and the interface says so.
 *
 * Verified request/response shapes (see COORDINATION.md §4 V1–V14):
 *   GET https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=…&endDate=…&gameTypes=R,F,D,L,W&hydrate=linescore
 *   GET https://statsapi.mlb.com/api/v1.1/game/{gamePk}/feed/live
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; }
  root.MLBPBP = root.MLBPBP || {};
  root.MLBPBP.api = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var OFFICIAL_ORIGIN = 'https://statsapi.mlb.com';
  var OFFICIAL_HOST = 'statsapi.mlb.com';
  var COPYRIGHT_MARKER = 'MLB Advanced Media, L.P.';
  var SPORT_ID = 1;
  var GAME_TYPES = ['R', 'F', 'D', 'L', 'W'];
  var MIN_DATE = '2014-01-01';
  var REQUEST_TIMEOUT_MS = 30000;
  var RETRIES = 3;

  /* Error carrying a stable machine code plus the exact URL that failed. */
  function OfficialError(code, message, url) {
    this.name = 'OfficialError';
    this.code = code;
    this.message = message;
    this.url = url || null;
    if (Error.captureStackTrace) { Error.captureStackTrace(this, OfficialError); }
    else { this.stack = (new Error(message)).stack; }
  }
  OfficialError.prototype = Object.create(Error.prototype);
  OfficialError.prototype.constructor = OfficialError;

  function isIsoDate(value) {
    return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value);
  }

  /* Reject any URL that is not HTTPS on the exact official host before a socket is opened. */
  function assertOfficialUrl(url) {
    var parsed;
    try {
      parsed = new URL(url);
    } catch (err) {
      throw new OfficialError('OFFICIAL_HOST', 'Not an absolute URL: ' + url, url);
    }
    if (parsed.protocol !== 'https:') {
      throw new OfficialError('OFFICIAL_HOST', 'Only HTTPS is permitted: ' + url, url);
    }
    if (parsed.hostname !== OFFICIAL_HOST) {
      throw new OfficialError('OFFICIAL_HOST', 'Only ' + OFFICIAL_HOST + ' is permitted: ' + url, url);
    }
    return parsed;
  }

  function scheduleUrl(date) {
    if (!isIsoDate(date)) {
      throw new OfficialError('BAD_DATE', 'Date must be YYYY-MM-DD: ' + date, null);
    }
    if (date < MIN_DATE) {
      throw new OfficialError('BAD_DATE', 'The archive starts on ' + MIN_DATE + ': ' + date, null);
    }
    var query = [
      'sportId=' + SPORT_ID,
      'startDate=' + date,
      'endDate=' + date,
      'gameTypes=' + GAME_TYPES.join(','),
      'hydrate=linescore'
    ].join('&');
    return OFFICIAL_ORIGIN + '/api/v1/schedule?' + query;
  }

  function gameUrl(gamePk) {
    var pk = String(gamePk == null ? '' : gamePk);
    if (!/^\d+$/.test(pk)) {
      throw new OfficialError('BAD_GAMEPK', 'gamePk must be numeric: ' + pk, null);
    }
    return OFFICIAL_ORIGIN + '/api/v1.1/game/' + pk + '/feed/live';
  }

  /* SHA-256 of the exact response text, so a stored report can be re-checked against the source. */
  function sha256Hex(text) {
    if (typeof crypto === 'undefined' || !crypto.subtle || typeof TextEncoder === 'undefined') {
      return Promise.resolve(null);
    }
    var bytes = new TextEncoder().encode(text);
    return crypto.subtle.digest('SHA-256', bytes).then(function (buffer) {
      var view = new Uint8Array(buffer);
      var out = '';
      for (var i = 0; i < view.length; i += 1) {
        out += view[i].toString(16).padStart(2, '0');
      }
      return out;
    });
  }

  function sleep(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  function copyrightOf(json) {
    return json && typeof json.copyright === 'string' ? json.copyright : '';
  }

  function requireCopyright(json, url) {
    var notice = copyrightOf(json);
    if (notice.indexOf(COPYRIGHT_MARKER) === -1) {
      throw new OfficialError(
        'COPYRIGHT',
        'Response does not carry the MLB Advanced Media notice: ' + url,
        url
      );
    }
    return notice;
  }

  /*
   * Fetch one official URL. Returns the exact text, the parsed JSON, the retrieval time and
   * the SHA-256 of the exact text. Retries only transport failures and 5xx/429 responses.
   */
  function fetchOfficial(url, options) {
    var opts = options || {};
    assertOfficialUrl(url);
    var attempt = 0;

    function once() {
      attempt += 1;
      var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
      var timer = controller ? setTimeout(function () { controller.abort(); }, REQUEST_TIMEOUT_MS) : null;
      var init = {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit',
        cache: 'no-store',
        redirect: 'error',
        referrerPolicy: 'no-referrer',
        headers: { Accept: 'application/json' }
      };
      if (controller) { init.signal = controller.signal; }

      return fetch(url, init).then(function (response) {
        if (!response.ok) {
          var status = response.status;
          var retriable = status >= 500 || status === 429;
          if (retriable && attempt <= RETRIES) {
            return sleep(400 * attempt).then(once);
          }
          throw new OfficialError('HTTP', 'Official endpoint returned HTTP ' + status + ': ' + url, url);
        }
        return response.text().then(function (text) {
          var json;
          try {
            json = JSON.parse(text);
          } catch (err) {
            throw new OfficialError('JSON', 'Official endpoint did not return JSON: ' + url, url);
          }
          var notice = requireCopyright(json, url);
          return sha256Hex(text).then(function (digest) {
            return {
              url: url,
              text: text,
              json: json,
              copyright: notice,
              fetchedAt: new Date().toISOString(),
              sha256: digest
            };
          });
        });
      }).catch(function (err) {
        if (err instanceof OfficialError) { throw err; }
        if (attempt <= RETRIES && (err.name === 'AbortError' || err.name === 'TypeError')) {
          return sleep(400 * attempt).then(once);
        }
        throw new OfficialError(
          'NETWORK',
          'The official endpoint could not be reached: ' + url + ' (' + err.message + ')',
          url
        );
      }).then(function (value) {
        if (timer) { clearTimeout(timer); }
        return value;
      }, function (err) {
        if (timer) { clearTimeout(timer); }
        throw err;
      });
    }

    return once();
  }

  /* Flatten dates[].games[] and keep only the documented game types. */
  function qualifyingGames(scheduleJson) {
    var out = [];
    var dates = scheduleJson && Array.isArray(scheduleJson.dates) ? scheduleJson.dates : [];
    dates.forEach(function (day) {
      var games = Array.isArray(day.games) ? day.games : [];
      games.forEach(function (game) {
        if (GAME_TYPES.indexOf(game.gameType) !== -1) { out.push(game); }
      });
    });
    return out;
  }

  function getSchedule(date) {
    return fetchOfficial(scheduleUrl(date)).then(function (response) {
      if (!response.json || !Array.isArray(response.json.dates)) {
        throw new OfficialError('SCHEMA', 'Schedule response has no dates[] array: ' + response.url, response.url);
      }
      response.games = qualifyingGames(response.json);
      return response;
    });
  }

  function getGame(gamePk) {
    var url = gameUrl(gamePk);
    return fetchOfficial(url).then(function (response) {
      var feed = response.json;
      var returned = feed && feed.gamePk;
      var declared = feed && feed.gameData && feed.gameData.game && feed.gameData.game.pk;
      if (String(returned) !== String(gamePk)) {
        throw new OfficialError(
          'GAMEPK',
          'Feed returned gamePk ' + returned + ' but ' + gamePk + ' was requested: ' + url,
          url
        );
      }
      if (declared != null && String(declared) !== String(gamePk)) {
        throw new OfficialError(
          'GAMEPK',
          'Feed declared gameData.game.pk ' + declared + ' but ' + gamePk + ' was requested: ' + url,
          url
        );
      }
      if (!feed.gameData || !feed.liveData) {
        throw new OfficialError('SCHEMA', 'Feed has no gameData/liveData: ' + url, url);
      }
      return response;
    });
  }

  return {
    OFFICIAL_ORIGIN: OFFICIAL_ORIGIN,
    OFFICIAL_HOST: OFFICIAL_HOST,
    COPYRIGHT_MARKER: COPYRIGHT_MARKER,
    SPORT_ID: SPORT_ID,
    GAME_TYPES: GAME_TYPES,
    MIN_DATE: MIN_DATE,
    OfficialError: OfficialError,
    assertOfficialUrl: assertOfficialUrl,
    scheduleUrl: scheduleUrl,
    gameUrl: gameUrl,
    sha256Hex: sha256Hex,
    fetchOfficial: fetchOfficial,
    qualifyingGames: qualifyingGames,
    getSchedule: getSchedule,
    getGame: getGame
  };
});

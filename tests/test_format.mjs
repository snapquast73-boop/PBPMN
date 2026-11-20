/**
 * Tests for docs/js/format.js and the pure render helpers exported by docs/js/app.js.
 *
 * Fixtures are SYNTHETIC scaffolding (invented clubs and players) and are never published
 * as baseball data; their shape mirrors fields verified against the official API.
 *
 * Run with: node --test tests/test_format.mjs
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const format = require('../docs/js/format.js');
require('../docs/js/api.js');
const app = require('../docs/js/app.js');

const NOTICE = 'Copyright 2026 MLB Advanced Media, L.P.  Synthetic test fixture.';

function syntheticFeed() {
  return {
    copyright: NOTICE,
    gamePk: 999001,
    metaData: { wait: 10 },
    gameData: {
      game: { pk: 999001, type: 'R', season: '2026', gameNumber: 1, doubleHeader: 'N' },
      datetime: { dateTime: '2026-04-01T23:05:00Z', officialDate: '2026-04-01' },
      status: { abstractGameState: 'Final', detailedState: 'Final' },
      teams: {
        away: { id: 9001, name: 'Synthetic Away', abbreviation: 'SYN' },
        home: { id: 9002, name: 'Synthetic Home', abbreviation: 'HOM' }
      },
      venue: { name: 'Synthetic Park' }
    },
    liveData: {
      linescore: {
        currentInning: 1,
        inningState: 'Bottom',
        innings: [
          { num: 1, away: { runs: 1, hits: 1, errors: 0, leftOnBase: 0 }, home: { runs: 0, hits: 0, errors: 0, leftOnBase: 0 } }
        ],
        teams: { away: { runs: 1, hits: 1, errors: 0, leftOnBase: 0 }, home: { runs: 0, hits: 0, errors: 1, leftOnBase: 0 } },
        note: 'Synthetic note.'
      },
      decisions: { winner: { fullName: 'Synthetic Winner' }, loser: { fullName: 'Synthetic Loser' } },
      plays: {
        allPlays: [
          {
            about: { atBatIndex: 0, inning: 1, halfInning: 'top', isComplete: true, isScoringPlay: false },
            result: { event: 'Single', description: 'Synthetic Batter singles.', awayScore: 0, homeScore: 0 },
            count: { balls: 1, strikes: 2, outs: 0 },
            matchup: { batter: { id: 100001, fullName: 'Synthetic Batter' }, pitcher: { id: 200002, fullName: 'Synthetic Pitcher' } },
            playEvents: [
              {
                index: 0,
                isPitch: true,
                type: 'pitch',
                details: { call: { code: 'C', description: 'Called Strike' }, description: 'Called Strike', type: { code: 'FF', description: 'Four-Seam Fastball' } },
                pitchData: { startSpeed: 95.2, zone: 5, coordinates: { pX: -0.22, pZ: 2.45 } }
              },
              {
                index: 1,
                isPitch: true,
                type: 'pitch',
                details: { call: { code: 'X', description: 'In play, no out' }, description: 'In play, no out', type: { code: 'SI', description: 'Sinker' } },
                pitchData: { startSpeed: 94.0, zone: 8 },
                hitData: { launchSpeed: 99.8, launchAngle: 12, totalDistance: 210, trajectory: 'line_drive', hardness: 'medium' }
              }
            ],
            runners: [
              {
                movement: { originBase: null, start: null, end: '1B', isOut: false, outBase: null, outNumber: null },
                details: { event: 'Single', runner: { fullName: 'Synthetic Batter' }, isScoringEvent: false }
              }
            ]
          }
        ]
      },
      boxscore: {
        teams: {
          away: {
            battingOrder: [100001],
            pitchers: [200003],
            players: {
              ID100001: {
                person: { fullName: 'Synthetic Batter' },
                position: { abbreviation: 'LF' },
                battingOrder: '100',
                stats: { batting: { atBats: 4, runs: 1, hits: 2, rbi: 1, baseOnBalls: 0, strikeOuts: 1 } },
                seasonStats: { batting: { avg: '.318' } }
              },
              ID200003: {
                person: { fullName: 'Synthetic Starter' },
                position: { abbreviation: 'P' },
                stats: { pitching: { inningsPitched: '6.0', hits: 4, runs: 1, earnedRuns: 1, baseOnBalls: 2, strikeOuts: 7, era: '2.84', note: '(W, 1-0)' } }
              }
            }
          },
          home: { battingOrder: [], pitchers: [], players: {} }
        }
      }
    }
  };
}

const META = {
  url: 'https://statsapi.mlb.com/api/v1.1/game/999001/feed/live',
  fetchedAt: '2026-11-20T00:00:00Z',
  sha256: 'f'.repeat(64),
  copyright: NOTICE
};

test('plain text report carries every documented section', () => {
  const text = format.formatPlainText(syntheticFeed(), META);
  for (const marker of ['MLB PLAINTEXT PLAY-BY-PLAY', 'SYN at HOM  — 1-0 | Final', 'PROVENANCE',
    'GAME', 'LINE SCORE', 'DECISIONS', 'PLAY-BY-PLAY', 'BOX SCORE']) {
    assert.ok(text.includes(marker), `missing section: ${marker}`);
  }
  assert.ok(text.includes('sourceSha256: ' + 'f'.repeat(64)));
  assert.ok(text.includes('note: Synthetic note.'));
  assert.ok(text.includes('W:  Synthetic Winner'));
  assert.ok(text.includes('SV: (none supplied by MLB)'));
  assert.ok(text.includes('pitch_type=Four-Seam Fastball'));
  assert.ok(text.includes('exit_mph=99.8'));
  assert.ok(text.includes('SYNTHETIC') === false, 'fixtures must not leak into the report');
  assert.ok(text.includes('.318'), 'AVG comes from seasonStats');
});

test('missing values are stated instead of invented', () => {
  const feed = syntheticFeed();
  feed.liveData.decisions = {};
  feed.liveData.plays.allPlays = [];
  feed.liveData.linescore.innings = [];
  const text = format.formatPlainText(feed, META);
  assert.ok(text.includes('not supplied by MLB (no decisions in the official feed)'));
  assert.ok(text.includes('not supplied by MLB (no plays in the official feed for this game status)'));
  assert.ok(text.includes('not supplied by MLB (no innings in the official feed)'));
});

test('ndjson has metadata, play and event records', () => {
  const lines = format.formatEventsNdjson(syntheticFeed(), META).trim().split('\n').map((line) => JSON.parse(line));
  assert.deepEqual(lines.map((line) => line.recordType), ['metadata', 'play', 'event', 'event']);
  assert.equal(lines[0].sourceSha256, 'f'.repeat(64));
});

test('app line score table renders official totals', () => {
  const html = app.lineScoreTable(syntheticFeed(), null);
  assert.ok(html.includes('Synthetic Away'));
  assert.ok(html.includes('Synthetic Home'));
  assert.ok(html.includes('<th class="tot">R</th>'));
});

test('app play-by-play groups by half-inning and shows pitch detail', () => {
  const html = app.playsHtml(syntheticFeed());
  assert.ok(html.includes('Top 1st'));
  assert.ok(html.includes('Synthetic Batter singles.'));
  assert.ok(html.includes('95.2 mph'));
  assert.ok(html.includes('Synthetic Batter: batter → 1B'));
});

test('app play-by-play says when MLB supplied nothing', () => {
  const feed = syntheticFeed();
  feed.liveData.plays.allPlays = [];
  assert.ok(app.playsHtml(feed).includes('MLB has not supplied play-by-play for this game status.'));
});

test('app box score reads batting average from seasonStats', () => {
  const html = app.boxScoreHtml(syntheticFeed());
  assert.ok(html.includes('.318'));
  assert.ok(html.includes('(W, 1-0)'));
});

test('app escapes untrusted text', () => {
  const feed = syntheticFeed();
  feed.liveData.plays.allPlays[0].result.description = '<script>alert(1)</script>';
  const html = app.playsHtml(feed);
  assert.ok(!html.includes('<script>alert(1)</script>'));
  assert.ok(html.includes('&lt;script&gt;'));
});

test('status labels prefer the official abstract state', () => {
  assert.equal(app.statusLabel({ abstractGameState: 'Preview', detailedState: 'Scheduled' }), 'Preview');
  assert.equal(app.statusLabel({ abstractGameState: 'Live', detailedState: 'In Progress' }), 'Live');
  assert.equal(app.statusLabel({ abstractGameState: 'Final', detailedState: 'Completed Early' }), 'Final');
  assert.equal(app.statusLabel({ detailedState: 'Postponed' }), 'Postponed');
  assert.equal(app.statusLabel(null), 'Status not supplied');
});

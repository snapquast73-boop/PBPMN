/**
 * Tests for docs/js/eventlog.js.
 *
 * Fixtures are SYNTHETIC scaffolding (invented clubs, invented players) and are never
 * published as baseball data.
 *
 * Run with: node --test tests/test_eventlog.mjs
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const eventlog = require('../docs/js/eventlog.js');

function feed({ status = 'Live', away = 0, home = 0, plays = [] } = {}) {
  return {
    gamePk: 999001,
    gameData: { status: { abstractGameState: status === 'Final' ? 'Final' : 'Live', detailedState: status } },
    liveData: {
      linescore: { teams: { away: { runs: away }, home: { runs: home } }, currentInning: 1, inningState: 'Top' },
      plays: { allPlays: plays }
    }
  };
}

function play(index, { event = 'Single', eventType = 'single', description = 'Synthetic single.', complete = true, review = null } = {}) {
  const entry = {
    about: { atBatIndex: index, inning: 1, halfInning: 'top', isComplete: complete, isScoringPlay: false, hasReview: review !== null },
    result: { event, eventType, description }
  };
  if (review) { entry.reviewDetails = review; }
  return entry;
}

test('first observation records the official status', () => {
  const store = eventlog.memoryStorage();
  const result = eventlog.record(store, 999001, feed(), '2026-11-20T00:00:00Z');
  assert.equal(result.entries.length, 1);
  assert.equal(result.entries[0].kind, 'game-state');
  assert.match(result.entries[0].text, /Watching began/);
});

test('an unchanged feed adds nothing', () => {
  const store = eventlog.memoryStorage();
  eventlog.record(store, 999001, feed(), '2026-11-20T00:00:00Z');
  const second = eventlog.record(store, 999001, feed(), '2026-11-20T00:00:10Z');
  assert.deepEqual(second.entries, []);
  assert.equal(eventlog.read(store, 999001).length, 1);
});

test('score changes are recorded with both totals', () => {
  const store = eventlog.memoryStorage();
  eventlog.record(store, 999001, feed(), '2026-11-20T00:00:00Z');
  const result = eventlog.record(store, 999001, feed({ away: 1 }), '2026-11-20T00:00:20Z');
  const score = result.entries.find((entry) => entry.kind === 'score');
  assert.ok(score, 'expected a score entry');
  assert.match(score.text, /0-0 → 1-0/);
});

test('status changes are recorded', () => {
  const store = eventlog.memoryStorage();
  eventlog.record(store, 999001, feed({ status: 'Live' }), '2026-11-20T00:00:00Z');
  const result = eventlog.record(store, 999001, feed({ status: 'Final' }), '2026-11-20T01:00:00Z');
  const state = result.entries.find((entry) => entry.kind === 'game-state');
  assert.ok(state);
  assert.match(state.text, /Live → Final/);
});

test('a pending ruling is recorded, then its resolution', () => {
  const store = eventlog.memoryStorage();
  const first = eventlog.record(store, 999001, feed({ plays: [play(0, { complete: false })] }), '2026-11-20T00:00:00Z');
  const pendingEntry = first.entries.find((entry) => entry.kind === 'scoring-pending');
  assert.ok(pendingEntry, 'expected a scoring-pending entry');
  const unchanged = eventlog.record(store, 999001, feed({ plays: [play(0, { complete: false })] }), '2026-11-20T00:00:10Z');
  assert.deepEqual(unchanged.entries, []);
  const resolved = eventlog.record(store, 999001, feed({ plays: [play(0, { complete: true })] }), '2026-11-20T00:00:20Z');
  const resolvedEntry = resolved.entries.find((entry) => entry.kind === 'ruling-resolved');
  assert.ok(resolvedEntry, 'expected a ruling-resolved entry');
});

test('official ruling changes are recorded', () => {
  const store = eventlog.memoryStorage();
  eventlog.record(store, 999001, feed({ plays: [play(3, { event: 'Error', eventType: 'error' })] }), '2026-11-20T00:00:00Z');
  const result = eventlog.record(
    store,
    999001,
    feed({ plays: [play(3, { event: 'Single', eventType: 'single' })] }),
    '2026-11-20T00:00:10Z'
  );
  const change = result.entries.find((entry) => entry.kind === 'ruling-change');
  assert.ok(change);
  assert.match(change.text, /Error → Single/);
});

test('reviews are opened and closed with the official verdict', () => {
  const store = eventlog.memoryStorage();
  const opened = eventlog.record(
    store,
    999001,
    feed({ plays: [play(5, { review: { inProgress: true, isOverturned: false, reviewType: 'MA' } })] }),
    '2026-11-20T00:00:00Z'
  );
  const open = eventlog.read(store, 999001).find((entry) => entry.kind === 'review-open');
  assert.ok(open, 'expected a review-open entry');
  assert.match(open.text, /reviewType MA/);

  eventlog.record(
    store,
    999001,
    feed({ plays: [play(5, { review: { inProgress: false, isOverturned: true, reviewType: 'MA' } })] }),
    '2026-11-20T00:00:30Z'
  );
  const decided = eventlog.read(store, 999001).find((entry) => entry.kind === 'review-decided');
  assert.ok(decided, 'expected a review-decided entry');
  assert.match(decided.text, /overturned/);
  assert.equal(opened.entries.filter((entry) => entry.kind === 'review-open').length, 1);
});

test('the log is capped and clearable', () => {
  const store = eventlog.memoryStorage();
  const many = [];
  for (let i = 0; i < eventlog.MAX_ENTRIES + 25; i += 1) {
    many.push({ at: '2026-11-20T00:00:00Z', kind: 'score', text: 'entry ' + i });
  }
  eventlog.write(store, 999001, many);
  const stored = eventlog.read(store, 999001);
  assert.equal(stored.length, eventlog.MAX_ENTRIES);
  assert.equal(stored[stored.length - 1].text, 'entry ' + (many.length - 1));

  eventlog.clear(store, 999001);
  assert.deepEqual(eventlog.read(store, 999001), []);
});

test('keys are namespaced per game', () => {
  assert.equal(eventlog.key(746170), 'mlb-pbp:eventlog:v1:746170');
  const store = eventlog.memoryStorage();
  eventlog.record(store, 1, feed(), '2026-11-20T00:00:00Z');
  assert.equal(eventlog.read(store, 2).length, 0);
});

test('a corrupt stored log does not throw', () => {
  const store = eventlog.memoryStorage();
  store.setItem(eventlog.key(999001), '{not json');
  assert.deepEqual(eventlog.read(store, 999001), []);
});

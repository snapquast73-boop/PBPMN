/**
 * Offline tests for the Event log (`docs/js/eventlog.js`).
 *
 * Run with: node --test tests/test_eventlog.mjs
 *
 * Fixtures are synthetic and labelled as such: they are hand-written shapes of
 * the fields the viewer reads from MLB's official feed, never published as
 * baseball data. No network access is used.
 */
import assert from "node:assert/strict";
import test from "node:test";

import {
  collect,
  isLive,
  parseRows,
  storageKey,
} from "../docs/js/eventlog.js";

const RETRIEVED = "2026-08-11T23:05:00.000Z";

const feed = ({ state = "Live", away = 0, home = 0, ruling = "Synthetic ruling", action = "Synthetic action", events = ["synthetic-event"] } = {}) => ({
  gamePk: 1,
  metaData: { gameEvents: events, logicalEvents: events },
  gameData: { status: { abstractGameState: state } },
  liveData: {
    linescore: { teams: { away: { runs: away }, home: { runs: home } } },
    plays: {
      allPlays: [
        {
          about: { atBatIndex: 0 },
          result: { description: ruling },
          playEvents: [
            { index: 0, isPitch: true, details: { description: "Synthetic pitch" } },
            { index: 1, isPitch: false, details: { description: action } },
          ],
        },
      ],
    },
  },
});

test("isLive follows MLB's abstractGameState field", () => {
  assert.equal(isLive(feed({ state: "Live" })), true);
  assert.equal(isLive(feed({ state: "Final" })), false);
  assert.equal(isLive(feed({ state: "Preview" })), false);
  assert.equal(isLive({}), false);
});

test("storageKey keeps one log per game", () => {
  assert.equal(storageKey(745675), "pbpmn:log:745675");
  assert.notEqual(storageKey(745675), storageKey(746170));
});

test("nothing is recorded when the game is not live and was not live", () => {
  const rows = collect(feed({ state: "Final" }), RETRIEVED, []);
  assert.deepEqual(rows, []);
});

test("a live feed records scores, rulings, actions and MLB's event markers", () => {
  const rows = collect(feed({ away: 3, home: 1 }), RETRIEVED, []);
  assert.deepEqual(
    rows.map((row) => [row.kind, row.value]),
    [
      ["away runs", 3],
      ["home runs", 1],
      ["Play 0 ruling", "Synthetic ruling"],
      ["Play 0 action 1", "Synthetic action"],
      ["gameEvents", '["synthetic-event"]'],
      ["logicalEvents", '["synthetic-event"]'],
    ],
  );
  assert.ok(rows.every((row) => row.at === RETRIEVED));
});

test("pitches are not logged as actions", () => {
  const rows = collect(feed(), RETRIEVED, []);
  assert.equal(rows.some((row) => row.value === "Synthetic pitch"), false);
  assert.equal(rows.filter((row) => row.kind.startsWith("Play 0 action")).length, 1);
});

test("an unchanged poll adds nothing, a changed value appends", () => {
  const first = collect(feed({ away: 1 }), RETRIEVED, []);
  const same = collect(feed({ away: 1 }), "2026-08-11T23:05:30.000Z", first);
  assert.deepEqual(same, first);

  const changed = collect(
    feed({ away: 2, ruling: "Synthetic overturn" }),
    "2026-08-11T23:06:00.000Z",
    first,
  );
  assert.equal(changed.length, first.length + 2);
  assert.deepEqual(
    changed.slice(first.length).map((row) => [row.kind, row.value, row.at]),
    [
      ["away runs", 2, "2026-08-11T23:06:00.000Z"],
      ["Play 0 ruling", "Synthetic overturn", "2026-08-11T23:06:00.000Z"],
    ],
  );
});

test("the previous log is not mutated", () => {
  const previous = collect(feed({ away: 1 }), RETRIEVED, []);
  const copy = JSON.parse(JSON.stringify(previous));
  collect(feed({ away: 5 }), "2026-08-11T23:06:00.000Z", previous);
  assert.deepEqual(previous, copy);
});

test("a game that was live keeps its closing values after it goes final", () => {
  const rows = collect(feed({ state: "Final", away: 7 }), RETRIEVED, [], true);
  assert.deepEqual(rows[0], { at: RETRIEVED, kind: "away runs", value: 7 });
});

test("only well-formed stored rows are read back", () => {
  const valid = { at: RETRIEVED, kind: "away runs", value: 3 };
  assert.deepEqual(parseRows(JSON.stringify([valid])), [valid]);
  assert.deepEqual(parseRows(JSON.stringify([valid, { at: 1, kind: 2, value: null }, "junk"])), [valid]);
  assert.deepEqual(parseRows("not json"), []);
  assert.deepEqual(parseRows(null), []);
  assert.deepEqual(parseRows("{}"), []);
});

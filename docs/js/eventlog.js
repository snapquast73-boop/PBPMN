/**
 * Event log for a live game.
 *
 * While MLB's official feed reports a game as Live, the viewer records the
 * official values it observed: the two scores, each play's ruling, non-pitch
 * play events (actions) and MLB's own game/logical event markers. The rows are
 * kept in this browser only (`localStorage`, one key per game) so the log can be
 * read after the event or the game. Nothing here is written to a server.
 *
 * Every function is pure with respect to the feed object, so
 * `tests/test_eventlog.mjs` exercises this file with synthetic fixtures and no
 * browser or network. Field names are the ones the viewer already reads; no
 * value is derived or estimated.
 */

/** MLB's own game state for the feed, e.g. "Live", "Final", "Preview". */
export const isLive = (feed) =>
  feed?.gameData?.status?.abstractGameState === "Live";

/** One storage key per game, so logs survive a refresh and stay separate. */
export const storageKey = (gamePk) => `pbpmn:log:${gamePk}`;

/**
 * Read a stored log back. Anything that is not a list of
 * `{at, kind, value}` rows is discarded rather than repaired.
 */
export const parseRows = (stored) => {
  try {
    const rows = JSON.parse(stored);
    return Array.isArray(rows)
      ? rows.filter(
          (row) =>
            row &&
            typeof row.kind === "string" &&
            ["string", "number", "boolean"].includes(typeof row.value) &&
            typeof row.at === "string",
        )
      : [];
  } catch {
    return [];
  }
};

const allPlays = (feed) => feed?.liveData?.plays?.allPlays ?? [];

/**
 * Append the official values in `feed` that differ from the last recorded value
 * of the same kind. `previous` is never modified; the returned array is a new
 * one. When the game is not Live and was not Live on the previous poll, nothing
 * is recorded.
 */
export function collect(feed, retrieved, previous = [], wasLive = false) {
  const rows = [...previous];
  if (!isLive(feed) && !wasLive) return rows;
  const add = (kind, value) => {
    if (value == null || value === "") return;
    const last = rows.findLast((row) => row.kind === kind);
    if (last?.value !== value) rows.push({ at: retrieved, kind, value });
  };
  for (const side of ["away", "home"])
    add(side + " runs", feed?.liveData?.linescore?.teams?.[side]?.runs);
  for (const play of allPlays(feed)) {
    const index = play.about?.atBatIndex;
    if (index == null) continue;
    add(`Play ${index} ruling`, play.result?.description);
    for (const event of play.playEvents ?? [])
      if (event.isPitch === false && event.index != null)
        add(`Play ${index} action ${event.index}`, event.details?.description);
  }
  for (const field of ["gameEvents", "logicalEvents"])
    if (feed?.metaData?.[field]?.length)
      add(field, JSON.stringify(feed.metaData[field]));
  return rows;
}

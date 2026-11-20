import { scheduleURL, feedURL, official } from "./api.js";
import { esc, plays, pretty, text, records } from "./format.js";
const $ = (id) => document.getElementById(id);
const link = (url, label) => `<a href="${esc(url)}">${esc(label)}</a>`;
const source = (url) => link(url, "MLB source");
const views = ["Overview", "Plays", "Box score", "Event log"];
let controller,
  timer,
  record,
  view,
  historyRows = [],
  storageWarning = "";
const localDay = (d) =>
  [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, "0"),
    String(d.getDate()).padStart(2, "0"),
  ].join("-");
function table(headers, rows) {
  if (!rows.length) return "<p>No records supplied by MLB.</p>";
  return `<div class="scroll"><table><thead><tr>${[...headers, "Source"].map((v) => `<th>${esc(v)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((v) => `<td>${esc(v)}</td>`).join("")}<td>${source(record.url)}</td></tr>`).join("")}</tbody></table></div>`;
}
function render() {
  const f = record.data,
    ld = f.liveData ?? {},
    gd = f.gameData ?? {},
    ls = ld.linescore ?? {};
  $("filter").hidden = view !== "Plays";
  for (const b of $("tabs").children)
    b.setAttribute("aria-pressed", String(b.textContent === view));
  let html = "";
  if (view === "Overview") {
    const innings = ls.innings ?? [];
    html =
      "<h3>Line score</h3>" +
      table(
        ["Team", ...innings.map((i) => i.num), "R", "H", "E", "LOB"],
        ["away", "home"].map((k) => [
          gd.teams?.[k]?.name,
          ...innings.map((i) => i[k]?.runs),
          ...["runs", "hits", "errors", "leftOnBase"].map(
            (s) => ls.teams?.[k]?.[s],
          ),
        ]),
      ) +
      "<h3>Decisions</h3>" +
      table(
        ["Decision", "Player"],
        Object.entries(ld.decisions ?? {}).map(([k, v]) => [k, v.fullName]),
      );
  } else if (view === "Box score") {
    for (const side of ["away", "home"]) {
      const team = ld.boxscore?.teams?.[side];
      html += `<h3>${esc(team?.team?.name)}</h3>`;
      for (const [list, category, stats] of [
        [
          "batters",
          "batting",
          ["atBats", "runs", "hits", "rbi", "baseOnBalls", "strikeOuts"],
        ],
        [
          "pitchers",
          "pitching",
          [
            "inningsPitched",
            "hits",
            "runs",
            "earnedRuns",
            "baseOnBalls",
            "strikeOuts",
          ],
        ],
      ]) {
        html += table(
          ["Player", ...stats],
          (team?.[list] ?? [])
            .map((id) => team.players?.["ID" + id])
            .filter(Boolean)
            .map((p) => [
              p.person?.fullName,
              ...stats.map((s) => p.stats?.[category]?.[s]),
            ]),
        );
      }
    }
  } else if (view === "Plays") {
    const q = $("search").value.toLowerCase().trim();
    for (const p of plays(f)) {
      if (q && !JSON.stringify(p).toLowerCase().includes(q)) continue;
      html += `<details><summary>${esc(p.about?.halfInning)} ${esc(p.about?.inning)} · ${esc(p.result?.description)}</summary><p>${esc(p.matchup?.batter?.fullName)} / ${esc(p.matchup?.pitcher?.fullName)} · ${source(record.url)}</p><h4>Pitches and actions</h4><pre>${esc(pretty(p.playEvents))}</pre><h4>Runners</h4><pre>${esc(pretty(p.runners))}</pre></details>`;
    }
    if (!html)
      html = q
        ? "No matching plays."
        : "No play-by-play supplied by MLB for this game status.";
  } else {
    html =
      "<p>Observations made while this browser was watching. Times are retrieval times, not official event times.</p>" +
      esc(storageWarning) +
      table(
        ["Observed (UTC)", "Change", "Official value"],
        historyRows.map((v) => [v.at, v.kind, v.value]),
      );
  }
  $("content").innerHTML = html;
}
function buttons(id, names, fn) {
  $(id).replaceChildren(
    ...names.map((name) => {
      const b = document.createElement("button");
      b.textContent = name;
      b.onclick = () => fn(name);
      return b;
    }),
  );
}
function download(kind) {
  const [ext, mime, body] =
    kind === "Raw JSON"
      ? ["json", "application/json", record.bytes]
      : kind === "Event NDJSON"
        ? ["ndjson", "application/x-ndjson", records(record)]
        : ["txt", "text/plain", text(record)];
  const url = URL.createObjectURL(new Blob([body], { type: mime })),
    a = document.createElement("a");
  a.href = url;
  a.download = `${record.data.gamePk}.${ext}`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function observe(r, wasLive) {
  const f = r.data,
    key = "pbpmn:log:" + f.gamePk;
  if (f.gameData?.status?.abstractGameState !== "Live" && !wasLive) return;
  const add = (kind, value) => {
    if (value == null || value === "") return;
    const previous = historyRows.findLast((e) => e.kind === kind);
    if (previous?.value !== value)
      historyRows.push({ at: r.retrieved, kind, value });
  };
  for (const side of ["away", "home"])
    add(side + " runs", f.liveData?.linescore?.teams?.[side]?.runs);
  for (const p of plays(f)) {
    const n = p.about?.atBatIndex;
    if (n == null) continue;
    add(`Play ${n} ruling`, p.result?.description);
    for (const e of p.playEvents ?? [])
      if (e.isPitch === false && e.index != null)
        add(`Play ${n} action ${e.index}`, e.details?.description);
  }
  for (const field of ["gameEvents", "logicalEvents"])
    if (f.metaData?.[field]?.length)
      add(field, JSON.stringify(f.metaData[field]));
  try {
    localStorage.setItem(key, JSON.stringify(historyRows));
  } catch {
    storageWarning =
      "Local storage unavailable. New observations are in memory only.";
  }
}
async function openGame(id, signal) {
  const url = feedURL(id),
    wasLive = record?.data.gameData?.status?.abstractGameState === "Live";
  $("game").hidden = false;
  try {
    const r = await official(url, signal, id);
    if (signal.aborted) return;
    record = r;
    observe(r, wasLive);
    const f = r.data,
      gd = f.gameData ?? {};
    $("match").textContent = [gd.teams?.away?.name, gd.teams?.home?.name].join(
      " at ",
    );
    $("summary").innerHTML =
      `${esc(gd.status?.detailedState)} · ${esc(gd.venue?.name)} · ${source(url)}`;
    $("controls").hidden = false;
    $("notice").textContent = f.copyright;
    render();
    if (gd.status?.abstractGameState === "Live") {
      const wait = Number(f.metaData?.wait);
      timer = setTimeout(
        () => openGame(id, signal),
        (wait > 0 ? wait : 30) * 1000,
      );
    }
  } catch (err) {
    if (signal.aborted) return;
    $("summary").innerHTML =
      `Could not refresh game: ${esc(err.message)} · ${source(url)}`;
    if (wasLive) timer = setTimeout(() => openGame(id, signal), 30000);
  }
}
async function load() {
  controller?.abort();
  clearTimeout(timer);
  controller = new AbortController();
  const { signal } = controller;
  record = null;
  view = "Overview";
  $("search").value = "";
  $("games").replaceChildren();
  $("game").hidden = true;
  $("controls").hidden = true;
  const params = new URLSearchParams(location.search),
    date = params.get("date") ?? localDay(new Date()),
    id = params.get("game");
  $("date").value = date;
  if (!$("date").checkValidity()) {
    $("status").textContent = "Choose a valid date from 2014 onward.";
    return;
  }
  const url = scheduleURL(date);
  $("status").textContent = "Loading official schedule…";
  try {
    const { data } = await official(url, signal);
    if (signal.aborted) return;
    const games = data.dates.flatMap((d) => d.games);
    $("status").innerHTML =
      (games.length ? "Select a game." : "No qualifying games on this date.") +
      " · " +
      source(url);
    for (const g of games) {
      const a = document.createElement("a");
      a.href = "?" + new URLSearchParams({ date, game: g.gamePk });
      a.innerHTML = `<strong>${esc(g.teams?.away?.team?.name)} at ${esc(g.teams?.home?.team?.name)}</strong><small>${esc(g.status?.detailedState)} · ${esc(g.gameDate)} · ${esc(g.venue?.name)}</small>`;
      $("games").append(a);
    }
    if (id && games.some((g) => String(g.gamePk) === id)) {
      storageWarning = "";
      historyRows = [];
      try {
        const rows = JSON.parse(localStorage.getItem("pbpmn:log:" + id));
        if (Array.isArray(rows))
          historyRows = rows.filter((e) => e && typeof e.kind === "string");
      } catch {
        storageWarning = "Stored observations unavailable.";
      }
      $("match").textContent = "Loading game…";
      $("summary").textContent = "";
      await openGame(id, signal);
    } else if (id)
      $("status").append(" Requested game not listed for this date.");
  } catch (err) {
    if (!signal.aborted)
      $("status").innerHTML =
        `Schedule unavailable: ${esc(err.message)} · ${source(url)}`;
  }
}
$("schedule-form").onsubmit = (e) => {
  e.preventDefault();
  history.pushState(
    null,
    "",
    "?" + new URLSearchParams({ date: $("date").value }),
  );
  load();
};
buttons("tabs", views, (v) => {
  view = v;
  render();
});
buttons("exports", ["Plain text", "Raw JSON", "Event NDJSON"], download);
$("search").oninput = render;
window.onpopstate = load;
load();

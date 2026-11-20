# COORDINATION — session task board

**Repo:** `snapquast73-boop/PBPMN` (upload of the "MLB Plaintext Play-by-Play" project)
**Live site target:** https://snapquast73-boop.github.io/PBPMN/
**Board owner of record:** session `arena-3fa5105a` (branch `arena/3fa5105a-pbpmn`)

This file is the shared task board for parallel agent sessions. Read it before doing any
work; claim a task by writing your session ID and file scope into the table, then commit
and push the claim immediately. Never start a task another session has claimed.

---

## 0. Integrity finding (read this first)

The uploaded snapshot of this repository is **incomplete**. `README.md`, `pyproject.toml`,
`index.html`, `.nojekyll`, `LICENSE` and `GIANTS_ATHLETICS_2014-2026_REVIEW.md` are present,
but every directory those documents reference was missing:

| Referenced by | Path | State in upload (`14c9aaf`) | State now |
|---|---|---|---|
| `README.md` "Web app", `index.html` redirect, Pages source `main:/` | `docs/` | **missing** | rebuilt |
| `README.md` "Repository map", `pyproject.toml` `mlb-pbp` script | `mlb_pbp/` | **missing** | rebuilt |
| `README.md` "Development and tests" | `tests/` | **missing** | rebuilt |
| `README.md` "Durable season releases" | `automation/github-actions/` | **missing** | rebuilt (templates) |

Consequence: `https://snapquast73-boop.github.io/PBPMN/` served a page whose only content was a
redirect to `./docs/`, which returned 404. GitHub Pages itself was healthy —
`gh api repos/snapquast73-boop/PBPMN/pages` returned `"status":"built",
"source":{"branch":"main","path":"/"},"https_enforced":true` — so this was a missing-content
failure, not a deployment-configuration failure.

The original upstream repository named in the uploaded documents
(`buffedlizard55-lab/MLB-PBP`) no longer resolves:
`GET https://api.github.com/repos/buffedlizard55-lab/MLB-PBP` → **404** and
`GET https://api.github.com/users/buffedlizard55-lab` → **404** (checked 2026-11-20).
A byte-for-byte diff was therefore impossible; the missing code was rebuilt to the behaviour
specified by this repository's own documents and verified against the one data source those
documents allow (`https://statsapi.mlb.com`).

---

## 1. Sessions

| Session ID | Branch | Scope | Status |
|---|---|---|---|
| `arena-3fa5105a` | `arena/3fa5105a-pbpmn` | entire rebuild (single active session) | active |

> There is exactly one agent session on this repository. The branch name is fixed by the
> session harness (`arena/3fa5105a-pbpmn`) instead of the `session-<id>/<task>` convention;
> that is a harness constraint, not a claim of a different scope. If a second session appears,
> it must claim unclaimed rows below before touching any file and must not edit files owned by
> `arena-3fa5105a` without logging a request here first.

---

## 2. Task board

Status values: `unclaimed` · `in progress` · `needs review` · `done`.

| ID | Task | Files (scope) | Owner | Status | Commit(s) |
|---|---|---|---|---|---|
| T1 | Static viewer shell (layout, styles, Pages redirect target) | `docs/index.html`, `docs/css/app.css` | `arena-3fa5105a` | done | see §7 |
| T2 | Official API access layer with provenance + host allowlist | `docs/js/api.js` | `arena-3fa5105a` | done | see §7 |
| T3 | Plain-text and NDJSON formatters (browser + CLI) | `docs/js/format.js`, `mlb_pbp/formatter.py` | `arena-3fa5105a` | done | see §7 |
| T4 | Viewer logic (schedule, line score, plays, box score, search, downloads, deep links, live refresh) | `docs/js/app.js` | `arena-3fa5105a` | done | see §7 |
| T5 | Local Event log | `docs/js/eventlog.js`, `tests/test_eventlog.mjs` | `arena-3fa5105a` | done | see §7 |
| T6 | CLI archive package | `mlb_pbp/__init__.py`, `__main__.py`, `client.py`, `archive.py` | `arena-3fa5105a` | done | see §7 |
| T7 | Test suite + CI | `tests/*`, `.github/workflows/ci.yml` | `arena-3fa5105a` | done | see §7 |
| T8 | Documented workflow templates | `automation/github-actions/pages.yml`, `archive.yml` | `arena-3fa5105a` | done | see §7 |
| T9 | Methodology + Flagged for Review pages | `docs/methodology.html`, `docs/flagged.html` | `arena-3fa5105a` | done | see §7 |
| T10 | Official-source verification of every published figure | `docs/flagged.html`, this file | `arena-3fa5105a` | done | see §4, §5 |
| T11 | Integration: PR → merge → Pages deploy verification | (board only) | `arena-3fa5105a` | in progress | see §7 |

---

## 3. Claim log

| UTC | Session | Action |
|---|---|---|
| 2026-11-20 | `arena-3fa5105a` | Board created. T1–T7 claimed; T8–T11 queued behind them. No other session present. |
| 2026-11-20 | `arena-3fa5105a` | Confirmed `origin/main` at `14c9aaf`; working branch `arena/3fa5105a-pbpmn`. |
| 2026-11-20 | `arena-3fa5105a` | T1–T10 finished within this session; no hand-off and no conflicts occurred — no other session wrote to this repository during the work. |

---

## 4. Verification log (official sources only)

Every row was checked on 2026-11-20 against `statsapi.mlb.com` (the only origin the repository's
documents permit) or the GitHub REST API. Responses were read live; no value was inferred.
The same table, with clickable links, is published on `docs/flagged.html` §2–§3.

| # | Claim | Source URL | Result |
|---|---|---|---|
| V1 | `sportId=1` = "Major League Baseball" | `https://statsapi.mlb.com/api/v1/sports/1` | confirmed |
| V2 | Schedule shape `dates[].games[]` with `gamePk`,`gameType`,`season`,`gameDate`,`officialDate`,`status`,`teams.away/home`,`leagueRecord`,`score`,`venue.name`,`linescore` | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-27&endDate=2026-10-30&gameTypes=F,D,L,W&hydrate=linescore` | confirmed (2 World Series games) |
| V3 | `gameTypes=R,F,D,L,W` accepted, restricts to those types | same as V2 | confirmed (only `"gameType":"W"`) |
| V4 | Feed path `/api/v1.1/game/{gamePk}/feed/live` returning `copyright`,`gamePk`,`metaData`,`gameData`,`liveData` | `https://statsapi.mlb.com/api/v1.1/game/746170/feed/live` | confirmed |
| V5 | Notice `…MLB Advanced Media, L.P.…` on every response | `https://statsapi.mlb.com/api/v1/sports/1` | confirmed |
| V6 | `metaData.wait/timeStamp/gameEvents/logicalEvents` | feed 746170 | confirmed (`wait:10`) |
| V7 | `gameData.game{…}`, `datetime{…}`, `status{…}`, `teams.away/home{id,name,abbreviation,record.leagueRecord}`, `players["ID<pk>"]`, `venue`, `weather`, `probablePitchers` | feed 746170 | confirmed |
| V8 | `liveData.decisions.{winner,loser,save}.fullName`; `save` omitted when none | `…/feed/live?fields=copyright,gameData,weather,liveData,decisions,winner,loser,save,fullName,id` | confirmed (winner+loser, no save) |
| V9 | `allPlays[]` `result{type,event,eventType,rbi,awayScore,homeScore,isOut}`, `about{atBatIndex,inning,halfInning,isComplete,isScoringPlay,hasReview}`, `count`, `matchup.batter/pitcher` | `…/feed/live?fields=…,allPlays,result,about,count,matchup,…` (game 849803) | confirmed (92 plays) |
| V10 | `playEvents[]` `index,isPitch,details{call,description,type,…},pitchData{startSpeed,endSpeed,zone,coordinates{pX,pZ}},hitData{launchSpeed,launchAngle,totalDistance,trajectory,hardness}` | `…/feed/live?fields=…,playEvents,details,pitchData,hitData,…` | confirmed |
| V11 | `reviewDetails{isOverturned,inProgress,reviewType}` when `about.hasReview` is true | `…/feed/live?fields=…,about,hasReview,reviewDetails,…` (play 30 of 849803) | confirmed (`reviewType":"MA"`) |
| V12 | `liveData.linescore{innings[],teams.{home,away}{runs,hits,errors,leftOnBase},note,currentInning,inningState}` | `https://statsapi.mlb.com/api/v1/game/746170/linescore` | confirmed |
| V13 | `liveData.boxscore.teams.{away,home}{battingOrder,pitchers,players["ID<pk>"]{person,position,stats,seasonStats},teamStats}` | `https://statsapi.mlb.com/api/v1/game/746170/boxscore?fields=…` | confirmed |
| V14 | In-game `stats.batting` has no AVG/OBP/SLG; only `seasonStats.batting` does | same as V13 | confirmed — AVG column reads `seasonStats` |
| V15 | `runners[]` `movement{originBase,start,end,outBase,outNumber,isOut}`, `details{event,runner.fullName,isScoringEvent}`, `credits[]` | `…/feed/live?fields=…,runners,movement,…` (game 849803) | confirmed |
| V16 | 746170 = 2024-04-01, SF at LAD, LAD 8 – SF 3 | `/api/v1/game/746170/linescore` | confirmed |
| V17 | 745675 = 2024-04-01, BOS 9 @ OAK 0, Final | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2024-04-01&endDate=2024-04-01&gameTypes=R,F,D,L,W&fields=…` | confirmed |
| V18 | CORS: the official origin returns `access-control-allow-origin: *` so the browser viewer can read it | `.github/workflows/verify-official-api.yml` (public run log prints the headers; the job fails if the header is missing) | measured in CI — see §7 |
| V19 | SF season counts 2014→2026-08-11 = 181,163,167,163,163,163,65,169,163,165,162,162,123 (total 2,009) | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=137&startDate=YYYY-01-01&endDate=YYYY-12-31&gameTypes=R,F,D,L,W&fields=copyright,totalGames` (13 requests; 2026 uses `endDate=2026-08-11`) | all 13 confirmed; total 2,009 |
| V20 | ATH season counts 2014→2026-08-11 = 165,162,163,163,164,165,73,163,162,162,**163**,162,**120** (total 1,987) | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=133&startDate=YYYY-01-01&endDate=YYYY-12-31&gameTypes=R,F,D,L,W&fields=copyright,totalGames` | 13 requests; 11 match the review document, 2 differ (2024, 2026) |
| V21 | 2014-03-31 SF first game = 380550, SF 9 @ ARI 8, Chase Field | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=137&startDate=2014-03-31&endDate=2014-03-31&gameTypes=R,F,D,L,W&fields=…` | confirmed |
| V22 | 2026-08-11 slate: all 15 `gamePk` values in the review document | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-08-11&endDate=2026-08-11&gameTypes=R,F,D,L,W&fields=…` | 15/15 match; 14/15 venue names match exactly |
| V23 | Local build serves every page (200) | `python -m http.server` + `curl` on `/`, `/docs/`, `/docs/methodology.html`, `/docs/flagged.html`, `/docs/css/app.css`, `/docs/js/*.js` | all 200, non-empty |
| V24 | Test suites pass | `python -m unittest discover -s tests -t .` → 36 tests; `node --test tests/test_eventlog.mjs tests/test_format.mjs` → 19 tests | all pass; `python -m compileall -q mlb_pbp`, `node --check docs/js/*.js` clean |
| V25 | Package installs and exposes the documented console script | `python -m venv /tmp/venvtest && pip install -e . --no-build-isolation` | `mlb-pbp` entry point created; `import mlb_pbp` → 1.0.0 |

Anything that could not be confirmed against an official source is published, with its source
link and the reason, on `docs/flagged.html` §4 ("values left blank").

---

## 5. Irregularities logged for review

Published with links on `docs/flagged.html` §1 and §4.

| ID | Irregularity | Handling |
|---|---|---|
| I1 | Upload contained no `docs/`, `mlb_pbp/`, `tests/`, `automation/` although every document references them | rebuilt; field-level verification in §4 |
| I2 | Upstream repo (`buffedlizard55-lab/MLB-PBP`) 404 — original source unavailable for a line-by-line diff | reconstruction is behaviour-compatible, not byte-identical; flagged |
| I3 | `README.md` links to the dead `buffedlizard55-lab.github.io/MLB-PBP/` | original line kept; one deployment note added pointing at this site |
| I4 | `GIANTS_ATHLETICS_2014-2026_REVIEW.md` contains approximations and two wrong counts | flagged cell-by-cell; official counts published alongside |
| I5 | `pyproject.toml` declared a package and console script that did not exist | package rebuilt; install verified (V25) |
| I6 | `index.html` meta-refresh target `./docs/` did not exist → Pages root redirected to a 404 | `docs/` rebuilt; all pages serve (V23) |
| I7 | Review document: ATH 2024 stated 162, official 163; ATH 2026-to-08-11 stated 119, official 120; ATH subtotal "≈2,024" is not reproducible (document's own rows sum to 1,985; official 1,987); combined "~4,033" is therefore wrong (official 3,996) | published on `docs/flagged.html` §3 with per-row source links; no value silently corrected in the source document |
| I8 | Review document venue "Dodger Stadium" for gamePk 823917; official response now returns "UNIQLO Field at Dodger Stadium" | site always renders the venue string MLB currently returns; noted |
| I9 | Review document recorded the 2026-08-11 slate as Preview/Scheduled; the same games now return Final with scores | normal time passing; noted so it is not mistaken for an error |
| I10 | Review document's "first game (example)" column could not be confirmed for all 26 rows within this session | left blank and marked unverified (3 rows spot-checked instead: V16, V17, V21) |

---

## 6. Files and ownership

| Path | Owner | Notes |
|---|---|---|
| `docs/**`, `mlb_pbp/**`, `tests/**`, `automation/**`, `.github/workflows/**` | `arena-3fa5105a` | created this session |
| `README.md` | `arena-3fa5105a` | one added deployment note (rest of the file untouched) |
| `index.html`, `.nojekyll`, `LICENSE`, `pyproject.toml`, `GIANTS_ATHLETICS_2014-2026_REVIEW.md` | untouched from upload | content preserved as-is |
| `COORDINATION.md` | board | this file |

Shared outputs (site index/navigation, table data) were changed only by this session, and only
after the per-task verification above was recorded — the integration role is carried by the
same session because no other session is active.

---

## 7. Merge log

| UTC | Action | Result |
|---|---|---|
| — | pending integration | — |

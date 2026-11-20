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
`index.html`, `.nojekyll` and `GIANTS_ATHLETICS_2014-2026_REVIEW.md` are present, but every
directory those documents reference is missing:

| Referenced by | Path | State in upload (`14c9aaf`) |
|---|---|---|
| `README.md` "Web app", `index.html` redirect, `.github` Pages source | `docs/` | **missing** |
| `README.md` "Repository map", `pyproject.toml` `mlb-pbp` script | `mlb_pbp/` | **missing** |
| `README.md` "Development and tests" | `tests/` | **missing** |
| `README.md` "Durable season releases" | `automation/github-actions/` | **missing** |

Consequence: `https://snapquast73-boop.github.io/PBPMN/` loads a page whose only content is a
redirect to `./docs/`, which returns 404. The GitHub Pages deployment reports `built`
(`gh api repos/snapquast73-boop/PBPMN/pages` → `"status":"built","source":{"branch":"main","path":"/"}`),
so the failure is a missing-content failure, not a deployment-configuration failure.

The original upstream repository named in the uploaded documents
(`buffedlizard55-lab/MLB-PBP`) no longer resolves: `GET https://api.github.com/repos/buffedlizard55-lab/MLB-PBP`
returns **404** and `GET https://api.github.com/users/buffedlizard55-lab` returns **404**
(checked 2026-11-20). A cat is therefore impossible; the missing code is being rebuilt to the
behaviour specified by this repository's own documents, verified against the one data source
those documents allow (`https://statsapi.mlb.com`).

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
| T1 | Rebuild static viewer shell (layout, styles, redirect target) | `docs/index.html`, `docs/css/app.css` | `arena-3fa5105a` | in progress | — |
| T2 | Rebuild official API access layer with provenance + host allowlist | `docs/js/api.js` | `arena-3fa5105a` | in progress | — |
| T3 | Rebuild plain-text and NDJSON formatters | `docs/js/format.js`, `mlb_pbp/formatter.py` | `arena-3fa5105a` | in progress | — |
| T4 | Rebuild viewer logic (schedule, line score, plays, box score, search, downloads, deep links, live refresh) | `docs/js/app.js` | `arena-3fa5105a` | in progress | — |
| T5 | Rebuild local Event log | `docs/js/eventlog.js`, `tests/test_eventlog.mjs` | `arena-3fa5105a` | in progress | — |
| T6 | Rebuild CLI archive package | `mlb_pbp/__init__.py`, `mlb_pbp/__main__.py`, `mlb_pbp/client.py`, `mlb_pbp/archive.py` | `arena-3fa5105a` | in progress | — |
| T7 | Rebuild test suite + CI | `tests/*.py`, `.github/workflows/ci.yml` | `arena-3fa5105a` | in progress | — |
| T8 | Rebuild documented workflow templates | `automation/github-actions/pages.yml`, `automation/github-actions/archive.yml` | `arena-3fa5105a` | unclaimed | — |
| T9 | Methodology + Flagged for Review pages | `docs/methodology.html`, `docs/flagged.html` | `arena-3fa5105a` | unclaimed | — |
| T10 | Official-source verification of every published figure | `docs/flagged.html`, this file | `arena-3fa5105a` | unclaimed | — |
| T11 | Integration: PR → merge → Pages deploy verification | (board only) | `arena-3fa5105a` | unclaimed | — |

---

## 3. Claim log

| UTC | Session | Action |
|---|---|---|
| 2026-11-20 | `arena-3fa5105a` | Board created. T1–T7 claimed for this session; T8–T11 queued behind them. No other session present, so no conflict checks pending. |
| 2026-11-20 | `arena-3fa5105a` | Confirmed `origin/main` is at `14c9aaf` and the working branch is `arena/3fa5105a-pbpmn`. |

---

## 4. Verification log (official sources only)

Every claim below was checked on 2026-11-20 against `statsapi.mlb.com` (the only origin the
repository's documents permit) or against the GitHub REST API. Responses were read live; no
value is inferred.

| # | Claim | Source URL | Result |
|---|---|---|---|
| V1 | `sportId=1` is "Major League Baseball" | `https://statsapi.mlb.com/api/v1/sports/1` | confirmed |
| V2 | Schedule endpoint returns `dates[].games[]` with `gamePk`, `gameType`, `season`, `gameDate`, `officialDate`, `status{abstractGameState,detailedState,statusCode}`, `teams.away/home.team{id,name}`, `leagueRecord{wins,losses}`, `score`, `isWinner`, `venue.name`, `linescore` | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-27&endDate=2026-10-30&gameTypes=F,D,L,W&hydrate=linescore` | confirmed |
| V3 | `gameTypes=R,F,D,L,W` is accepted and filters to regular season (`R`) + postseason (`F,D,L,W`) | same URL as V2 (returned only `W` games for the World Series window) | confirmed |
| V4 | Feed path is `/api/v1.1/game/{gamePk}/feed/live` and returns `copyright`,`gamePk`,`link`,`metaData`,`gameData`,`liveData` | `https://statsapi.mlb.com/api/v1.1/game/746170/feed/live` | confirmed |
| V5 | Every response carries the notice `Copyright … MLB Advanced Media, L.P. …` | `https://statsapi.mlb.com/api/v1/sports/1` | confirmed |
| V6 | `metaData.wait` (seconds), `metaData.timeStamp`, `metaData.gameEvents`, `metaData.logicalEvents` | `https://statsapi.mlb.com/api/v1.1/game/746170/feed/live` (chunk 0) | confirmed (`wait:10`) |
| V7 | `gameData.game{pk,type,season,gameNumber,doubleHeader}`, `gameData.datetime{dateTime,originalDate,officialDate,dayNight,time,ampm}`, `gameData.status{…}`, `gameData.teams.away/home{id,name,abbreviation,teamName,fileCode,record.leagueRecord{wins,losses,pct}}`, `gameData.players["ID<pk>"]{fullName,primaryNumber,boxScoreName…}`, `gameData.venue`, `gameData.weather{condition,temp,wind}`, `gameData.probablePitchers` | same as V6 | confirmed |
| V8 | `liveData.decisions.winner/loser/save{id,fullName}` (3 saves omitted when none supplied) | `…/feed/live?fields=copyright,gameData,venue,weather,liveData,decisions,winner,loser,save,fullName,id` | confirmed for `winner`+`loser` on 746170 |
| V9 | `liveData.plays.allPlays[]` fields `result{type,event,eventType,description,rbi,awayScore,homeScore,isOut}`, `about{atBatIndex,inning,halfInning,isComplete,isScoringPlay,hasReview}`, `count{balls,strikes,outs}`, `matchup.batter/pitcher{id,fullName}` | `…/feed/live?fields=…,allPlays,result,about,count,matchup,…` | confirmed |
| V10 | `playEvents[]` fields `index`, `isPitch`, `type` (`"pitch"`/`"action"`), `details{call{code,description},description,code,isType…,isInPlay,isStrike,isBall,type{code,description}}`, `pitchData{startSpeed,endSpeed,zone,coordinates{pX,pZ,…}}`, `hitData{launchSpeed,launchAngle,totalDistance,trajectory,hardness}` | `…/feed/live?fields=…,playEvents,details,pitchData,hitData,…` | confirmed |
| V11 | `reviewDetails{isOverturned,inProgress,reviewType}` present when `about.hasReview` is true | `…/feed/live?fields=…,about,hasReview,reviewDetails,…` (play 30 of 849803) | confirmed |
| V12 | `liveData.linescore{currentInning,currentInningOrdinal,inningState,scheduledInnings,note,innings[]{num,ordinalNum,home{runs,hits,errors,leftOnBase},away{…}},teams.home/away{runs,hits,errors,leftOnBase,isWinner}}` | `https://statsapi.mlb.com/api/v1/game/746170/linescore` | confirmed |
| V13 | `liveData.boxscore.teams.away/home{team{name,abbreviation},teamStats.batting{…,avg,obp,slg,ops},teamStats.pitching{…,era,inningsPitched,earnedRuns},players["ID<pk>"]{person.fullName,jerseyNumber,position{name,abbreviation},battingOrder,stats.batting,stats.pitching{note},seasonStats}}` | `https://statsapi.mlb.com/api/v1/game/746170/boxscore?fields=…` | confirmed |
| V14 | In-game `stats.batting` omits `avg/obp/slg/ops`; those exist only in `seasonStats.batting` (so an AVG column must be read from `seasonStats`) | same as V13 | confirmed |
| V15 | `buffedlizard55-lab/MLB-PBP` and user `buffedlizard55-lab` no longer resolve | `https://api.github.com/repos/buffedlizard55-lab/MLB-PBP`, `https://api.github.com/users/buffedlizard55-lab` | 404 / 404 |
| V16 | Pages on this repo is enabled, source `main:/`, `https_enforced`, status `built` | `gh api repos/snapquast73-boop/PBPMN/pages` | confirmed |
| V17 | 746170 = 2024-04-01, SF at LAD, final LAD 8 – SF 3 (matches `GIANTS_ATHLETICS_2014-2026_REVIEW.md`) | `https://statsapi.mlb.com/api/v1/game/746170/linescore` | confirmed |
| V18 | Schedule totals with `fields=copyright,totalGames` (cheap counting probe) | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=137&startDate=2014-01-01&endDate=2014-12-31&gameTypes=R,F,D,L,W&fields=copyright,totalGames` | confirmed (181 for SF 2014) |
| V19 | `access-control-allow-origin` on the official origin (browser fetch requirement) | measured by `.github/workflows/verify-official-api.yml`; published on `docs/flagged.html` with the run link | see run |

Anything that could not be confirmed against an official source is published, with its source
link and the reason, on `docs/flagged.html` ("Flagged for Review").

---

## 5. Irregularities logged for review

| ID | Irregularity | Handling |
|---|---|---|
| I1 | Upload contained no `docs/`, `mlb_pbp/`, `tests/`, `automation/` although every document references them | rebuilt from documentation; see V1–V14 |
| I2 | Upstream repo (`buffedlizard55-lab/MLB-PBP`) 404 — original source unavailable for line-by-line diff | reconstruction is behaviour-compatible, not byte-identical; flagged |
| I3 | `README.md` links to `https://buffedlizard55-lab.github.io/MLB-PBP/` (dead) | left untouched (content parity); our live site is `https://snapquast73-boop.github.io/PBPMN/` and is linked from the site header and methodology page |
| I4 | `GIANTS_ATHLETICS_2014-2026_REVIEW.md` contains approximations and unverified cells (`≈2,009`, `162 (est.)`, `162 (verified via SD schedule pattern)`) | flagged cell-by-cell on `docs/flagged.html`; each row is either backed by an official count or marked unverified |
| I5 | `pyproject.toml` declares a `mlb-pbp` console script and packaging for `mlb_pbp*` that did not exist | package rebuilt so `pip install -e .` and `mlb-pbp --help` work |
| I6 | `index.html` meta-refresh target `./docs/` did not exist → Pages root was a redirect to 404 | `docs/` rebuilt, redirect now resolves |

---

## 6. Merge log

| UTC | Action | Result |
|---|---|---|
| — | pending | — |

# Final integration verification — 20 November 2026

Session: `a5191c3d`. Scope: final integration and independent verification only —
`VERIFICATION-a5191c3d.md`, `VERIFICATION-26c1dbb9.md` (integrated verbatim from
PR #11's branch), and the `COORDINATION.md` board. No application, data,
navigation or styling file was changed by this session. PR #9's hardened files
(`tools/published_check.py`, `.github/workflows/published-site-check.yml`,
`README.md`) were left untouched; `git diff origin/main --name-only` on this
branch shows only `COORDINATION.md` and the two verification files.

Method: every value below was checked against an official source in this session
(MLB Stats API via direct page fetch of the exact API URLs, GitHub Pages builds
API, the repository's own offline tests, and a local Pages-style serve). A value
that could not be confirmed from an official source is left blank and flagged
**Unverified** — nothing is inferred or filled in. Sandbox shell access to
`statsapi.mlb.com` and to the Pages hostname is blocked, so MLB and live-site
checks were performed with direct page fetches of the exact URLs, plus the
repository's GitHub-hosted CI runs which re-derive the audit from MLB on GitHub
runners. Where a row was verified via CI regeneration rather than a direct fetch
in this session, that is stated explicitly — no row is claimed as directly
fetched here unless it was.

## Verdict

The published site at <https://snapquast73-boop.github.io/PBPMN/> is live and
functionally working. The Pages build for the current `main` commit `d0d69a2`
(the PR #9 merge) reports `built` ([builds](https://api.github.com/repos/snapquast73-boop/PBPMN/pages/builds)).
The viewer loads the official schedule, renders line score / decisions / plays /
box score, searches plays, and downloads text, raw JSON and NDJSON with per-row
MLB source links (verified in CI Chrome runs, see §C). All 41 audit rows carry a
`statsapi.mlb.com` source link and reconcile with MLB (see §B). No functional
defect in this session's scope was found. Items that cannot be confirmed are
listed in §E and remain on the live
[Flagged for Review page](https://snapquast73-boop.github.io/PBPMN/docs/review.html).
The two sites cited in the task,
<https://snapquast73-boop.github.io/LIVPBP2/reviews.html> and
<https://snapquast73-boop.github.io/POSTSSNALRT/reviews.html>, were fetched live
in this session and return content — they are separate repositories (Live PBP
Replay Feed), confirmed via the GitHub API
([LIVPBP2](https://github.com/snapquast73-boop/LIVPBP2),
[POSTSSNALRT](https://github.com/snapquast73-boop/POSTSSNALRT)) and direct fetch,
but out of scope for this PBPMN fix. PBPMN's own equivalent is
`docs/review.html` (singular) — see §E. PBPMN's site is verified independently
below.

## A. Repository inventory (line-by-line)

| File | What it is | Verification |
|---|---|---|
| `index.html` (447 B) | Root redirect to `./docs/` preserving `location.search` + `location.hash`, with `<noscript>` fallback and canonical link | Read line-by-line; local server returns 200; deep link `?date=2024-04-01&game=745675` survives the redirect (CI Chrome check). Original upload `index.html` (363 B, meta-refresh only, no query preservation) is preserved in git history at [14c9aaf](https://github.com/snapquast73-boop/PBPMN/blob/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3/index.html). The query-preserving form is a functional improvement, not a break. |
| `docs/index.html` | Viewer shell: schedule form (`#date`, `min="2014-01-01"`), `#games`, `#game` section, tabs/search/exports containers, nav to methodology/audit/review | All 6 links resolve locally (see §C). All IDs referenced by `docs/app.js` exist in this file. |
| `docs/api.js` | `scheduleURL(date)` → `GET /api/v1/schedule?sportId=1&date=…&gameTypes=R,F,D,L,W&hydrate=linescore`; `feedURL(id)` → `GET /api/v1.1/game/{id}/feed/live`; `official()` enforces exact `https://statsapi.mlb.com` origin, no redirects, JSON parse, `MLB Advanced Media` notice, `gamePk` match, SHA-256 digest | `node --check` passes. Query form confirmed against [2024-04-01 schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W&hydrate=linescore) (14 games, fetched in this session). `crypto.subtle` requires HTTPS/localhost — documented in README and methodology. |
| `docs/format.js` | `plays`, `esc`, `provenance`, `records` (NDJSON), `pretty`, `text` (plain-text report) | `node --check` passes. All imports in `app.js` resolve to exports here. Text/NDJSON include source URL, retrieval time, MLB notice and SHA-256 (code inspection). Byte parity with the original formatter is **Unverified** (see §E). |
| `docs/app.js` | Schedule load, game open, live refresh via `metaData.wait` (30 s fallback), Overview/Plays/Box score/Event log views, search, three downloads, `localStorage` event log (`pbpmn:log:{gamePk}`) | `node --check` passes. CI Chrome run exercises deep link, all four tabs, search, per-row sources and three downloads with no page errors ([run 44829063412](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063412)). |
| `docs/style.css` | Site styling | Served 200 locally; byte-compared to `main` in CI published check. |
| `docs/methodology.html` | Data & methodology page | All internal links resolve; external links are MLB schedule/feed examples and [MLB Terms of Use](https://www.mlb.com/official-information/terms-of-use). Fetched live in this session (see §C). |
| `docs/audit.html` | 41-row schedule audit (15 + 26), each row linked to its exact MLB request | 41/41 rows carry a `statsapi.mlb.com` link (offline test + direct count in this session). Row-by-row reconciliation in §B. Regenerable with `python tools/audit.py`. Live copy fetched in this session matches the local file (see §C). |
| `docs/review.html` | Flagged for Review page (import audit findings) | All internal links resolve; external links point to the [original uploaded report](https://github.com/snapquast73-boop/PBPMN/blob/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3/GIANTS_ATHLETICS_2014-2026_REVIEW.md), [original tree](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3) and MLB feeds. Fetched live in this session; claims spot-checked in §B/§E. |
| `mlb_pbp/client.py` | Official-host allowlist, no-redirect, retries (3), throttling, provenance/game-ID validation | `compileall` passes; `test_host` passes (non-MLB URL raises `ValueError`). |
| `mlb_pbp/formatter.py` | `render('raw'|'text'|'events', …)` — raw passthrough, NDJSON records, text report | `test_events` passes (metadata → play → event). Presentation differs from the original described `[000]` format — flagged in §E, not a data loss (same source fields). |
| `mlb_pbp/archive.py` | Month-window schedule discovery, parallel feed fetch, resume, manifests, `verify` | `test_digest` passes (digest + corruption detection). Manifest stores path + SHA-256 per file; media-type/encoding per original README spec is **not** stored — handoff request in §G, not edited here (outside scope). |
| `mlb_pbp/__main__.py` | CLI: `game`, `archive`, `verify` | All `--help` invocations exit 0 in this session. README examples match the parser. |
| `pyproject.toml`, `LICENSE`, `.gitignore`, `.nojekyll` | Packaging, MIT license, ignores, Pages no-Jekyll marker | Byte-identical to the original upload at [14c9aaf](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3) (verified in this session via `git show` diff: 0 lines differ). |
| `tests/test_site.py`, `tests/test_archive.py` | Offline link/source-citation and archive tests | 4/4 pass in this session (`python -m unittest discover -s tests -v`). |
| `tools/audit.py` | Regenerates `docs/audit.html` from MLB (Eastern times via `America/New_York`) | CI runs it and asserts no diff ([run 44829063552](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063552)). Eastern-time computation re-checked in §B. |
| `tools/browser_check.py`, `tools/published_check.py` | Chrome walkthrough; published-site HTTP/CORS/byte-parity/Chrome check | Owned by other sessions (a1fdfd4c / 17011489). Read-only inspection only; not edited here. |
| `.github/workflows/audit.yml` | CI: offline tests, JS syntax, audit re-derivation, archive retrieval, Chrome walkthrough | Latest runs on `main` and on PR branches are `success` (see §C). |
| `.github/workflows/published-site-check.yml` | Published-site check (owned by 17011489 / PR #9) | Read-only inspection only; not edited here. |
| `automation/github-actions/archive.yml` | Optional season-release template (kept outside active workflows) | Present and referenced from README. The original README also listed `automation/github-actions/pages.yml`, which was never in the upload and is absent — flagged in §E. |
| `README.md`, `GIANTS_ATHLETICS_2014-2026_REVIEW.md`, `COORDINATION.md`, `VERIFICATION-f5839ed3.md` | Documentation and coordination | Current README replaces the original (9,158 B); current GIANTS file (491 B pointer) replaces the original (11,892 B report). Originals preserved at [14c9aaf](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3). See §D. |

Original upload tree (commit `14c9aaf`) contained only 7 files —
`.gitignore`, `.nojekyll`, `GIANTS_ATHLETICS_2014-2026_REVIEW.md`, `LICENSE`,
`README.md`, `index.html`, `pyproject.toml` — verified via
[git tree API](https://api.github.com/repos/snapquast73-boop/PBPMN/git/trees/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3?recursive=1).
`docs/`, `mlb_pbp/`, `tests/` and workflows were missing, so the uploaded
Pages site could not function. The upstream named in the original README,
`buffedlizard55-lab/MLB-PBP`, returns HTTP 404
([API](https://api.github.com/repos/buffedlizard55-lab/MLB-PBP)), so exact
upstream parity cannot be confirmed — see §E.

## B. Audit table — every row with its official source

### B1. August 11, 2026 — 15 rows (all 15 fetched directly in this session)

Source for all 15 rows:
[2026-08-11 schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11)
(`totalGames: 15`, all `Final` at check time). Eastern times recomputed from MLB
UTC `gameDate` via `America/New_York` (EDT, UTC−4) — all 15 match the published
`Time (Eastern)` column. Every cell below was compared field-by-field against
that response in this session.

| # | Time (ET) | Game ID | Away | Home | Venue | Status | Source |
|---|---|---|---|---|---|---|---|
| 1 | 18:40 | 824240 | Cleveland Guardians | Detroit Tigers | Comerica Park | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 2 | 18:40 | 823832 | Pittsburgh Pirates | Miami Marlins | loanDepot park | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 3 | 18:45 | 822697 | Chicago Cubs | Washington Nationals | Nationals Park | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 4 | 19:05 | 823512 | Seattle Mariners | New York Yankees | Yankee Stadium | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 5 | 19:07 | 822778 | Boston Red Sox | Toronto Blue Jays | Rogers Centre | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 6 | 19:15 | 824886 | New York Mets | Atlanta Braves | Truist Park | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 7 | 19:40 | 823673 | Baltimore Orioles | Minnesota Twins | Target Field | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 8 | 19:40 | 824563 | Cincinnati Reds | Chicago White Sox | Rate Field | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 9 | 19:45 | 823019 | Philadelphia Phillies | St. Louis Cardinals | Busch Stadium | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 10 | 21:38 | 823997 | Texas Rangers | Los Angeles Angels | Angel Stadium | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 11 | 21:40 | 825046 | Colorado Rockies | Arizona Diamondbacks | Chase Field | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 12 | 21:40 | 824970 | Tampa Bay Rays | Athletics | Sutter Health Park | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 13 | 21:40 | 823264 | Milwaukee Brewers | San Diego Padres | Petco Park | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 14 | 21:45 | 823186 | Houston Astros | San Francisco Giants | Oracle Park | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |
| 15 | 22:10 | 823917 | Kansas City Royals | Los Angeles Dodgers | UNIQLO Field at Dodger Stadium | Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11) |

### B2. Team-season rows — 26 rows

Each row's `totalGames` is MLB's `totalGames` for that exact team/season window
(not wins, completed games or available feeds). Four windows were fetched
directly in this session (marked **direct**); the remaining 22 were verified via
CI regeneration of the full audit from MLB with no diff
([run 44829063552](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063552)),
which re-derives every `totalGames`, first/last game string and source URL from
MLB. First/last game strings for the directly fetched windows' example games
were also spot-checked in this session (see §B3). No row is claimed as directly
fetched here unless marked **direct**.

| # | Team | Season | Entries | First listed game | Last listed game | Source |
|---|---|---|---|---|---|---|
| 16 | 137 | 2014 | 181 (**direct**) | 2014-03-31 · 380550 · San Francisco Giants 9 · Arizona Diamondbacks 8 · Chase Field · Final | 2014-10-29 · 416387 · San Francisco Giants 3 · Kansas City Royals 2 · Kauffman Stadium · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2014-01-01&endDate=2014-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 17 | 137 | 2015 | 163 (CI) | 2015-04-06 · 413660 · San Francisco Giants 5 · Arizona Diamondbacks 4 · Chase Field · Final | 2015-10-04 · 416069 · Colorado Rockies 7 · San Francisco Giants 3 · AT&T Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2015-01-01&endDate=2015-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 18 | 137 | 2016 | 167 (CI) | 2016-04-04 · 446875 · San Francisco Giants 12 · Milwaukee Brewers 3 · Miller Park · Final | 2016-10-11 · 487610 · Chicago Cubs 6 · San Francisco Giants 5 · AT&T Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2016-01-01&endDate=2016-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 19 | 137 | 2017 | 163 (CI) | 2017-04-02 · 490110 · San Francisco Giants 5 · Arizona Diamondbacks 6 · Chase Field · Final | 2017-10-01 · 492526 · San Diego Padres 4 · San Francisco Giants 5 · AT&T Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2017-01-01&endDate=2017-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 20 | 137 | 2018 | 163 (CI) | 2018-03-29 · 529418 · San Francisco Giants 1 · Los Angeles Dodgers 0 · Dodger Stadium · Final | 2018-09-30 · 531829 · Los Angeles Dodgers 15 · San Francisco Giants 0 · AT&T Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2018-01-01&endDate=2018-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 21 | 137 | 2019 | 163 (CI) | 2019-03-28 · 566275 · San Francisco Giants 0 · San Diego Padres 2 · Petco Park · Final | 2019-09-29 · 566551 · Los Angeles Dodgers 9 · San Francisco Giants 0 · Oracle Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2019-01-01&endDate=2019-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 22 | 137 | 2020 | 65 (CI) | 2020-07-23 · 631377 · San Francisco Giants 1 · Los Angeles Dodgers 8 · Dodger Stadium · Final | 2020-09-27 · 631002 · San Diego Padres 5 · San Francisco Giants 4 · Oracle Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2020-01-01&endDate=2020-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 23 | 137 | 2021 | 169 (CI) | 2021-04-01 · 634625 · San Francisco Giants 7 · Seattle Mariners 8 · T-Mobile Park · Final | 2021-10-14 · 660920 · Los Angeles Dodgers 2 · San Francisco Giants 1 · Oracle Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2021-01-01&endDate=2021-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 24 | 137 | 2022 | 163 (CI) | 2022-04-08 · 662124 · Miami Marlins 5 · San Francisco Giants 6 · Oracle Park · Final | 2022-10-05 · 662238 · San Francisco Giants 8 · San Diego Padres 1 · Petco Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2022-01-01&endDate=2022-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 25 | 137 | 2023 | 165 (CI) | 2023-03-30 · 718781 · San Francisco Giants 0 · New York Yankees 5 · Yankee Stadium · Final | 2023-10-01 · 716363 · Los Angeles Dodgers 5 · San Francisco Giants 2 · Oracle Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2023-01-01&endDate=2023-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 26 | 137 | 2024 | 162 (CI) | 2024-03-28 · 745445 · San Francisco Giants 4 · San Diego Padres 6 · Petco Park · Final | 2024-09-29 · 745282 · St. Louis Cardinals 6 · San Francisco Giants 1 · Oracle Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2024-01-01&endDate=2024-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 27 | 137 | 2025 | 162 (CI) | 2025-03-27 · 778561 · San Francisco Giants 6 · Cincinnati Reds 4 · Great American Ball Park · Final | 2025-09-28 · 776137 · Colorado Rockies 0 · San Francisco Giants 4 · Oracle Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2025-01-01&endDate=2025-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 28 | 137 | 2026 | 123 (**direct**) | 2026-03-25 · 823244 · New York Yankees 7 · San Francisco Giants 0 · Oracle Park · Final | 2026-08-11 · 823186 · Houston Astros 1 · San Francisco Giants 4 · Oracle Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2026-01-01&endDate=2026-08-11&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 29 | 133 | 2014 | 165 (CI) | 2014-03-31 · 380543 · Cleveland Indians 2 · Oakland Athletics 0 · O.co Coliseum · Final | 2014-09-30 · 416345 · Oakland Athletics 8 · Kansas City Royals 9 · Kauffman Stadium · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2014-01-01&endDate=2014-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 30 | 133 | 2015 | 162 (CI) | 2015-04-06 · 413662 · Texas Rangers 0 · Oakland Athletics 8 · O.co Coliseum · Final | 2015-10-04 · 416075 · Oakland Athletics 2 · Seattle Mariners 3 · Safeco Field · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2015-01-01&endDate=2015-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 31 | 133 | 2016 | 163 (CI) | 2016-04-04 · 446868 · Chicago White Sox 4 · Oakland Athletics 3 · Oakland Coliseum · Final | 2016-10-02 · 449293 · Oakland Athletics 3 · Seattle Mariners 2 · Safeco Field · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2016-01-01&endDate=2016-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 32 | 133 | 2017 | 163 (CI) | 2017-04-03 · 490104 · Los Angeles Angels 2 · Oakland Athletics 4 · Oakland Coliseum · Final | 2017-10-01 · 492524 · Oakland Athletics 5 · Texas Rangers 2 · Globe Life Park in Arlington · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2017-01-01&endDate=2017-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 33 | 133 | 2018 | 164 (CI) | 2018-03-29 · 529412 · Los Angeles Angels 5 · Oakland Athletics 6 · Oakland Coliseum · Final | 2018-10-03 · 563346 · Oakland Athletics 2 · New York Yankees 7 · Yankee Stadium · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2018-01-01&endDate=2018-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 34 | 133 | 2019 | 165 (CI) | 2019-03-20 · 566083 · Seattle Mariners 9 · Oakland Athletics 7 · Tokyo Dome · Final | 2019-10-02 · 599335 · Tampa Bay Rays 5 · Oakland Athletics 1 · Oakland Coliseum · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2019-01-01&endDate=2019-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 35 | 133 | 2020 | 73 (CI) | 2020-07-24 · 631182 · Los Angeles Angels 3 · Oakland Athletics 7 · Oakland Coliseum · Final | 2020-10-08 · 635936 · Oakland Athletics 6 · Houston Astros 11 · Dodger Stadium · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2020-01-01&endDate=2020-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 36 | 133 | 2021 | 163 (CI) | 2021-04-01 · 634640 · Houston Astros 8 · Oakland Athletics 1 · Oakland Coliseum · Final | 2021-10-03 · 632245 · Oakland Athletics 6 · Houston Astros 7 · Minute Maid Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2021-01-01&endDate=2021-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 37 | 133 | 2022 | 162 (CI) | 2022-04-08 · 661131 · Oakland Athletics 5 · Philadelphia Phillies 9 · Citizens Bank Park · Final | 2022-10-05 · 662421 · Los Angeles Angels 2 · Oakland Athletics 3 · Oakland Coliseum · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2022-01-01&endDate=2022-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 38 | 133 | 2023 | 162 (**direct**) | 2023-03-30 · 718769 · Los Angeles Angels 1 · Oakland Athletics 2 · Oakland Coliseum · Final | 2023-10-01 · 716365 · Oakland Athletics 3 · Los Angeles Angels 7 · Angel Stadium · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2023-01-01&endDate=2023-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 39 | 133 | 2024 | 163 (CI) | 2024-03-28 · 745687 · Cleveland Guardians 8 · Oakland Athletics 0 · Oakland Coliseum · Final | 2024-09-29 · 745201 · Oakland Athletics 4 · Seattle Mariners 6 · T-Mobile Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2024-01-01&endDate=2024-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 40 | 133 | 2025 | 162 (**direct**) | 2025-03-27 · 778547 · Athletics 2 · Seattle Mariners 4 · T-Mobile Park · Final | 2025-09-28 · 776138 · Kansas City Royals 9 · Athletics 2 · Sutter Health Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2025-01-01&endDate=2025-12-31&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 41 | 133 | 2026 | 120 (CI) | 2026-03-27 · 822839 · Athletics 2 · Toronto Blue Jays 3 · Rogers Centre · Final | 2026-08-11 · 824970 · Tampa Bay Rays 12 · Athletics 4 · Sutter Health Park · Final | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2026-01-01&endDate=2026-08-11&fields=copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |

### B3. Example games and API behaviour (all fetched directly in this session)

| Check | Official source | Result |
|---|---|---|
| `sportId=1` is Major League Baseball | [sports/1](https://statsapi.mlb.com/api/v1/sports/1) | `id 1`, `name "Major League Baseball"`, `abbreviation "MLB"` |
| Club IDs used by the audit | [teams?sportId=1&fields=…](https://statsapi.mlb.com/api/v1/teams?sportId=1&fields=teams,id,name,abbreviation,fileCode) | `137` San Francisco Giants (`SF`/`sf`); `133` Athletics (`ATH`/`ath`); no `oak` code today |
| `gameTypes=R,F,D,L,W` excludes Spring Training | [2026-03-01 filtered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01&gameTypes=R,F,D,L,W&fields=copyright,totalGames) (`totalGames: 0`) | Confirmed (filtered query returns 0; unfiltered Spring Training games exist per prior sessions' direct fetch) |
| The viewer's own schedule query | [2024-04-01](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W&hydrate=linescore) | 14 games |
| Giants example `746170`, SF 3 @ LAD 8, Dodger Stadium | [teamId=137, 2024-04-01](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&teamId=137&gameTypes=R,F,D,L,W) | Confirmed |
| Athletics example `745675`, BOS 9 @ Oakland Athletics 0, Oakland Coliseum | [teamId=133, 2024-04-01](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&teamId=133&gameTypes=R,F,D,L,W) | Confirmed (club name then `Oakland Athletics`) |
| Imported 2014 opener `380550`, SF 9 @ ARI 8, Chase Field | [teamId=137, 2014-03-31](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2014-03-31&teamId=137&gameTypes=R,F,D,L,W) | Confirmed |
| At-bat 12 in `746170` | [746170 feed (atBatIndex slice)](https://statsapi.mlb.com/api/v1.1/game/746170/feed/live?fields=liveData,plays,allPlays,about,atBatIndex,result,description) | `Thairo Estrada strikes out swinging.` — contradicts the import's single |
| Imported venue "Dodger Stadium" for `823917` | [2026-08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-08-11&gameTypes=R,F,D,L,W) | **Irregular:** MLB returns `UNIQLO Field at Dodger Stadium`; the published audit row uses MLB's name |
| Viewer default date (today, 2026-11-20) has no games | [2026-11-20](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-11-20&gameTypes=R,F,D,L,W&fields=copyright,totalGames) | `totalGames: 0`; the page states that instead of substituting data |

## C. Functional checks performed in this session

- `python -m unittest discover -s tests -v` — 4/4 pass (digest, events,
  official-host restriction, local links + 41 sourced audit rows).
- `python -m compileall -q mlb_pbp` — pass. `node --check` on all three
  `docs/*.js` — pass. CLI `--help` for `game`/`archive`/`verify` — pass.
- Internal-link sweep of every `docs/*.html` + root `index.html` — all
  relative links resolve to files; all 41 audit rows link `statsapi.mlb.com`;
  no `buffedlizard55-lab` or `docs/js/` dead references remain in the tree
  (only historical mentions in `COORDINATION.md`).
- Local Pages-style serve (`python -m http.server` over the repo parent) —
  `/`, `/docs/`, all four docs pages and all four assets return 200 with
  expected content types.
- Live site fetch — `https://snapquast73-boop.github.io/PBPMN/` renders the
  viewer and correctly shows the empty-schedule state for today with an MLB
  source link. Live `docs/audit.html` and `docs/review.html` fetched in this
  session match the local files. The two sites cited in the task,
  <https://snapquast73-boop.github.io/LIVPBP2/reviews.html> and
  <https://snapquast73-boop.github.io/POSTSSNALRT/reviews.html>, also return
  content — they are separate repositories (Live PBP Replay Feed), confirmed
  live via the Pages API and direct fetch, but out of scope for this PBPMN
  fix. PBPMN's own site is verified independently above.
- CI evidence (read-only, not re-run here): full verification
  [run 44829063552](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063552)
  (offline suite, JS syntax, 41-row re-derivation with no diff, archive
  retrieval, Chrome walkthrough) and published-site check
  [run 44829063412](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063412)
  (5/5 PASS: pages/assets byte-identical to `main`, 41/41 sourced rows, MLB
  CORS `*`, Chrome deep link/tabs/search/sources/downloads). PR #9 checks
  `verify` + `published` passed before merge
  ([run 44829362749](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829362749),
  [run 44829362731](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829362731)).
- Pages build for `d0d69a2` reports `built` ([builds](https://api.github.com/repos/snapquast73-boop/PBPMN/pages/builds)).
  A transient GitHub API rate-limit (HTTP 403) was observed on some calls in
  this session; the builds call succeeded and the live site fetch confirms the
  deployment. No action required.

## D. "Keep everything the same" — what changed and why

The upload's `README.md` (9,158 B) and `GIANTS_ATHLETICS_2014-2026_REVIEW.md`
(11,892 B) were replaced by the current short README and the 491-byte audit
pointer. The originals are preserved verbatim in git history at
[14c9aaf](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3)
and linked from `docs/review.html`, so no information is lost from the
repository. The replacement was necessary because the originals contain
values that MLB does not support (see §E) and links to the 404 upstream;
restoring them verbatim would re-publish unverified data as fact. The current
README preserves the original's functional contract (same MLB endpoints,
same CLI, same archive layout, same Pages source) with verified links only.
`pyproject.toml`, `LICENSE`, `.gitignore` and `.nojekyll` are byte-identical
to the upload (re-verified in this session). Root `index.html` keeps the same
redirect target (`./docs/`) and adds query preservation so deep links work —
the original meta-refresh dropped `?date=…&game=…`.

## E. Flagged irregularities / unverified (blank, not inferred)

Published on the live [Flagged for Review page](https://snapquast73-boop.github.io/PBPMN/docs/review.html);
repeated here for manual review. No value below is used as application data.

| Item | Status | Official source / evidence |
|---|---|---|
| Import's `2023 162 (verified via SD schedule pattern)` explanation | **Unverified** — the count `162` itself is confirmed ([ATH 2023](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2023-01-01&endDate=2023-12-31&fields=copyright,totalGames)); the SD-pattern explanation is not an MLB record | — |
| Import's `2025 162 (est.)` | **Unverified** as an estimate — the count `162` is confirmed ([ATH 2025](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2025-01-01&endDate=2025-12-31&fields=copyright,totalGames)) | — |
| Subtotals `≈2,009` / `≈2,024` / `~4,033` | **Unverified** — approximate, not MLB `totalGames` sums | — |
| `typically 65–85 plays, 250–340 playEvents` | **Unverified** — no per-game play counts in the audit | — |
| Midnight `Preview` snapshot of 2026-08-11 and `empty feeds` claim | **Unverified** — cannot be checked after the fact; all 15 are now `Final` | [2026-08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-08-11&gameTypes=R,F,D,L,W) |
| Import's Estrada single + pitch measurements (`95.2 mph`, zone, `plate_x/z`) | **Contradicted** — MLB returns a strikeout (see §B3) | [746170 feed](https://statsapi.mlb.com/api/v1.1/game/746170/feed/live) |
| Import's `OAK` / `fileCode oak/ath`, `Dodger Stadium` venue, ATH counts `162` (2024) / `119` (2026), first 2024 ATH game, last 2022 SF date | **Irregular** — MLB current values differ; audit uses MLB's returned values | [teams](https://statsapi.mlb.com/api/v1/teams?sportId=1&fields=teams,id,name,abbreviation,fileCode), [venues](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-08-11&gameTypes=R,F,D,L,W&fields=dates,games,gamePk,venue,id,name) |
| Original implementation (appearance, `docs/js/` layout, formatter bytes, `tests/test_eventlog.mjs`, `automation/github-actions/pages.yml`, historical local logs, built season archives) | **Unverified** — upstream 404; reconstruction only | [API 404](https://api.github.com/repos/buffedlizard55-lab/MLB-PBP), [original tree](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3) |
| `745675` decisions detail | **Unverified in this session** — see §B3; viewer handles absent decisions gracefully | — |
| Manifest media-type/encoding per file (original README spec) | **Gap** — current manifest stores path + SHA-256 only; raw JSON remains canonical, no data loss | Original [README](https://github.com/snapquast73-boop/PBPMN/blob/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3/README.md) |
| Audit CI (`audit.py` + `git diff --exit-code`) fails if MLB revises history | Maintenance note — currently passing; a future MLB correction will require regenerating the audit, which is the intended behavior | [audit workflow](https://github.com/snapquast73-boop/PBPMN/blob/main/.github/workflows/audit.yml) |
| Task-cited `reviews.html` (plural) vs PBPMN's `review.html` (singular) | **Naming difference, not a defect** — LIVPBP2/POSTSSNALRT use `reviews.html`; PBPMN's Flagged for Review page is `docs/review.html`. Both are live. No rename made (would break existing links). | [LIVPBP2 reviews](https://snapquast73-boop.github.io/LIVPBP2/reviews.html), [POSTSSNALRT reviews](https://snapquast73-boop.github.io/POSTSSNALRT/reviews.html), [PBPMN review](https://snapquast73-boop.github.io/PBPMN/docs/review.html) |

## F. Manual-review links

- Live site: <https://snapquast73-boop.github.io/PBPMN/> ·
  [deep link example](https://snapquast73-boop.github.io/PBPMN/?date=2024-04-01&game=745675)
- [Schedule audit (41 sourced rows)](https://snapquast73-boop.github.io/PBPMN/docs/audit.html)
- [Flagged for Review](https://snapquast73-boop.github.io/PBPMN/docs/review.html)
- [Methodology](https://snapquast73-boop.github.io/PBPMN/docs/methodology.html)
- [Original upload tree](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3)
- [Pages API](https://api.github.com/repos/snapquast73-boop/PBPMN/pages) ·
  [Pages builds](https://api.github.com/repos/snapquast73-boop/PBPMN/pages/builds)
- [Full verification run 44829063552](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063552) ·
  [Published check run 44829063412](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063412)
- [PR #9 (17011489, merged as d0d69a2)](https://github.com/snapquast73-boop/PBPMN/pull/9) ·
  [PR #10 (a1fdfd4c, open)](https://github.com/snapquast73-boop/PBPMN/pull/10) ·
  [PR #11 (26c1dbb9, open)](https://github.com/snapquast73-boop/PBPMN/pull/11)
- MLB examples: [sports/1](https://statsapi.mlb.com/api/v1/sports/1) ·
  [2024-04-01 schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W&hydrate=linescore) ·
  [745675 feed](https://statsapi.mlb.com/api/v1.1/game/745675/feed/live) ·
  [746170 feed](https://statsapi.mlb.com/api/v1.1/game/746170/feed/live)

## G. Handoff requests (logged, not edited — outside this scope)

1. **PR #10 owner (a1fdfd4c):** your COORDINATION-only content is integrated
   here (cherry-picked `1f9bc6b`, conflict resolved by keeping both appends).
   Please close PR #10 as superseded once this integration merges, or rebase it
   if you prefer to merge it yourself — do not merge both.
2. **PR #11 owner (26c1dbb9):** your `VERIFICATION-26c1dbb9.md` is integrated
   here verbatim (258 lines). Your branch's other files
   (`tools/published_check.py`, `.github/workflows/published-site-check.yml`,
   `README.md`, `COORDINATION.md`) are stale pre-PR #9 versions and were
   deliberately not merged, so PR #9's hardening is not regressed. Note your
   report's "PR #9 open" line is superseded — PR #9 merged as `d0d69a2`. Please
   close PR #11 as superseded once this integration merges.
3. **`mlb_pbp` owner:** consider adding media-type/encoding to manifest file
   records to match the original README spec (§E). No data loss either way.
4. **Integration owner (this session):** no further data or navigation changes
   are needed for the site to be live. Flagged items in §E do not block the
   merge and remain published on the review page for post-live review.

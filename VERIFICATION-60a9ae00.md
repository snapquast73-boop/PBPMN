# Verification report — session `60a9ae00` (2026-11-22)

Final integration verification of the PBPMN repository and its published GitHub Pages site.
Every value below was checked in this session against the official source linked in the same row.
No value is inferred; anything that cannot be confirmed from an official source is left to the
[Flagged for Review page](https://snapquast73-boop.github.io/PBPMN/docs/review.html) and is not
restated as fact.

Sandbox note: direct `curl`/Python egress is restricted to GitHub hosts in this environment, so
official MLB responses were fetched through the page-fetch tool (which reaches
`statsapi.mlb.com`), and GitHub-side evidence through `gh`/API. Each fetch URL is listed so a
reviewer can re-open it in a browser.

## A. Repository review, line by line, against the original upload

The original upload is commit
[`14c9aaf`](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3)
(7 files, "Add files via upload"). Every file in the current tree was compared with it:

| File | State vs original upload | Evidence / decision |
| --- | --- | --- |
| `.gitignore` | **byte-identical** | `git show 14c9aaf:.gitignore` diff empty |
| `.nojekyll` | **byte-identical** | diff empty; served 200 locally and on Pages |
| `LICENSE` | **byte-identical** | diff empty |
| `pyproject.toml` | **byte-identical** | diff empty |
| `index.html` (root) | changed on purpose | now a query- and hash-preserving redirect (`location.replace("./docs/" + location.search + location.hash)` + `<noscript>` refresh). Original was a meta-refresh that dropped query strings, which broke `?date=…&game=…` deep links. Verified: redirect preserves query locally and on the live site (published-site check §1) |
| `README.md` | rewritten | the original pointed at the retired upstream site (`buffedlizard55-lab.github.io/MLB-PBP`, repository returns HTTP 404 — [API](https://api.github.com/repos/buffedlizard55-lab/MLB-PBP)). The current README documents this deployment, the restored `docs/js/` layout and the exact original test commands. Original text remains in git history at `14c9aaf` |
| `GIANTS_ATHLETICS_2014-2026_REVIEW.md` | replaced by a source-audit stub | the imported report contained unverified estimates (flagged on the review page). The stub links the [schedule audit](docs/audit.html) and [Flagged for Review](docs/review.html). Full original text preserved at `14c9aaf` |
| `docs/` (viewer, style, 4 JS modules, audit/review/methodology pages) | absent from upload → restored | paths match the original README's own map (`docs/js/api.js`, `docs/js/format.js`, `docs/js/app.js`), plus `docs/js/eventlog.js` for the documented Event log |
| `mlb_pbp/` (client, formatter, archive, CLI) | absent from upload → restored | matches the original README's repository map (`mlb_pbp/client.py`, `mlb_pbp/formatter.py`, `mlb_pbp/archive.py`) |
| `tests/` (`test_site.py`, `test_archive.py`, `test_eventlog.mjs`) | absent → restored | includes `node --test tests/test_eventlog.mjs`, a command the original README names |
| `tools/` (`audit.py`, `browser_check.py`, `published_check.py`) | absent → added | `tools/audit.py` regenerates the public snapshot from MLB; the other two verify the deployment |
| `.github/workflows/audit.yml`, `published-site-check.yml` | absent → added | CI that reconciles all published rows with MLB and verifies the live site after each deployment |
| `automation/github-actions/{archive,pages}.yml` | absent → restored | both are inactive templates under `automation/`, exactly as the original README's repository map describes |
| `COORDINATION.md`, `VERIFICATION-*.md`, `GIANTS…` review, `README` status notes | added by parallel sessions | coordination and evidence only; no site data |

Dead-reference sweep: no file in the tree links the retired upstream repository or the pre-`js/`
module paths (grep over `*.html`, `*.js`, `*.md`, `*.py`, excluding coordination/evidence logs).

## B. Published table rows — every row, every field, official source

Source of the published table: [docs/audit.html](https://snapquast73-boop.github.io/PBPMN/docs/audit.html)
(local file identical to `main`; the published-site check re-proves byte parity after every deploy).

Structure: 41 data rows = 15 daily rows (2026-08-11) + 26 club-season rows (teams 137, 133 × 2014–2026).
**Every row carries a `statsapi.mlb.com` source link** (checked programmatically: 41/41; enforced
offline by `tests/test_site.py` and live by `tools/published_check.py`).

### B1. Daily rows (15/15 verified field-for-field)

Official source for all 15 rows (fetched this session, `totalGames: 15`, copyright present):
[schedule?date=2026-08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11&fields=copyright,totalGames,dates,date,games,gamePk,gameDate,status,detailedState,teams,away,home,team,name,venue)

Each published cell — Eastern time (computed from MLB's UTC `gameDate`, EDT = UTC−4 on that
date), game ID, away club, home club, venue, status — was compared to that response:

| # | Game ID | Result |
| --- | --- | --- |
| 1 | 824240 | ✅ 18:40 · Cleveland Guardians @ Detroit Tigers · Comerica Park · Final |
| 2 | 823832 | ✅ 18:40 · Pittsburgh Pirates @ Miami Marlins · loanDepot park · Final |
| 3 | 822697 | ✅ 18:45 · Chicago Cubs @ Washington Nationals · Nationals Park · Final |
| 4 | 823512 | ✅ 19:05 · Seattle Mariners @ New York Yankees · Yankee Stadium · Final |
| 5 | 822778 | ✅ 19:07 · Boston Red Sox @ Toronto Blue Jays · Rogers Centre · Final |
| 6 | 824886 | ✅ 19:15 · New York Mets @ Atlanta Braves · Truist Park · Final |
| 7 | 823673 | ✅ 19:40 · Baltimore Orioles @ Minnesota Twins · Target Field · Final |
| 8 | 824563 | ✅ 19:40 · Cincinnati Reds @ Chicago White Sox · Rate Field · Final |
| 9 | 823019 | ✅ 19:45 · Philadelphia Phillies @ St. Louis Cardinals · Busch Stadium · Final |
| 10 | 823997 | ✅ 21:38 · Texas Rangers @ Los Angeles Angels · Angel Stadium · Final |
| 11 | 825046 | ✅ 21:40 · Colorado Rockies @ Arizona Diamondbacks · Chase Field · Final |
| 12 | 824970 | ✅ 21:40 · Tampa Bay Rays @ Athletics · Sutter Health Park · Final |
| 13 | 823264 | ✅ 21:40 · Milwaukee Brewers @ San Diego Padres · Petco Park · Final |
| 14 | 823186 | ✅ 21:45 · Houston Astros @ San Francisco Giants · Oracle Park · Final |
| 15 | 823917 | ✅ 22:10 · Kansas City Royals @ Los Angeles Dodgers · **UNIQLO Field at Dodger Stadium** · Final — MLB's current venue name; the import's "Dodger Stadium" stays flagged |

Result: **15/15 rows match official MLB field-for-field**, each with its source link.

### B2. Club-season rows — schedule-entry counts (26/26 verified)

Each count was re-fetched from the row's own source URL family with
`fields=copyright,totalGames`:

| Team | Season windows fetched | Result |
| --- | --- | --- |
| 137 San Francisco Giants | 2014→2026 (13 windows: [2014](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2014-01-01&endDate=2014-12-31&fields=copyright,totalGames), …, [2026 to 08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2026-01-01&endDate=2026-08-11&fields=copyright,totalGames)) | ✅ 181, 163, 167, 163, 163, 163, 65, 169, 163, 165, 162, 162, 123 — all match the published column |
| 133 Athletics | 2014→2026 (13 windows: [2014](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2014-01-01&endDate=2014-12-31&fields=copyright,totalGames), …, [2026 to 08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2026-01-01&endDate=2026-08-11&fields=copyright,totalGames)) | ✅ 165, 162, 163, 163, 164, 165, 73, 163, 162, 162, 163, 162, 120 — all match the published column |

Result: **26/26 counts match official `totalGames`.**

### B3. Club-season rows — first/last listed game cells (26/26 verified)

For every row, narrow official windows around the published first and last dates were fetched
(e.g. [SF first 2014](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2014-01-01&endDate=2014-03-31&fields=copyright,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue),
[SF last 2014](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2014-10-29&endDate=2014-12-31&fields=copyright,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue)
— the same field list the row's own source link uses) and the complete cell strings were compared:

- ✅ **26/26 first-game cells match** official `officialDate · gamePk · away score · home score · venue · status`
  (including the Athletics' 2019 first game at the Tokyo Dome and the 2026 opener at Rogers Centre).
- ✅ **26/26 last-game cells match** (including SF 2014 WS clincher `416387` at Kauffman Stadium,
  ATH 2020 last `635936` at Dodger Stadium, and both 2026-08-11 finals).

Result: **all 26 rows match official MLB field-for-field, 0 mismatches.**

### B4. Cross-checks of values the review page depends on

| Claim | Official source | Result |
| --- | --- | --- |
| `sportId=1` is Major League Baseball | [sports/1](https://statsapi.mlb.com/api/v1/sports/1) | ✅ `id 1`, `name "Major League Baseball"` |
| Club IDs 137/133 and today's codes | [teams?sportId=1](https://statsapi.mlb.com/api/v1/teams?sportId=1&fields=teams,id,name,abbreviation,fileCode&teamId=137,133) | ✅ 137 `San Francisco Giants` (`SF`, `sf`); 133 `Athletics` (`ATH`, `ath`) — no `oak` code today, which is why the import's `OAK` stays flagged |
| `gameTypes=R,F,D,L,W` excludes Spring Training | [2026-03-01 unfiltered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01&fields=copyright,totalGames,dates,games,gameType) (16 games, all `gameType S`) vs [filtered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01&gameTypes=R,F,D,L,W&fields=copyright,totalGames) (`0`) | ✅ confirmed |
| The viewer's own schedule query returns data | [2024-04-01 hydrate=linescore](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W&hydrate=linescore&fields=copyright,totalGames) | ✅ 14 games (matches the live deep link's 14 game cards) |
| 745675 decisions shown on the live page | [745675 feed](https://statsapi.mlb.com/api/v1.1/game/745675/feed/live?fields=gamePk,gameData,teams,away,home,name,liveData,linescore,decisions,winner,loser,save,fullName) | ✅ winner Tanner Houck, loser Joe Boyle, save Chase Anderson — exactly what the live page renders |
| Import's "Thairo Estrada single" at at-bat 12 of 746170 | [746170 feed, allPlays](https://statsapi.mlb.com/api/v1.1/game/746170/feed/live?fields=liveData,plays,allPlays,about,atBatIndex,result,description) | ✅ official description is "Thairo Estrada strikes out swinging." — the import's single stays flagged and is not published |
| Today (2026-11-22) has no qualifying games | [2026-11-22](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-11-22&gameTypes=R,F,D,L,W&fields=copyright,totalGames) | ✅ `totalGames: 0`; the viewer states "No qualifying games on this date." with an MLB source link instead of substituting data |

## C. Build, tests and links (site builds with no broken links)

| Check | Command / method | Result |
| --- | --- | --- |
| Offline unit tests | `python -m unittest discover -s tests -v` | ✅ 5/5 pass (includes the 41-row source-link rule and module-layout rule) |
| Package compiles | `python -m compileall -q mlb_pbp tools` | ✅ |
| JS syntax (all four modules) | `node --check docs/js/{api,app,eventlog,format}.js` | ✅ 4/4 |
| Event log tests | `node --test tests/test_eventlog.mjs` | ✅ 9/9 pass (synthetic fixtures, no network) |
| CLI help | `python -m mlb_pbp --help` | ✅ |
| Internal links (HTML + README + module imports + workflow templates) | local sweep | ✅ 37 references checked, **0 missing** |
| Audit row citations | local sweep | ✅ 41/41 rows link `statsapi.mlb.com` |
| Pages-style local serve (repo mounted at `/PBPMN/`) | 14 paths + query-bearing root URL | ✅ all 200 with expected content types; root redirect preserves query+hash |
| CI on this branch | [verify run 44975192093](https://github.com/snapquast73-boop/PBPMN/actions/runs/44975192093) (dispatch) and [44974138781](https://github.com/snapquast73-boop/PBPMN/actions/runs/44974138781) (push) | ✅ both green: offline suite, **full 41-row MLB re-derivation with no diff**, real archive window with digest verification, Chrome walkthrough of deep links/tabs/search/per-row sources/three downloads |
| Published-site check on this branch | [run 44974138726](https://github.com/snapquast73-boop/PBPMN/actions/runs/44974138726) → [readable report](https://github.com/snapquast73-boop/PBPMN/commit/451dc47#commitcomment) | ✅ **PASS 5/5**: five pages 200 and byte-identical to `main`, 41/41 sourced rows, MLB `Access-Control-Allow-Origin: *` for the Pages origin, Chrome run of `?date=2024-04-01&game=745675` with no page errors |

## D. Live site verification (fetched this session)

| Page | Result |
| --- | --- |
| <https://snapquast73-boop.github.io/PBPMN/> | ✅ 200; query-preserving redirect into `docs/` |
| `docs/` viewer (today) | ✅ renders; "No qualifying games on this date." + MLB source link (correct for the off-season) |
| `docs/?date=2026-08-11` | ✅ all 15 official games listed, matching MLB names/venues/times |
| `docs/?date=2024-04-01&game=745675` | ✅ 14-game schedule; line score 9–0; decisions Houck/Boyle/Anderson; every table row links the official feed; three export buttons present |
| `docs/audit.html` | ✅ serves both tables, 41 sourced rows, byte-identical to `main` |
| `docs/review.html` | ✅ Flagged for Review page serves every published finding |
| `docs/methodology.html` | ✅ serves; links MLB terms of use |
| [Pages API](https://api.github.com/repos/snapquast73-boop/PBPMN/pages) / [builds](https://api.github.com/repos/snapquast73-boop/PBPMN/pages/builds/latest) | ✅ `status: built`, source `main` at `/`, `build_type: legacy`, latest build for `1d6f962` |

## E. Triage of stale parallel work (takeover rule: >60 min, no commits)

### PR #11 (`arena/26c1dbb9-pbpmn`, "Independent line-by-line verification")

- State observed: `CONFLICTING` / `mergeable: false`, last updated 2026-11-20T22:33Z — older than
  60 minutes with no further commits, so the takeover rule in `COORDINATION.md` applies.
- Content analysis:
  - `VERIFICATION-26c1dbb9.md` on that branch is **byte-identical** to the copy already in `main`
    (integrated verbatim by session a5191c3d in PR #12) — merging would add nothing.
  - The branch's `COORDINATION.md`, `tools/published_check.py`, workflows, `README.md` and
    `docs/*.js` are all **older than** current `main`: merging the branch would revert PR #9's
    hardened published-site check and PR #16's restored `docs/js/` layout (its head still has
    `docs/api.js` at the old path and no `docs/js/eventlog.js`).
  - Its one unique artifact — the `## Session 26c1dbb9` board section — was **not** in `main`.
- Action taken: that unique section was integrated into `COORDINATION.md` on this branch (nothing
  from the branch discarded), and PR #11 is closed as superseded, with a comment pointing at the
  integrated section. No application file from the stale branch is merged.

### Issue #1 ("Parallel integration handoff: missing app and review findings")

- All findings in the issue are already published: missing app restored (PR #2, #16), review
  findings on the live Flagged for Review page, handoffs acknowledged by later sessions.
- Action taken: closed with a final comment summarising the current verified state; the issue's
  evidence comments remain readable.

## F. Irregularities (non-blocking; all already on the Flagged for Review page)

Nothing new was found that is not already published on
[docs/review.html](https://snapquast73-boop.github.io/PBPMN/docs/review.html). Carried forward:

1. The import's midnight `Preview` snapshot of 2026-08-11 and "empty feeds" claim cannot be
   re-checked after the fact (official schedule now shows 15 finals).
2. The import's `OAK` identifiers, "Dodger Stadium" venue string, wrong Athletics game ID
   (`823512` is Mariners @ Yankees; the Athletics game is `824970`), and the contradicted
   Estrada single/pitch measurements at 746170 at-bat 12.
3. Unverified explanations in the import: "2023 162 (verified via SD schedule pattern)",
   "2025 162 (est.)", subtotals `≈2,009`/`≈2,024`/`~4,033`, "typically 65–85 plays, 250–340
   playEvents". Not published as fact; replaced by sourced rows in `docs/audit.html`.
4. The original upstream repository returns HTTP 404, so exact byte parity with the retired
   site (appearance, original formatter bytes, historical local logs) remains unverifiable.
5. The Event log's documented scope in the imported README is broader than the reconstruction;
   the implemented behaviour is published as verified, the rest as unverified.
6. `automation/github-actions/*.yml` are inactive templates (by design: publishing must not
   start bulk downloads).

## G. Sources (official)

MLB Stats API (all fetched in this session): [sports/1](https://statsapi.mlb.com/api/v1/sports/1) ·
[teams](https://statsapi.mlb.com/api/v1/teams?sportId=1&fields=teams,id,name,abbreviation,fileCode&teamId=137,133) ·
[daily schedule 2026-08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11&fields=copyright,totalGames,dates,date,games,gamePk,gameDate,status,detailedState,teams,away,home,team,name,venue) ·
26 club-season windows (each row's own source link in `docs/audit.html`) ·
[first/last windows](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2014-01-01&endDate=2014-03-31&fields=copyright,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue)
(row field list) · [745675 feed](https://statsapi.mlb.com/api/v1.1/game/745675/feed/live) ·
[746170 allPlays](https://statsapi.mlb.com/api/v1.1/game/746170/feed/live?fields=liveData,plays,allPlays,about,atBatIndex,result,description) ·
[2026-03-01 unfiltered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01&fields=copyright,totalGames,dates,games,gameType) vs
[filtered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01&gameTypes=R,F,D,L,W&fields=copyright,totalGames) ·
[2024-04-01 viewer query](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W&hydrate=linescore&fields=copyright,totalGames) ·
[2026-11-22](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-11-22&gameTypes=R,F,D,L,W&fields=copyright,totalGames).

GitHub: [original upload tree](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3) ·
[upstream repository API (404)](https://api.github.com/repos/buffedlizard55-lab/MLB-PBP) ·
[Pages configuration](https://api.github.com/repos/snapquast73-boop/PBPMN/pages) ·
[latest Pages build](https://api.github.com/repos/snapquast73-boop/PBPMN/pages/builds/latest) ·
[GitHub Pages publishing docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) ·
CI runs linked in section C.

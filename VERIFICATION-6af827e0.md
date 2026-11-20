# Independent verification of the published `main` — 20 November 2026

Session: `6af827e0`. Scope: read-only independent verification of the current `main`
(`04dcb02`, the PR #12 integration merge) and the live GitHub Pages site. No application,
data, navigation, styling, test or workflow file was changed by this session, and no other
owner's scope was edited. This session does **not** duplicate the final integration that
session `a5191c3d` completed in [PR #12](https://github.com/snapquast73-boop/PBPMN/pull/12).

Method: every value below was checked against an official source in this session — direct
fetches of MLB's own Stats API URLs (the exact requests the site and the audit use), direct
fetches of the live Pages pages, the repository's offline suite, and the GitHub-hosted CI
runs on this session's branch. A value that could not be confirmed is left out and flagged
**Unverified**; nothing is inferred or filled in.

## A. Official reference identities

| Check | Official source | Result |
|---|---|---|
| `sportId=1` is Major League Baseball | [sports/1](https://statsapi.mlb.com/api/v1/sports/1) | Confirmed: `id 1`, `name "Major League Baseball"`, `abbreviation "MLB"`. |
| Club IDs used by the audit | [teams?sportId=1&fields=teams,id,name,abbreviation,fileCode](https://statsapi.mlb.com/api/v1/teams?sportId=1&fields=teams,id,name,abbreviation,fileCode) | Confirmed: `137` San Francisco Giants (`SF`/`sf`); `133` Athletics (`ATH`/`ath`). No `oak` fileCode is returned today. |
| `gameTypes=R,F,D,L,W` excludes Spring Training | [2026-03-01 unfiltered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01) vs [filtered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01&gameTypes=R,F,D,L,W&fields=copyright,totalGames) | The filtered request returns `totalGames: 0`; Spring Training games are excluded. |

## B. August 11, 2026 — all 15 schedule rows

Source for every row: [2026-08-11 schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&date=2026-08-11&fields=dates,games,gamePk,gameDate,status,detailedState,teams,away,home,team,name,venue)
(`totalGames: 15`). Eastern times recomputed from MLB's UTC `gameDate` at UTC−4 (EDT);
all 15 match the published `Time (Eastern)` column, and every row is `Final`.

| Time (ET) | Game ID | Away | Home | Venue | Status |
|---|---|---|---|---|---|
| 18:40 | 824240 | Cleveland Guardians | Detroit Tigers | Comerica Park | Final |
| 18:40 | 823832 | Pittsburgh Pirates | Miami Marlins | loanDepot park | Final |
| 18:45 | 822697 | Chicago Cubs | Washington Nationals | Nationals Park | Final |
| 19:05 | 823512 | Seattle Mariners | New York Yankees | Yankee Stadium | Final |
| 19:07 | 822778 | Boston Red Sox | Toronto Blue Jays | Rogers Centre | Final |
| 19:15 | 824886 | New York Mets | Atlanta Braves | Truist Park | Final |
| 19:40 | 823673 | Baltimore Orioles | Minnesota Twins | Target Field | Final |
| 19:40 | 824563 | Cincinnati Reds | Chicago White Sox | Rate Field | Final |
| 19:45 | 823019 | Philadelphia Phillies | St. Louis Cardinals | Busch Stadium | Final |
| 21:38 | 823997 | Texas Rangers | Los Angeles Angels | Angel Stadium | Final |
| 21:40 | 825046 | Colorado Rockies | Arizona Diamondbacks | Chase Field | Final |
| 21:40 | 824970 | Tampa Bay Rays | Athletics | Sutter Health Park | Final |
| 21:40 | 823264 | Milwaukee Brewers | San Diego Padres | Petco Park | Final |
| 21:45 | 823186 | Houston Astros | San Francisco Giants | Oracle Park | Final |
| 22:10 | 823917 | Kansas City Royals | Los Angeles Dodgers | UNIQLO Field at Dodger Stadium | Final |

## C. Team-season windows — all 26 `totalGames` values

Each value below was fetched directly from the exact URL published in the `Source` column of
`docs/audit.html` (the `fields=copyright,totalGames` form of the same request). All 26 match.

| Team ID | Season | Window end | MLB `totalGames` | Audit row |
|---|---|---|---|---|
| 137 | 2014 | 2014-12-31 | 181 | 181 |
| 137 | 2015 | 2015-12-31 | 163 | 163 |
| 137 | 2016 | 2016-12-31 | 167 | 167 |
| 137 | 2017 | 2017-12-31 | 163 | 163 |
| 137 | 2018 | 2018-12-31 | 163 | 163 |
| 137 | 2019 | 2019-12-31 | 163 | 163 |
| 137 | 2020 | 2020-12-31 | 65 | 65 |
| 137 | 2021 | 2021-12-31 | 169 | 169 |
| 137 | 2022 | 2022-12-31 | 163 | 163 |
| 137 | 2023 | 2023-12-31 | 165 | 165 |
| 137 | 2024 | 2024-12-31 | 162 | 162 |
| 137 | 2025 | 2025-12-31 | 162 | 162 |
| 137 | 2026 | 2026-08-11 | 123 | 123 |
| 133 | 2014 | 2014-12-31 | 165 | 165 |
| 133 | 2015 | 2015-12-31 | 162 | 162 |
| 133 | 2016 | 2016-12-31 | 163 | 163 |
| 133 | 2017 | 2017-12-31 | 163 | 163 |
| 133 | 2018 | 2018-12-31 | 164 | 164 |
| 133 | 2019 | 2019-12-31 | 165 | 165 |
| 133 | 2020 | 2020-12-31 | 73 | 73 |
| 133 | 2021 | 2021-12-31 | 163 | 163 |
| 133 | 2022 | 2022-12-31 | 162 | 162 |
| 133 | 2023 | 2023-12-31 | 162 | 162 |
| 133 | 2024 | 2024-12-31 | 163 | 163 |
| 133 | 2025 | 2025-12-31 | 162 | 162 |
| 133 | 2026 | 2026-08-11 | 120 | 120 |

The remaining fields of each row (first/last listed game) were checked directly for the
windows below; the full 41-row regeneration from MLB is enforced by CI (`python tools/audit.py`
with `git diff --exit-code docs/audit.html`).

| Window | First / last listed game | Official source |
|---|---|---|
| 137 2014 | first `2014-03-31 · 380550 · San Francisco Giants 9 · Arizona Diamondbacks 8 · Chase Field · Final`; last `2014-10-29 · 416387 · San Francisco Giants 3 · Kansas City Royals 2 · Kauffman Stadium · Final` | [2014-03-31](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&date=2014-03-31&fields=dates,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue), [2014-10-29](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&date=2014-10-29&fields=dates,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 137 2026 | first `2026-03-25 · 823244 · New York Yankees 7 · San Francisco Giants 0 · Oracle Park · Final`; last `2026-08-11 · 823186 · Houston Astros 1 · San Francisco Giants 4 · Oracle Park · Final` | [2026-03-25](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&date=2026-03-25&fields=dates,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue), [2026-08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&date=2026-08-11&fields=dates,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 133 2014 | first `2014-03-31 · 380543 · Cleveland Indians 2 · Oakland Athletics 0 · O.co Coliseum · Final` | [2014-03-31](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&date=2014-03-31&fields=dates,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 133 2024 | first `2024-03-28 · 745687 · Cleveland Guardians 8 · Oakland Athletics 0 · Oakland Coliseum · Final` | [2024-03-28](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&date=2024-03-28&fields=dates,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |
| 133 2026 | last `2026-08-11 · 824970 · Tampa Bay Rays 12 · Athletics 4 · Sutter Health Park · Final` | [2026-08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&date=2026-08-11&fields=dates,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue) |

## D. Viewer examples and current schedule

| Check | Official source | Result |
|---|---|---|
| The viewer's own schedule query | [2024-04-01](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W&hydrate=linescore&fields=copyright,totalGames) | `totalGames: 14`. |
| Athletics example feed | [745675](https://statsapi.mlb.com/api/v1.1/game/745675/feed/live?fields=gamePk,gameData,teams,away,home,name,liveData,linescore,decisions,winner,loser,save,fullName) | `gamePk 745675`, Boston Red Sox at Oakland Athletics; decisions winner Tanner Houck, loser Joe Boyle, save Chase Anderson. |
| Giants example feed, at-bat 12 | [746170 plays](https://statsapi.mlb.com/api/v1.1/game/746170/feed/live?fields=liveData,plays,allPlays,about,atBatIndex,result,description) | `atBatIndex 12` → “Thairo Estrada strikes out swinging.” This contradicts the imported report’s single; the review page flags it. |
| Viewer default date (today, 2026-11-20) | [2026-11-20](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-11-20&gameTypes=R,F,D,L,W&fields=copyright,totalGames) | `totalGames: 0`; the live page says so instead of substituting data. |

## E. Live site (fetched directly in this session)

- `https://snapquast73-boop.github.io/PBPMN/` redirects into `docs/` and preserves the query
  string; the deep link `?date=2024-04-01&game=745675` loaded MLB’s 14-game schedule and
  rendered the 745675 line score (Boston 9, Oakland 0; 9 innings) and decisions
  (Houck / Boyle / Anderson), each row carrying its `statsapi.mlb.com` source link.
- `https://snapquast73-boop.github.io/PBPMN/docs/audit.html` serves all 41 rows, each with an
  official `statsapi.mlb.com` source link; `docs/review.html` and `docs/methodology.html`
  render with working internal links.

## F. Offline checks and CI on this branch

- `python -m unittest discover -s tests -v` — 4/4 pass (archive digest, event serialization,
  official-host restriction, internal links + 41 sourced audit rows).
- `python -m compileall -q mlb_pbp` — pass. `node --check` on `docs/api.js`, `docs/app.js`,
  `docs/format.js` — pass. `python -m mlb_pbp --help` — pass.
- [Verify archive and Pages viewer — run 44830766241](https://github.com/snapquast73-boop/PBPMN/actions/runs/44830766241)
  — SUCCESS on this branch: offline suite, JS syntax, full re-derivation of the 41 audit rows
  from MLB with no diff, official archive retrieval and digest verification, and the Chrome
  walkthrough.
- [Published site check — run 44830766301](https://github.com/snapquast73-boop/PBPMN/actions/runs/44830766301)
  — PASS 5/5 against the live URL: every published page and asset returns 200 and is
  byte-identical to `origin/main`, 41/41 audit rows cite `statsapi.mlb.com`, both MLB
  endpoints send `Access-Control-Allow-Origin: *` for the Pages origin, and Chrome follows
  the deep link through all four tabs, search, per-row sources and the three downloads with
  no page errors. [Readable report](https://github.com/snapquast73-boop/PBPMN/commit/ec428069d83e907ff3e8185612136b1fa371e3f9#commitcomment-211115659).

## G. Deployment state

- `main` was `04dcb02` ([PR #12](https://github.com/snapquast73-boop/PBPMN/pull/12)) when the
  live checks below were made; it has since moved to `ddeabd8` through the documentation-only
  [PR #13](https://github.com/snapquast73-boop/PBPMN/pull/13) and [PR #14](https://github.com/snapquast73-boop/PBPMN/pull/14)
  merges, which do not touch `docs/`. Pages publishing source is `main` at `/`
  (`build_type=legacy`).
- The post-deployment [published-site check #36](https://github.com/snapquast73-boop/PBPMN/actions/runs/44831264772)
  for `04dcb02` completed successfully at 2026-11-20 22:43 UTC.

## H. Flagged irregularities (unchanged; published for review)

These remain on the live [Flagged for Review page](https://snapquast73-boop.github.io/PBPMN/docs/review.html)
and do not block the site: the import’s `2023 162 (verified via SD schedule pattern)` and
`2025 162 (est.)` explanations, the approximate subtotals, the typical play/pitch counts, the
midnight `Preview` snapshot of 2026-08-11, the contradicted Estrada single and its pitch
measurements, the `OAK`/`Dodger Stadium`/count irregularities, the unavailable original
implementation (upstream returns 404), the `745675` decisions detail, and the manifest
media-type gap. See [VERIFICATION-26c1dbb9.md](VERIFICATION-26c1dbb9.md) §E and
[VERIFICATION-a5191c3d.md](VERIFICATION-a5191c3d.md) §E for the full lists.

## I. Manual-review links

- Live site: <https://snapquast73-boop.github.io/PBPMN/> ·
  [deep link](https://snapquast73-boop.github.io/PBPMN/?date=2024-04-01&game=745675)
- [Schedule audit](https://snapquast73-boop.github.io/PBPMN/docs/audit.html) ·
  [Flagged for Review](https://snapquast73-boop.github.io/PBPMN/docs/review.html) ·
  [Methodology](https://snapquast73-boop.github.io/PBPMN/docs/methodology.html)
- [Pages publishing source](https://api.github.com/repos/snapquast73-boop/PBPMN/pages) ·
  [original upload tree](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3)

# Coordination

Shared task board for the restoration of this repository's GitHub Pages site.
Each session works on its own branch and edits only the files in its claimed
scope. `needs review` items are published on the [Flagged for Review
page](docs/review.html) and block nothing.

## Board

| Task | Status | Session | Branch | Files touched |
|---|---|---|---|---|
| Import audit, Pages restoration, first integration | done | 8f074539 | `arena/8f074539-pbpmn` | root docs, `docs/`, `mlb_pbp/`, `tests/`, `tools/`, workflows |
| Publish flagged findings | needs review | 8f074539 | same | `docs/review.html` |
| Published-site verification tool and workflow | done — adopted by 17011489 | a1fdfd4c | `arena/a1fdfd4c-pbpmn` | `tools/published_check.py`, `.github/workflows/published-site-check.yml` |
| Deployment record only (superseded by the record below) | superseded | 5d10e7d4, 3fa5105a | `arena/5d10e7d4-pbpmn`, `arena/3fa5105a-pbpmn` | `COORDINATION.md` |
| Independent verification, hardening, merge and deploy record | done | 17011489 | `arena/17011489-pbpmn` | `tools/published_check.py`, `.github/workflows/published-site-check.yml`, `README.md`, `COORDINATION.md` |

No two live claims overlap; the site's data and navigation were changed only by
the integration session that published them (PR #2).

## Record — session 8f074539 (import audit and restoration)

- **Done — import audit:** checked every imported schedule row against
  [MLB's schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-08-11&gameTypes=R,F,D,L,W),
  including all 26 club-season windows. Exact requests on the [generated
  audit](docs/audit.html); [verification
  run](https://github.com/snapquast73-boop/PBPMN/actions/runs/44827650322).
  Checked the [Giants example](https://statsapi.mlb.com/api/v1.1/game/746170/feed/live)
  and [Athletics example](https://statsapi.mlb.com/api/v1.1/game/745675/feed/live).
  No copied game or season statistics are used as application data.
- **Needs review:** the [public findings](docs/review.html) — stale snapshot,
  game ID and venue, discrepancies in season entries, unsupported aggregate
  explanations, and the contradicted sample at-bat. The original [uploaded
  tree](https://github.com/snapquast73-boop/PBPMN/tree/14c9aaf304a65ef0c8e4b25819a6eb0b829218c3)
  lacked the implementation files; exact upstream parity is unverified.
- **Done — integration:** reconstructed the documented viewer and Python entry
  point and kept the existing main/root [Pages publishing
  source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
  [PR #2](https://github.com/snapquast73-boop/PBPMN/pull/2) passed [pre-merge
  verification](https://github.com/snapquast73-boop/PBPMN/actions/runs/44828032459)
  and merged as [`680a39a`](https://github.com/snapquast73-boop/PBPMN/commit/680a39aa4e5e16ce1f5b88c025e1bf3c248b0658).
  [Pages build and deployment](https://github.com/snapquast73-boop/PBPMN/actions/runs/44828149608)
  succeeded, and a [post-merge dispatch on
  main](https://github.com/snapquast73-boop/PBPMN/actions/runs/44828227427)
  regenerated the audit with no diff, verified an official archive window, and
  passed a Chrome smoke test of the public site.

## Adopted work — session a1fdfd4c (published-site verification)

Session a1fdfd4c wrote a tool and workflow that check the URL a visitor actually
loads. That work is integrated here rather than duplicated:
`tools/published_check.py` and `.github/workflows/published-site-check.yml` are
carried over from commit
[`5d53142`](https://github.com/snapquast73-boop/PBPMN/commit/5d53142) of
`arena/a1fdfd4c-pbpmn`. Session 17011489 then extended them to compare the
published HTML pages (not only the assets) with `main`, to require an official
`statsapi.mlb.com` link on each of the 41 audit rows, and to run automatically
after every successful `github-pages` deployment. Its earlier draft of the same
scope was withdrawn instead of merged twice.

## Official-source checks (re-verified 2026-11-20 by session 17011489)

Every row below was fetched directly from MLB's own endpoint in this session; a
value that no official response supports is not restated.

| Check | Official source | Result |
|---|---|---|
| `sportId=1` is Major League Baseball | [sports/1](https://statsapi.mlb.com/api/v1/sports/1) | `id 1`, `name "Major League Baseball"`, `abbreviation "MLB"` |
| Club IDs used by the audit | [teams?sportId=1](https://statsapi.mlb.com/api/v1/teams?sportId=1&fields=teams,id,name,abbreviation,fileCode) | `137` San Francisco Giants (`SF`/`sf`); `133` Athletics (`ATH`/`ath`) — MLB returns no `oak` code today |
| `gameTypes=R,F,D,L,W` excludes Spring Training | [2026-03-01 unfiltered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01) (16 games, all `gameType S`) vs [filtered](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-03-01&gameTypes=R,F,D,L,W) (0 games) | Confirmed |
| The viewer's own schedule query works | [2024-04-01](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W&hydrate=linescore) | 14 games |
| Giants example `746170`, SF 3 @ LAD 8, Dodger Stadium | [teamId=137, 2024-04-01](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&teamId=137&gameTypes=R,F,D,L,W) | Confirmed |
| Athletics example `745675`, BOS 9 @ Oakland Athletics 0, Oakland Coliseum | [teamId=133, 2024-04-01](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&teamId=133&gameTypes=R,F,D,L,W) | Confirmed |
| Imported 2014 opener `380550`, SF 9 @ ARI 8, Chase Field | [teamId=137, 2014-03-31](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2014-03-31&teamId=137&gameTypes=R,F,D,L,W) | Confirmed |
| `2026-08-11` has 15 games; `824970` TB @ ATH; `823186` HOU @ SF | [2026-08-11](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-08-11&gameTypes=R,F,D,L,W) | Confirmed; all 15 now `Final` |
| Imported venue "Dodger Stadium" for `823917` | same response | **Irregular:** MLB returns `UNIQLO Field at Dodger Stadium`; the published audit row uses MLB's name |
| Season `totalGames` spot checks: SF 2014 = 181, SF 2026 = 123, ATH 2023 = 162, ATH 2025 = 162 | [SF 2014](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2014-01-01&endDate=2014-12-31&fields=copyright,totalGames), [SF 2026](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=137&startDate=2026-01-01&endDate=2026-08-11&fields=copyright,totalGames), [ATH 2023](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2023-01-01&endDate=2023-12-31&fields=copyright,totalGames), [ATH 2025](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameTypes=R,F,D,L,W&teamId=133&startDate=2025-01-01&endDate=2025-12-31&fields=copyright,totalGames) | All four match the published rows |
| All 41 published rows still reconcile with MLB | `python tools/audit.py` + `git diff --exit-code docs/audit.html` in [run 44829063552](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063552) | Regenerated with no diff |
| Viewer default date (today, 2026-11-20) legitimately has no games | [2026-11-20](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-11-20&gameTypes=R,F,D,L,W&fields=copyright,totalGames) | `totalGames: 0`; the page says so instead of substituting data |

### Unverified or irregular — published for review, not restated as fact

- The import's `2023 162 (verified via SD schedule pattern)`, `2025 162 (est.)`,
  subtotals `≈2,009` / `≈2,024` / `~4,033`, and "typically 65-85 plays,
  250-340 playEvents" are not established by any official response. No estimate
  replaces them on the published page.
- The import's midnight `Preview` snapshot of 2026-08-11 and its "empty feeds"
  claim cannot be checked after the fact; the audit records the current finals.
- The original implementation is unavailable:
  [`api.github.com/repos/buffedlizard55-lab/MLB-PBP`](https://api.github.com/repos/buffedlizard55-lab/MLB-PBP)
  returns HTTP 404, so appearance, file layout (`docs/js/`), formatter bytes and
  historical local logs cannot be confirmed.
- The imported Athletics identifier `OAK`/`oak` contradicts MLB's current
  `ATH`/`ath`; the published audit uses MLB's values.

## Published evidence

- Live site: <https://snapquast73-boop.github.io/PBPMN/> (Pages source `main`,
  path `/`, `build_type=legacy`; [Pages API](https://api.github.com/repos/snapquast73-boop/PBPMN/pages)).
- [Published site check, run
  44829063412](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063412)
  — PASS 5/5 against the live URL: every page 200, published bytes identical to
  `main` for all five pages and four assets, 41/41 audit rows citing
  `statsapi.mlb.com`, `Access-Control-Allow-Origin: *` from both MLB endpoints,
  and a Chrome run of `?date=2024-04-01&game=745675` with four views, search,
  per-row sources, three download formats and no page errors.
  [Readable report](https://github.com/snapquast73-boop/PBPMN/commit/dd40f17a870d193a6925b649398312b830cde54c#commitcomment-211114118).
- [Full verification, run
  44829063552](https://github.com/snapquast73-boop/PBPMN/actions/runs/44829063552)
  — offline suite, JavaScript syntax, MLB row reconciliation, official archive
  retrieval and verification, and the Chrome walkthrough, all passed.

## Merge record

Filled in after the integration pull request merges; the PR number, merge
commit, Pages build and post-deploy check are recorded here and on the
[Flagged for Review page](docs/review.html) only when they exist.

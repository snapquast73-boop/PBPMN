# Independent post-integration verification — 20 November 2026

Session: `f5839ed3`. Scope: independent verification, not a second restoration.

## Results

- Read the coordination board before claiming work; preserved the restoration owner's application scope and deployment evidence.
- Ran `python -m unittest discover -s tests -v`: all four tests passed (archive digest, event serialization, official-host restriction, local links and schedule-row citations).
- Ran `python -m compileall -q mlb_pbp`: passed.
- Ran `node --check` on all three `docs/*.js` files: passed.
- Inspected `docs/api.js` and `docs/app.js`: requests target MLB's official Stats API; response validation checks MLB attribution and requested game ID; table generation adds the feed source to each row; unavailable fields are passed through the formatter rather than replaced by estimated statistics.
- Inspected `docs/review.html`: it explicitly identifies unsupported imported assertions and the unavailable original implementation. Exact upstream appearance and behavior remain **unverified**, not certified identical.

## Official evidence and manual-review links

- [Live site](https://snapquast73-boop.github.io/PBPMN/).
- [Source-linked schedule audit](https://snapquast73-boop.github.io/PBPMN/docs/audit.html).
- [Flagged for Review](https://snapquast73-boop.github.io/PBPMN/docs/review.html).
- [Official MLB example schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W).
- [Official MLB example feed](https://statsapi.mlb.com/api/v1.1/game/745675/feed/live).
- [GitHub verification run against the public deployment](https://github.com/snapquast73-boop/PBPMN/actions/runs/44828230014): independently queried through GitHub's API; overall conclusion and every verification step were successful, including MLB reconciliation, real archive retrieval, Chrome interactions and public-site smoke test.
- [Original restoration PR #2](https://github.com/snapquast73-boop/PBPMN/pull/2).
- [GitHub's Pages publishing-source documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Verification boundaries

The local tests validate implementation invariants, not the truth of every historical statistic. The GitHub-hosted workflow performs real MLB requests and regenerates the published audit; its results are distinct from the local offline checks. This sandbox's network allowlist does not permit direct requests to MLB or the public Pages hostname, so those network checks run on GitHub-hosted runners. No unsupported claim of direct local network verification is made.

No new functional defect was established by this review. Existing unverified import claims remain published on the site's clearly labeled review page. No application file or data value was changed by this session.

# MLB Plaintext Play-by-Play

**[Open the archive](https://snapquast73-boop.github.io/PBPMN/)** · [Methodology](docs/methodology.html) · [Verified schedule audit](docs/audit.html) · [Flagged for Review](docs/review.html)

Browse MLB regular-season and postseason schedules from 2014 onward. Select a game to inspect the line score, decisions, plays, pitch/action details, runner movements and batting/pitching box scores. Search by a player or description. Download the readable text, exact MLB JSON, or event-oriented NDJSON. While watching a live game, observations are saved on this browser only.

The static viewer talks directly to [MLB’s schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W) and [game feed](https://statsapi.mlb.com/api/v1.1/game/745675/feed/live). No backend, key, sample scores or fallback dataset. See [an example deep link](https://snapquast73-boop.github.io/PBPMN/?date=2024-04-01&game=745675). GitHub Pages serves `main` at `/`, with `.nojekyll` and a query-preserving redirect to `docs/`.

## Run locally

```sh
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000/`. HTTPS or localhost is required for Web Crypto. Network access to MLB is required to load schedules and games.

## Archive CLI (Python 3.11+; standard library)

```sh
python -m mlb_pbp game 745675 --format text --output game.txt
python -m mlb_pbp game 745675 --format raw --output game.json
python -m mlb_pbp game 745675 --format events --output game.ndjson
python -m mlb_pbp archive --start 2024-04-01 --end 2024-04-01 --output archive --formats text,raw,events --workers 2 --request-delay 0.2
python -m mlb_pbp verify archive
```

Omit the dates to archive from 2014-01-01 through today. Schedules are saved by month under `schedules/`. Outputs under `games/`, `raw/` and `events/` are grouped by official date. Raw JSON is compressed unless `--raw-uncompressed` is specified. Manifests retain the MLB notice, URL, UTC retrieval time, and SHA-256 digests. Resume checks existing files. Use `--refresh` to retrieve corrections; verification uses the latest manifest entry for each game or schedule window. Failures go to `errors.ndjson`. Large data archives stay out of Git.

## Maintenance
The optional [season-release workflow template](automation/github-actions/archive.yml) is kept outside active workflows so that publishing the viewer does not start bulk downloads. No season release assets are required by the site.

`python tools/audit.py` regenerates the historical snapshot from MLB. `python tools/published_check.py` verifies the deployment itself: HTTP status and content type of every published page and asset, byte-for-byte parity with `main`, one `statsapi.mlb.com` source link on each of the 41 audit rows, `Access-Control-Allow-Origin` from MLB for the Pages origin, and a Chrome run of the live URL. The [published-site workflow](.github/workflows/published-site-check.yml) runs it after every successful `github-pages` deployment, daily, and on demand, and posts the report as a commit comment. `python -m unittest discover -s tests` checks the site and archive offline. The [verification workflow](.github/workflows/audit.yml) also exercises real MLB requests. See [coordination and deployment evidence](COORDINATION.md).

This independent project is not affiliated with MLB. The [MIT license](LICENSE) covers software only, not MLB data. The original upload lacked the implementation; the review page documents what cannot be confirmed about it.

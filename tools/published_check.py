"""Verify the published GitHub Pages deployment, end to end.

Unlike ``tools/browser_check.py`` (which serves the working tree), this checks the
*site a visitor actually loads*: ``https://snapquast73-boop.github.io/PBPMN/``.

Checks, in order:

1. the root URL still redirects into ``docs/`` and carries the query string;
2. every published page and asset returns 200 with the expected content type;
3. published bytes match ``origin/main`` byte for byte (proves Pages is serving
   the merged commit, not a stale or partial build);
4. MLB's endpoints return ``Access-Control-Allow-Origin`` for the Pages origin, so
   the browser-side fetch in ``docs/api.js`` can work at all;
5. optionally, a real Chrome run of the published site (deep link, tabs, search,
   source links, downloads) via ``tools/browser_check.py``.

Usage::

    python tools/published_check.py                      # full report to stdout
    python tools/published_check.py --report out.md      # also write markdown
    python tools/published_check.py --skip-browser       # HTTP checks only

Exit status is 0 only when every executed check passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_BASE = "https://snapquast73-boop.github.io/PBPMN/"
PAGES_ORIGIN = "https://snapquast73-boop.github.io"
REPO_ROOT = Path(__file__).resolve().parent.parent

PAGES = ["", "docs/", "docs/index.html", "docs/methodology.html", "docs/audit.html", "docs/review.html"]
ASSETS = ["docs/style.css", "docs/api.js", "docs/app.js", "docs/format.js"]

MLB_SCHEDULE = (
    "https://statsapi.mlb.com/api/v1/schedule?"
    "sportId=1&date=2024-04-01&gameTypes=R,F,D,L,W&hydrate=linescore"
)
MLB_FEED = "https://statsapi.mlb.com/api/v1.1/game/745675/feed/live"

USER_AGENT = "pbpmn-published-check/1.0 (+https://github.com/snapquast73-boop/PBPMN)"


class Result:
    def __init__(self, name: str):
        self.name = name
        self.rows: list[tuple[bool, str]] = []

    def add(self, ok: bool, detail: str) -> None:
        self.rows.append((bool(ok), detail))

    @property
    def ok(self) -> bool:
        return all(ok for ok, _ in self.rows) and bool(self.rows)

    def markdown(self) -> str:
        lines = [f"### {'PASS' if self.ok else 'FAIL'} — {self.name}", ""]
        for ok, detail in self.rows:
            lines.append(f"- {'✅' if ok else '❌'} {detail}")
        return "\n".join(lines)


def http_get(url: str, origin: str | None = None) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    if origin:
        request.add_header("Origin", origin)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in error.headers.items()}, error.read()
    except (urllib.error.URLError, OSError) as error:
        # Unreachable host, TLS failure or timeout: report it, never crash.
        return 0, {}, str(error).encode("utf-8")


def git_blob(path: str) -> bytes | None:
    try:
        return subprocess.run(
            ["git", "show", f"origin/main:{path}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def check_pages(base: str) -> Result:
    result = Result("Published pages")
    for path in PAGES:
        url = base + path
        status, headers, body = http_get(url)
        ctype = headers.get("content-type", "?")
        result.add(status == 200 and "html" in ctype, f"`{url}` → {status} ({ctype}, {len(body)} bytes)")
        if path == "":
            html = body.decode("utf-8", "replace")
            result.add("location.replace" in html and "./docs/" in html, "root page redirects into `docs/`")
            result.add("location.search" in html, "root redirect preserves the query string (deep links survive)")
        if path in ("docs/", "docs/index.html"):
            html = body.decode("utf-8", "replace")
            for needle, label in (
                ('id="date"', "schedule date input present"),
                ('id="games"', "schedule container present"),
                ('id="game"', "game section present"),
                ('id="content"', "game content container present"),
                ('src="app.js"', "viewer module referenced"),
                ('href="style.css"', "stylesheet referenced"),
                ("review.html", "Flagged for Review linked"),
            ):
                result.add(needle in html, label)
    return result


def check_assets(base: str) -> Result:
    result = Result("Assets match main byte for byte")
    for path in ASSETS:
        url = base + path
        status, headers, body = http_get(url)
        published = hashlib.sha256(body).hexdigest()
        expected_bytes = git_blob(path)
        if expected_bytes is None:
            result.add(status == 200, f"`{path}` → {status} (no `origin/main` copy to compare)")
            continue
        expected = hashlib.sha256(expected_bytes).hexdigest()
        result.add(
            status == 200 and published == expected,
            f"`{path}` → {status}; sha256 published `{published[:16]}…` vs origin/main `{expected[:16]}…`",
        )
    return result


def check_cors() -> Result:
    result = Result("MLB allows the Pages origin (browser fetch path)")
    for url in (MLB_SCHEDULE, MLB_FEED):
        status, headers, body = http_get(url, origin=PAGES_ORIGIN)
        allow = headers.get("access-control-allow-origin", "")
        result.add(status == 200, f"`{url.split('?')[0]}` → HTTP {status}")
        result.add(
            allow in ("*", PAGES_ORIGIN),
            f"`Access-Control-Allow-Origin: {allow or 'absent'}`",
        )
        try:
            payload = json.loads(body)
            notice = payload.get("copyright", "")
            result.add("MLB Advanced Media" in notice, f"notice present: `{notice[:60]}…`")
            if "schedule" in url:
                games = sum(len(day.get("games", [])) for day in payload.get("dates", []))
                result.add(games > 0, f"schedule for 2024-04-01 returned {games} games (the site's own query)")
            else:
                result.add(payload.get("gamePk") == 745675, f"feed echoes gamePk {payload.get('gamePk')}")
        except json.JSONDecodeError:
            result.add(False, "body was not JSON")
    return result


def check_browser(base: str) -> Result:
    result = Result("Live browser run of the published site (Chrome)")
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from tools.browser_check import check  # noqa: PLC0415 - optional dependency path
    except Exception as error:  # pragma: no cover - environment dependent
        result.add(False, f"could not import tools/browser_check.py: {error}")
        return result
    try:
        check(base)
    except AssertionError as error:
        result.add(False, f"assertion failed: {error}")
    except Exception as error:  # pragma: no cover - environment dependent
        result.add(False, f"browser run raised {type(error).__name__}: {error}")
        traceback.print_exc()
    else:
        result.add(
            True,
            "deep link `?date=2024-04-01&game=745675` rendered MLB's away/home names, all four tabs "
            "opened, search narrowed the play list, every table row linked its official source, and "
            "the three downloads returned the exact feed bytes/digests, with no page errors",
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base", nargs="?", default=DEFAULT_BASE, help=f"site root (default: {DEFAULT_BASE})")
    parser.add_argument("--report", help="write a markdown report to this path")
    parser.add_argument("--skip-browser", action="store_true", help="skip the Chrome run")
    args = parser.parse_args(argv)

    base = args.base if args.base.endswith("/") else args.base + "/"
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    sections = [check_pages(base), check_assets(base), check_cors()]
    if not args.skip_browser:
        sections.append(check_browser(base))

    failures = [section for section in sections if not section.ok]
    report = [
        "## Published-site verification",
        "",
        f"- Site: {base}",
        f"- Run (UTC): {started}",
        f"- Result: **{'PASS' if not failures else 'FAIL'}** "
        f"({len(sections) - len(failures)}/{len(sections)} sections passed)",
        "",
    ]
    report.extend(section.markdown() + "\n" for section in sections)
    text = "\n".join(report)
    print(text)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

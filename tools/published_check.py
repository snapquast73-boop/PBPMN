"""Verify the published GitHub Pages deployment of this repository.

Checks, against the real site over HTTPS:

1. every published file is served byte-for-byte as committed here;
2. every internal link on every published page returns HTTP 200;
3. the schedule audit still carries one official MLB source link per row;
4. the viewer loads the official schedule and game feed in Chrome, switches
   views, searches, and downloads text, raw JSON and NDJSON (unless
   ``--http-only`` is given).

Standard library only, except that the browser phase imports
``tools/browser_check.py`` (Playwright). Run from the repository root.
"""
import argparse
import hashlib
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_URL = 'https://snapquast73-boop.github.io/PBPMN/'
PUBLISHED = [
    ('index.html', 'index.html'),
    ('docs/index.html', 'docs/'),
    ('docs/methodology.html', 'docs/methodology.html'),
    ('docs/audit.html', 'docs/audit.html'),
    ('docs/review.html', 'docs/review.html'),
    ('docs/style.css', 'docs/style.css'),
    ('docs/app.js', 'docs/app.js'),
    ('docs/api.js', 'docs/api.js'),
    ('docs/format.js', 'docs/format.js'),
]
AUDIT_ROWS = 41
AUDIT_HOST = 'statsapi.mlb.com'


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'pbpmn-published-check/1.0 '
            '(+https://github.com/snapquast73-boop/PBPMN)'
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.status, response.read()


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.status = [], None
        self.rows, self.row = [], None

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        for key in ('href', 'src'):
            if key in data:
                self.links.append(data[key])
        if tag == 'td' and self.row is None:
            self.row = []
        if tag == 'a' and self.row is not None:
            self.row.append(data.get('href', ''))

    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def digest(body):
    return hashlib.sha256(body).hexdigest()[:16]


def published_files(base, report):
    """Published bytes must equal the committed bytes, page by page."""
    for local, path in PUBLISHED:
        url = urljoin(base, path)
        status, body = fetch(url)
        assert status == 200, f'{url}: HTTP {status}'
        expected = (ROOT / local).read_bytes()
        if body != expected:
            raise AssertionError(
                f'{url}: published bytes differ from {local} '
                f'({len(body)} vs {len(expected)} bytes); the deployment is '
                'stale or the file was modified in transit'
            )
        report.append(f'file  200  {url}  sha256 {digest(body)}  = {local}')


def internal_links(base, report):
    """Every same-origin link on every published page must resolve."""
    seen = set()
    for _, path in PUBLISHED[:5]:
        url = urljoin(base, path)
        _, body = fetch(url)
        page = Page()
        page.feed(body.decode())
        for link in page.links:
            split = urlsplit(link)
            if split.scheme or link.startswith(('#', 'mailto:', 'javascript:')):
                continue
            target = urljoin(url, link)
            if not target.startswith(base) or target in seen:
                continue
            seen.add(target)
            status, _ = fetch(target)
            assert status == 200, f'{url} -> {link}: HTTP {status}'
            report.append(f'link  200  {target}')
    assert seen, 'no internal links found'


def audit_rows(base, report):
    """Each published audit row must cite an official MLB response."""
    url = urljoin(base, 'docs/audit.html')
    _, body = fetch(url)
    page = Page()
    page.feed(body.decode())
    assert len(page.rows) == AUDIT_ROWS, (
        f'{url}: {len(page.rows)} rows, expected {AUDIT_ROWS}'
    )
    for index, row in enumerate(page.rows, 1):
        assert any(urlsplit(href).netloc == AUDIT_HOST for href in row), (
            f'{url}: row {index} has no official MLB source link'
        )
    report.append(f'rows  200  {url}  {len(page.rows)} rows, each citing '
                  f'{AUDIT_HOST}')


def browser(base, report):
    sys.path.insert(0, str(ROOT / 'tools'))
    from browser_check import check

    check(base)
    report.append('chrome ok  schedule, deep link, four views, search, '
                  'source links, plain text / raw JSON / NDJSON downloads')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--url', default=DEFAULT_URL, help='published site URL')
    parser.add_argument('--http-only', action='store_true',
                        help='skip the Chrome phase')
    args = parser.parse_args()
    base = args.url if args.url.endswith('/') else args.url + '/'
    report = [f'published site: {base}']
    try:
        published_files(base, report)
        internal_links(base, report)
        audit_rows(base, report)
        if not args.http_only:
            browser(base, report)
    except (AssertionError, urllib.error.URLError, OSError) as exc:
        print('\n'.join(report))
        print(f'::error::published check failed: {exc}', flush=True)
        raise SystemExit(1)
    print('\n'.join(report))
    print(f'published check passed: {len(report) - 1} assertions')


if __name__ == '__main__':
    main()

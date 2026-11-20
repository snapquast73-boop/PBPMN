"""Browser smoke test against an actual Pages-style path and actual MLB responses."""
import hashlib
import json
import sys
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


@contextmanager
def project_site():
    if len(sys.argv) > 1:
        yield sys.argv[1]
        return
    root = Path.cwd()
    server = ThreadingHTTPServer(('localhost', 0), partial(SimpleHTTPRequestHandler, directory=str(root.parent)))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f'http://localhost:{server.server_port}/{root.name}/'
    finally:
        server.shutdown()
        server.server_close()


def check(base):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome')
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        page.on('requestfailed', lambda request: errors.append(f'{request.url}: {request.failure}'))
        page.set_default_timeout(60000)
        with page.expect_response(lambda r: '/745675/feed/live' in r.url) as feed:
            page.goto(base+'?date=2024-04-01&game=745675')
        raw = feed.value.body()
        data = json.loads(raw)
        page.locator('#controls').wait_for()
        assert page.locator('#match').inner_text() == ' at '.join(data['gameData']['teams'][s]['name'] for s in ('away','home'))
        assert page.locator('#games a').count() > 0
        # The original README documents docs/js/ as the module location: prove
        # the browser really loaded the viewer modules from there.
        loaded = page.evaluate("performance.getEntriesByType('resource').map(e => e.name)")
        for module in ('api', 'app', 'eventlog', 'format'):
            assert any(url.endswith(f'/docs/js/{module}.js') for url in loaded), module
        for tab in ('Plays','Box score','Event log','Overview'):
            page.get_by_role('button', name=tab, exact=True).click()
            if tab == 'Event log':
                assert 'Observations made while this browser was watching' in page.locator('#content').inner_text()
            if tab == 'Plays':
                plays = data['liveData']['plays']['allPlays']
                assert page.locator('details').count() == len(plays)
                page.locator('#search').fill(plays[0]['matchup']['batter']['fullName'])
                assert 0 < page.locator('details').count() < len(plays)
            for tr in page.locator('#content tbody tr').all():
                assert tr.locator('a').get_attribute('href') == feed.value.url
        for label in ('Plain text','Raw JSON','Event NDJSON'):
            with page.expect_download() as event:
                page.get_by_role('button',name=label).click()
            result = event.value.path().read_bytes()
            if label == 'Raw JSON':
                assert result == raw
            else:
                assert hashlib.sha256(raw).hexdigest().encode() in result
        for name in ('review.html','audit.html','methodology.html'):
            assert page.goto(urljoin(base, 'docs/'+name)).ok
        assert not errors, errors
        browser.close()


if __name__ == '__main__':
    with project_site() as base:
        try:
            check(base)
        except Exception as exc:
            print(f'::error::{str(exc).splitlines()[0]}',flush=True)
            raise

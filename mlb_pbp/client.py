"""Fetch only MLB HTTPS JSON, without following redirects."""
import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener

BASE = 'https://statsapi.mlb.com'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def schedule_url(start, end):
    return BASE + '/api/v1/schedule?' + urlencode(dict(sportId=1, startDate=start, endDate=end,
                                                        gameTypes='R,F,D,L,W', hydrate='linescore'), safe=',')


def feed_url(game):
    return f'{BASE}/api/v1.1/game/{int(game)}/feed/live'


class Client:
    def __init__(self, delay=0.2):
        self.delay = delay
        self.lock = threading.Lock()
        self.last = 0

    def get(self, url, game=None):
        parts = urlsplit(url)
        if (parts.scheme, parts.netloc) != ('https', 'statsapi.mlb.com'):
            raise ValueError('Not an MLB HTTPS source')
        for attempt in range(3):
            with self.lock:
                time.sleep(max(0, self.delay - (time.monotonic() - self.last)))
                self.last = time.monotonic()
            try:
                with build_opener(NoRedirect()).open(url, timeout=60) as response:
                    body = response.read()
                break
            except (URLError, TimeoutError) as exc:
                if attempt == 2 or isinstance(exc, HTTPError) and exc.code < 500 and exc.code != 429:
                    raise
                time.sleep(2 ** attempt)
        data = json.loads(body)
        if 'MLB Advanced Media' not in data.get('copyright', '') or game is not None and data.get('gamePk') != game:
            raise ValueError('Unverified notice or mismatched game ID')
        meta = dict(sourceUrl=url, fetchedAt=datetime.now(timezone.utc).isoformat(),
                    sha256=hashlib.sha256(body).hexdigest(), copyright=data['copyright'])
        return body, data, meta

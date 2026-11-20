import calendar
import gzip
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

from .client import Client, feed_url, schedule_url
from .formatter import render


def append(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record) + '\n')


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def save(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_bytes(content)
    temp.replace(path)
    return dict(path=name, sha256=hashlib.sha256(content).hexdigest())


def latest(rows, key):
    return {row[key]: row for row in rows}


def verified(root, row):
    for kind, file in row['files'].items():
        path = (root / file['path']).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            return False
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != file['sha256']:
            return False
        if kind == 'raw':
            raw = gzip.decompress(body) if path.suffix == '.gz' else body
            if hashlib.sha256(raw).hexdigest() != row['sha256']:
                return False
    return True


def verify(root):
    count = 0
    for path, key in [('schedules/manifest.ndjson', 'sourceUrl'), ('manifest.ndjson', 'gamePk')]:
        for row in latest(read(root / path), key).values():
            if not verified(root, row):
                raise ValueError(f"Missing or corrupt file for {row[key]}")
            count += 1
    if not count:
        raise ValueError('No archive manifests found')
    print(f'Checked {count} current manifest records')


def archive(args):
    root, start = args.output, args.start
    client = Client(args.request_delay)
    manifest = root / 'manifest.ndjson'
    previous = latest(read(manifest), 'gamePk')
    ids = set()
    while start <= args.end:
        end = min(args.end, start.replace(day=calendar.monthrange(start.year, start.month)[1]))
        body, schedule, meta = client.get(schedule_url(start, end))
        file = save(root, f'schedules/{start}_{end}.json.gz', gzip.compress(body, mtime=0))
        append(root/'schedules/manifest.ndjson', dict(**meta, files={'raw': file}))
        ids.update(g['gamePk'] for d in schedule['dates'] for g in d['games'] if g.get('gameType') in ('R','F','D','L','W'))
        start = end + timedelta(days=1)

    def fetch(game):
        try:
            body, data, meta = client.get(feed_url(game), game)
            gd = data['gameData']
            from datetime import date
            day = date.fromisoformat(gd['datetime']['officialDate']).strftime('%Y/%m/%d')
            files = {}
            for kind in args.formats:
                folder, ext = {'raw': ('raw','json'), 'text': ('games','txt'), 'events': ('events','ndjson')}[kind]
                content = render(kind, body, data, meta)
                if kind == 'raw' and not args.raw_uncompressed:
                    content, ext = gzip.compress(content, mtime=0), 'json.gz'
                files[kind] = save(root, f'{folder}/{day}/{game}.{ext}', content)
            return dict(gamePk=game, **meta, files=files, officialDate=gd['datetime']['officialDate'],
                        teams=gd.get('teams'), status=gd.get('status'), season=gd.get('game',{}).get('season'),
                        gameType=gd.get('game',{}).get('type'))
        except Exception as exc:
            return dict(gamePk=game, sourceUrl=feed_url(game), error=str(exc))

    def reusable(game):
        row = previous.get(game)
        return (not args.refresh and row and set(args.formats) <= row['files'].keys() and verified(root, row)
                and ('raw' not in args.formats or row['files']['raw']['path'].endswith('.json') == args.raw_uncompressed))
    failed = False
    with ThreadPoolExecutor(args.workers) as pool:
        for row in pool.map(fetch, sorted(g for g in ids if not reusable(g))):
            if 'error' in row:
                failed = True
                append(root/'errors.ndjson', row)
            else:
                append(manifest, row)
    if failed:
        raise ValueError('Some games failed; see errors.ndjson')

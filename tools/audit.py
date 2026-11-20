"""Regenerate the public snapshot directly from MLB (standard library only)."""
import datetime as dt
import html
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo

BASE = 'https://statsapi.mlb.com/api/v1/schedule?'
DAY = '2026-08-11'


def schedule(**params):
    url = BASE + urlencode(dict(sportId=1, gameTypes='R,F,D,L,W', **params), safe=',')
    for attempt in range(3):
        try:
            with urlopen(url, timeout=40) as r:
                assert r.url == url
                data = json.load(r)
            assert 'MLB Advanced Media' in data['copyright']
            return url, data
        except Exception as exc:
            if attempt == 2:
                print(f"::error::{url}: {type(exc).__name__}: {exc}", flush=True)
                raise
            time.sleep(2 ** attempt)


def row(values, url):
    return '<tr>' + ''.join('<td>' + html.escape(str(v if v is not None else '')) + '</td>' for v in values) + '<td><a href="' + html.escape(url) + '">MLB schedule</a></td></tr>\n'


def games(data):
    return [g for d in data['dates'] for g in d['games']]


def table(headers):
    return '<div class="scroll"><table><thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers.split('|')) + '<th>Source</th></tr></thead><tbody>\n'


def render():
    lines = [table('Time (Eastern)|Game ID|Away|Home|Venue|Current status')]
    url, data = schedule(date=DAY)
    for g in games(data):
        timestamp = g.get('gameDate')
        eastern = dt.datetime.fromisoformat(timestamp).astimezone(ZoneInfo('America/New_York')).strftime('%H:%M') if timestamp else None
        lines.append(row([eastern, g.get('gamePk'), g['teams']['away']['team'].get('name'), g['teams']['home']['team'].get('name'), g['venue'].get('name'), g['status'].get('detailedState')], url))
    lines += ['</tbody></table></div><h2>Schedule entries by team and season</h2><p>These are MLB’s totalGames, not a count of wins, completed games or available feeds. The last window ends August 11, 2026. First and last dates are schedule dates.</p>', table('Team ID|Season|Schedule entries|First listed game|Last listed game')]
    for team in (137, 133):
        for year in range(2014, 2027):
            url, data = schedule(teamId=team, startDate=f'{year}-01-01', endDate=min(DAY, f'{year}-12-31'), fields='copyright,totalGames,dates,date,games,gamePk,officialDate,status,detailedState,teams,away,home,team,name,score,venue')
            entries = games(data)
            def describe(g):
                sides = [g['teams'][side] for side in ('away', 'home')]
                return ' · '.join(str(v) for v in [g.get('officialDate'), g.get('gamePk'),
                    *(' '.join(str(v) for v in (s['team'].get('name'), s.get('score')) if v is not None) for s in sides),
                    g.get('venue', {}).get('name'), g.get('status', {}).get('detailedState')] if v is not None)
            lines.append(row([team, year, data.get('totalGames'), describe(entries[0]) if entries else None,
                              describe(entries[-1]) if entries else None], url))
    return ''.join(lines) + '</tbody></table></div>'


if __name__ == '__main__':
    p = Path('tools/audit-template.html').read_text()
    Path('docs/audit.html').write_text(p.replace('<!--DATA-->', render()))

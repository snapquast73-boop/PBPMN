import json


def render(kind, body, data, meta):
    if kind == 'raw':
        return body
    live = data.get('liveData', {})
    plays = live.get('plays', {}).get('allPlays', [])
    game = data.get('gameData', {})
    if kind == 'events':
        rows = [dict(recordType='metadata', gamePk=data['gamePk'], gameData=game, **meta)]
        for play in plays:
            rows.append(dict(recordType='play', **{k: v for k, v in play.items() if k != 'playEvents'}))
            for event in play.get('playEvents', []):
                rows.append(dict(recordType='event', atBatIndex=play.get('about', {}).get('atBatIndex'), event=event))
        lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    else:
        def pretty(obj):
            return json.dumps(obj, ensure_ascii=False, indent=2) if obj is not None else ''
        lines = ['MLB PLAINTEXT PLAY-BY-PLAY', 'PROVENANCE', pretty(meta), 'GAME', str(data['gamePk']),
                 pretty(game.get('teams')), pretty(game.get('datetime')), pretty(game.get('status')),
                 'LINE SCORE', pretty(live.get('linescore')), 'DECISIONS', pretty(live.get('decisions')), 'PLAY-BY-PLAY']
        for play in plays:
            lines.extend([play.get('result', {}).get('description', ''), pretty(play)])
        lines.extend(['BOX SCORE', pretty(live.get('boxscore'))])
    return ('\n'.join(lines) + '\n').encode()

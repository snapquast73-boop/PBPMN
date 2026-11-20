export const plays = f => f.liveData?.plays?.allPlays ?? [];
export const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const provenance = r => ({gamePk:r.data.gamePk,sourceUrl:r.url,retrieved:r.retrieved,sha256:r.sha256,copyright:r.data.copyright});
export function records(r) {
  const rows = [{recordType:'metadata',...provenance(r),gameData:r.data.gameData}];
  for (const {playEvents,...play} of plays(r.data)) {
    rows.push({recordType:'play',...play});
    for (const event of playEvents ?? []) rows.push({recordType:'event',atBatIndex:play.about?.atBatIndex,event});
  }
  return rows.map(x=>JSON.stringify(x)).join('\n')+'\n';
}
export const pretty = v => JSON.stringify(v,null,2) ?? '';
export function text(r) {
  const f=r.data, live=f.liveData ?? {};
  return ['MLB PLAINTEXT PLAY-BY-PLAY',pretty(provenance(r)), 'GAME', [f.gameData?.teams?.away?.name,f.gameData?.teams?.home?.name].join(' at '),f.gameData?.datetime?.officialDate,f.gameData?.status?.detailedState,'LINE SCORE',pretty(live.linescore),'DECISIONS',pretty(live.decisions),'PLAY-BY-PLAY',...plays(f).map(p=>[p.about?.halfInning,p.about?.inning,p.result?.description,pretty(p.matchup),pretty(p.count),pretty(p.playEvents),pretty(p.runners)].join('\n')),'BOX SCORE',pretty(live.boxscore)].join('\n')+'\n';
}

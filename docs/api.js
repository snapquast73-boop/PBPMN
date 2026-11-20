export const base = 'https://statsapi.mlb.com';
export const scheduleURL = date => `${base}/api/v1/schedule?` + new URLSearchParams({sportId:1,date,gameTypes:'R,F,D,L,W',hydrate:'linescore'});
export const feedURL = id => `${base}/api/v1.1/game/${id}/feed/live`;
export async function official(url, signal, id) {
  if (new URL(url).origin !== base) throw Error('Not an official MLB URL');
  const r = await fetch(url,{signal,redirect:'error',cache:'no-store'});
  if (!r.ok) throw Error(`MLB returned HTTP ${r.status}`);
  const bytes = await r.arrayBuffer();
  const data = JSON.parse(new TextDecoder().decode(bytes));
  if (!data.copyright?.includes('MLB Advanced Media') || (id != null && String(data.gamePk) !== String(id))) throw Error('MLB provenance or game ID could not be validated');
  const hash = await crypto.subtle.digest('SHA-256',bytes);
  return {data,bytes,url,retrieved:new Date().toISOString(),sha256:Array.from(new Uint8Array(hash),n=>n.toString(16).padStart(2,'0')).join('')};
}

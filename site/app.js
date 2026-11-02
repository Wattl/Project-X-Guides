'use strict';
const el = id => document.getElementById(id);
const fmt = text => new Intl.DateTimeFormat('de-DE', {day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'Europe/Berlin',timeZoneName:'short'}).format(new Date(text));
let current = null;
function paragraph(text, klass='') { const p=document.createElement('p'); p.textContent=text; p.className=klass; return p; }
function render(state) {
  current = state;
  const age = Date.now() - Date.parse(state.checked_at);
  const fresh = state.source_status === 'ok' && Number.isFinite(age) && age >= -300000 && age <= 8*3600*1000;
  el('dcs-build').textContent = state.dcs_build || 'Unbekannt';
  el('checked-at').textContent = state.checked_at ? fmt(state.checked_at) : 'Nicht verfügbar';
  el('downloads').replaceChildren();
  el('preparation').replaceChildren();
  const guides = fresh ? state.guides : [];
  el('guide-count').textContent = String(guides.length);
  el('notice').hidden = guides.length > 0;
  el('notice').textContent = !fresh
    ? 'Die DCS-Version konnte nicht aktuell bestätigt werden. Downloads sind vorübergehend ausgeblendet. Bitte später erneut laden.'
    : 'Für DCS ' + state.dcs_build + ' ist derzeit noch kein Guide vollständig geprüft und freigegeben. Die geplanten Ausgaben stehen unten.';
  for (const g of guides) {
    const card=document.createElement('article'); card.className='card';
    const title=document.createElement('h3'); title.textContent=g.title; card.append(title);
    card.append(paragraph(g.module+' · Ausgabe '+g.version, 'fine'));
    card.append(paragraph('DCS '+state.dcs_build+' · praktisch geprüft am '+g.tested_at.slice(0,10)));
    const row=document.createElement('div'); row.className='downloads';
    for (const a of g.artifacts) {
      const link=document.createElement('a'); link.className='button'; link.textContent=a.label+' · PDF';
      link.href=a.download; link.download=a.filename; row.append(link);
    }
    card.append(row); el('downloads').append(card);
  }
  for (const draft of state.in_preparation || []) {
    const box=document.createElement('article'); box.className='draft'; const title=document.createElement('strong');
    title.textContent=draft.title+' · Entwurf '+draft.version; box.append(title,paragraph(draft.status)); el('preparation').append(box);
  }
}
async function refresh() {
  try { const response=await fetch('status.json?t='+Date.now(), {cache:'no-store'}); if(!response.ok) throw Error('status'); render(await response.json()); }
  catch (_) { current=null; el('downloads').replaceChildren(); el('guide-count').textContent='0'; el('notice').hidden=false; el('notice').textContent='Der Veröffentlichungsstand ist gerade nicht erreichbar. Bitte die Seite später erneut laden.'; }
}
refresh();
setInterval(() => { if(current) render(current); }, 60000);
setInterval(refresh, 300000);

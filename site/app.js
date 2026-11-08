'use strict';
const $ = id => document.getElementById(id);
let records = [];
const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date = value => /^\d{4}-\d{2}-\d{2}$/.test(value || '') ? value : 'Unknown';
const number = (value, suffix) => Number.isFinite(value) ? `${new Intl.NumberFormat('en-GB').format(value)} ${suffix}` : 'Unconfirmed';
function render(){
  const status = $('status').value, city = $('city').value;
  const filtered = records.filter(r => (status === 'all' || (status === 'current' ? r.status === 'candidate' : r.status === 'archived')) && (city === 'all' || r.city === city));
  $('count').textContent = `${filtered.length} ${filtered.length === 1 ? 'record' : 'records'}`;
  $('state').hidden = filtered.length > 0;
  $('state').textContent = records.length ? 'No records match these filters. Try another status or city.' : 'No verified listings yet. This is not evidence that no suitable homes exist. The daily scan is limited and may find nothing.';
  $('cards').replaceChildren();
  for(const r of filtered){
    if(!(/^(https:\/\/www\.ohne-makler\.net\/immobilie\/\d+\/|https:\/\/immobilien\.sparkasse\.de\/expose\/FID-F14-[\d-]+\.html)$/.test(r.url))) continue;
    const card = document.createElement('article'); card.className = `card ${r.status === 'archived' ? 'archived' : ''}`;
    card.innerHTML = `<div class="card-top"><span>${safe(r.city)}</span><span class="status">${r.status === 'archived' ? 'Archived' : 'To verify'}</span></div><h3>${safe(r.city)} · ${safe(r.district || 'Area unconfirmed')}</h3><p class="type">${safe(r.property_type || 'House type unconfirmed')}</p><div class="facts"><div><small>Asking price</small>${safe(number(r.price_eur, '€'))}</div><div><small>Living area</small>${safe(number(r.living_area_m2, 'm²'))}</div><div><small>Plot, not garden</small>${safe(number(r.plot_area_m2, 'm²'))}</div></div><p class="caution">Usable garden and cycling time to an S1 station: not verified.</p><div class="card-foot"><a href="${safe(r.url)}" target="_blank" rel="noopener noreferrer">View original listing ↗</a><small>Last seen ${safe(date(r.last_seen))}<br>Source: ${safe(r.source)}</small></div>`;
    $('cards').append(card);
  }
}
async function init(){
  try{
    const response = await fetch('./data/listings.json', {cache:'no-store'});
    if(!response.ok) throw new Error('Data unavailable');
    const data = await response.json();
    if(!Array.isArray(data.listings)) throw new Error('Invalid data');
    records = data.listings;
    const cities = [...new Set(records.map(r => r.city).filter(Boolean))].sort((a,b)=>a.localeCompare(b));
    for(const city of cities){ const option = document.createElement('option');option.value = city;option.textContent = city;$('city').append(option); }
    if(data.updated_at) $('updated').textContent = `Scan ${date(data.updated_at)}`;
    render();
  }catch(_){ $('state').textContent = 'Data unavailable right now. No listing status can be confirmed. Please try again later.';$('count').textContent = 'Unavailable'; }
}
$('status').addEventListener('change',render);$('city').addEventListener('change',render);init();

'use strict';
const $ = id => document.getElementById(id);
const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const allowedUrl = url => typeof url === 'string' && /^(https:\/\/www\.ohne-makler\.net\/immobilie\/\d+\/|https:\/\/immobilien\.sparkasse\.de\/expose\/FID-F14-[\d-]+\.html)$/.test(url);
const date = value => {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return 'date non indiquée';
  const parsed = new Date(`${value}T12:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value
    ? new Intl.DateTimeFormat('fr-FR', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'}).format(parsed)
    : 'date non indiquée';
};
const number = (value, unit) => typeof value === 'number' && Number.isFinite(value) && value >= 0
  ? `${new Intl.NumberFormat('fr-FR', {maximumFractionDigits:1}).format(value)} ${unit}` : 'Non indiqué';
const types = {'Einfamilienhaus':'Maison individuelle', 'Reihenendhaus':'Maison de bout de rangée', 'Doppelhaushälfte':'Maison jumelée', 'Bungalow':'Bungalow'};
const houseType = type => types[type] || type || 'Type non indiqué';
let records = [];
function render(){
  const status = $('status').value, city = $('city').value;
  const filtered = records.filter(r => (status === 'all' || (status === 'current' ? r.status === 'candidate' : r.status === 'archived')) && (city === 'all' || r.city === city))
    .sort((a, b) => (Number.isFinite(a.price_eur) ? a.price_eur : Infinity) - (Number.isFinite(b.price_eur) ? b.price_eur : Infinity));
  $('count').textContent = `${filtered.length} ${filtered.length === 1 ? 'maison affichée' : 'maisons affichées'}`;
  $('state').hidden = filtered.length > 0;
  $('state').textContent = records.length ? 'Aucune maison pour ces filtres. Essaie une autre ville ou affiche les archives.' : 'Aucune annonce dans les données pour le moment. La recherche est partielle : cela ne veut pas dire qu’aucune maison ne correspond.';
  $('cards').replaceChildren();
  for (const r of filtered) {
    const extras = [];
    if (Number.isInteger(r.rooms) && r.rooms > 0 && r.rooms < 30) extras.push(`${r.rooms} pièces`);
    if (Number.isInteger(r.year_built) && r.year_built >= 1800 && r.year_built <= new Date().getFullYear()) extras.push(`Construit en ${r.year_built}`);
    if (typeof r.buyer_commission_pct === 'number' && r.buyer_commission_pct >= 0 && r.buyer_commission_pct <= 20) extras.push(`Commission annoncée : ${number(r.buyer_commission_pct, '%')}`);
    const more = extras.length ? `<p class="extras">${extras.map(s => `<span>${safe(s)}</span>`).join('')}</p>` : '';
    const card = document.createElement('article');
    card.className = `card${r.status === 'archived' ? ' archived' : ''}`;
    card.innerHTML = `<div class="card-art" aria-hidden="true"><span class="card-art-house"></span><span class="card-art-label">Illustration, pas le bien</span></div><div class="card-body"><div class="card-top"><span class="card-location">${safe(r.city || 'Ville non indiquée')}</span><span class="card-status">${r.status === 'archived' ? 'Archive' : 'À explorer'}</span></div><h3>${safe(houseType(r.property_type))}</h3><p class="price"><small>Prix annoncé</small>${safe(number(r.price_eur, '€'))}</p><div class="facts"><div><small>Surface habitable</small>${safe(number(r.living_area_m2, 'm²'))}</div><div><small>Terrain (pas jardin)</small>${safe(number(r.plot_area_m2, 'm²'))}</div></div>${more}<p class="caution">Jardin utilisable et trajet à vélo jusqu’à la S1 non vérifiés.</p><div class="card-foot"><a href="${safe(r.url)}" target="_blank" rel="noopener noreferrer" aria-label="Ouvrir l’annonce d’origine : ${safe(houseType(r.property_type))}, ${safe(r.city || 'ville non indiquée')}, ${safe(number(r.price_eur, '€'))} (nouvel onglet)">Voir l’annonce d’origine <span aria-hidden="true">↗</span></a><small>Dernière vue : ${safe(date(r.last_seen))}<br>${safe(r.source || 'Source non indiquée')}</small></div></div>`;
    $('cards').append(card);
  }
}
async function init(){
  try {
    const response = await fetch('./data/listings.json', {cache:'no-store'});
    if (!response.ok) throw new Error('Données indisponibles');
    const data = await response.json();
    if (!Array.isArray(data.listings)) throw new Error('Format invalide');
    records = data.listings.filter(r => r && typeof r === 'object' && allowedUrl(r.url) && (r.status === 'candidate' || r.status === 'archived'));
    const cities = [...new Set(records.map(r => r.city).filter(c => typeof c === 'string' && c.trim()))].sort((a,b) => a.localeCompare(b, 'fr'));
    for (const city of cities) { const option = document.createElement('option'); option.value = city; option.textContent = city; $('city').append(option); }
    if (data.updated_at && date(data.updated_at) !== 'date non indiquée') $('updated').textContent = `Données mises à jour le ${date(data.updated_at)}${data.scan_state === 'partial_sample' ? ' · sélection partielle' : ''}`;
    render();
  } catch (_) {
    $('state').hidden = false;
    $('state').textContent = 'Données indisponibles pour le moment. Impossible de confirmer le statut des annonces. Réessaie plus tard.';
    $('count').textContent = 'Données indisponibles';
  }
}
$('status').addEventListener('change', render);
$('city').addEventListener('change', render);
init();

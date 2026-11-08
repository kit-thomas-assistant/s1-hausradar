#!/usr/bin/env python3
"""Bounded, fail-closed public-facts scan of one sitemap and direct listings."""
import argparse
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib import request, robotparser
from urllib.error import HTTPError
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'site/data/listings.json'
BASE = 'https://www.ohne-makler.net'
ROBOTS = BASE + '/robots.txt'
SITEMAP = BASE + '/sitemap-immobilien.xml'
AGENT = 'S1Hausradar/1.0 (small public-facts index; no images or contacts)'
DETAIL = re.compile(r'https://www\.ohne-makler\.net/immobilie/(\d{1,9})/')
SPARKASSE = re.compile(r'https://immobilien\.sparkasse\.de/expose/FID-F14-[\d-]+\.html')
CITIES = ('Erlangen', 'Fürth', 'Nürnberg', 'Lauf an der Pegnitz', 'Röthenbach an der Pegnitz', 'Schwaig bei Nürnberg', 'Rückersdorf')
TYPES = ('Bungalow', 'Reihenendhaus', 'Reiheneckhaus', 'Doppelhaushälfte', 'Einfamilienhaus')
XMLNS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
MAX_DETAIL = 30


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.meta = {}
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'meta':
            key = attrs.get('property') or attrs.get('name')
            if key in ('og:title', 'og:description', 'original-source'):
                self.meta[key] = attrs.get('content', '')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(' '.join(data.split()))


def valid_url(url):
    return isinstance(url, str) and (DETAIL.fullmatch(url) is not None or SPARKASSE.fullmatch(url) is not None)


def fetch(url, max_bytes, allow_missing=False):
    if not url.startswith(BASE + '/') or urlparse(url).query or urlparse(url).fragment:
        raise ValueError('Unexpected network URL')
    req = request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html, application/xml, text/plain'})
    try:
        with request.urlopen(req, timeout=18) as response:
            if response.status != 200 or response.url != url:
                raise ValueError('Unexpected response or redirect')
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError('Response size limit')
            return body.decode('utf-8', 'replace')
    except HTTPError as error:
        if allow_missing and error.code in (404, 410):
            return None
        raise


def parse_sitemap(raw, today):
    root = ET.fromstring(raw)
    if root.tag != XMLNS + 'urlset':
        raise ValueError('Expected listing sitemap')
    latest = today - timedelta(days=14)
    candidates = []
    for entry in root.findall(XMLNS + 'url'):
        url = entry.findtext(XMLNS + 'loc', default='')
        modified = entry.findtext(XMLNS + 'lastmod', default='')[:10]
        if DETAIL.fullmatch(url) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', modified):
            try:
                if latest <= date.fromisoformat(modified) <= today:
                    candidates.append((modified, url))
            except ValueError:
                continue
    return [url for _, url in sorted(set(candidates), reverse=True)]


def parse_detail(html, url):
    page = PageText()
    page.feed(html)
    if page.meta.get('original-source') != url:
        return None
    title = page.meta.get('og:title', '')
    description = page.meta.get('og:description', '')
    city = next((c for c in CITIES if title.endswith(' - ' + c)), None)
    prop_type = next((t for t in TYPES if re.match(r'^' + re.escape(t) + r' in ', description, re.I)), None)
    if not city or not prop_type:
        return None
    text = ' '.join(page.parts)
    price = re.search(r'\bKaufpreis\s+([\d.]+)\s*€', text)
    area = re.search(r'\b(\d{2,3})\s*m²\s+Wohnfläche\b', text)
    plot = re.search(r'\b([\d.]+)\s*m²\s+Grundstücksfläche\b', text)
    if not price or not area:
        return None
    amount = int(price.group(1).replace('.', ''))
    living = int(area.group(1))
    if not 0 < amount < 600000 or not 100 <= living <= 150:
        return None
    plot_m2 = int(plot.group(1).replace('.', '')) if plot else None
    if plot_m2 is not None and plot_m2 < 250:
        return None  # A usable 250 m² garden cannot fit on a smaller plot.
    return {'id': 'ohne-makler-' + DETAIL.fullmatch(url).group(1), 'url': url, 'source': 'Ohne-Makler', 'city': city,
            'district': None, 'property_type': prop_type, 'price_eur': amount, 'living_area_m2': living,
            'plot_area_m2': plot_m2,
            'usable_garden_m2': None, 'bike_minutes_to_s1': None,
            'uncertainties': ['usable_garden_m2', 'bike_minutes_to_s1', 'availability']}


def merge(old, observed, missing, today):
    by_id = {item['id']: dict(item) for item in old}
    for identifier, record in observed.items():
        prev = by_id.get(identifier, {})
        record.update(first_seen=prev.get('first_seen', today), last_seen=today, status='candidate', absence_checks=0)
        by_id[identifier] = record
    for identifier in missing:
        if identifier not in by_id:
            continue
        prev = by_id[identifier]
        prev['absence_checks'] = prev.get('absence_checks', 0) + 1
        if prev['absence_checks'] >= 2:
            prev['status'] = 'archived'
    return sorted(by_id.values(), key=lambda x: (x['status'] == 'archived', x['first_seen'], x['id']))


def run(today, transport=fetch, data_path=DATA):
    existing = json.loads(data_path.read_text(encoding='utf-8'))
    if existing.get('schema_version') != 1 or not isinstance(existing.get('listings'), list):
        raise ValueError('Existing data schema invalid; refusing to replace it')
    old = existing['listings']
    auto = [item for item in old if item.get('source') == 'Ohne-Makler']
    if sum(item.get('status') != 'archived' for item in auto) > MAX_DETAIL or any(not valid_url(item.get('url')) or item.get('id') != 'ohne-makler-' + DETAIL.fullmatch(item['url']).group(1) for item in auto):
        raise ValueError('Existing auto records invalid or exceed check cap')
    if any(not valid_url(item.get('url')) for item in old):
        raise ValueError('Existing manual records contain unsafe links')
    raw_robots = transport(ROBOTS, 100_000)
    if not raw_robots or 'User-agent:' not in raw_robots:
        raise ValueError('Missing or invalid robots policy')
    robots = robotparser.RobotFileParser()
    robots.parse(raw_robots.splitlines())
    if not robots.can_fetch(AGENT, SITEMAP):
        raise ValueError('Sitemap blocked by robots policy')
    urls = parse_sitemap(transport(SITEMAP, 8_000_000), today)
    if not urls:
        raise ValueError('No recent sitemap entries; refusing to update status')
    current = [item for item in auto if item['status'] != 'archived']
    pool = urls[:1000]
    shift = (today.toordinal() * 24) % len(pool)
    scheduled = [item['url'] for item in current] + (pool[shift:] + pool[:shift])
    scheduled = list(dict.fromkeys(scheduled))[:MAX_DETAIL]
    observed = {}
    missing = set()
    old_ids = {item['id'] for item in auto}
    for url in scheduled:
        if not robots.can_fetch(AGENT, url):
            raise ValueError('Detail blocked by robots policy')
        html = transport(url, 1_000_000, allow_missing=True)
        identifier = 'ohne-makler-' + DETAIL.fullmatch(url).group(1)
        if html is None:
            if identifier in old_ids:
                missing.add(identifier)
            continue
        record = parse_detail(html, url)
        if record:
            observed[identifier] = record
    updated = {'schema_version': 1, 'updated_at': today.isoformat(), 'scan_state': 'partial_sample',
               'listings': merge(old, observed, missing, today.isoformat())}
    if updated != existing:
        temp = data_path.with_suffix('.json.tmp')
        temp.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        temp.replace(data_path)
    return len(scheduled), len(observed), len(updated['listings'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=date.fromisoformat, default=datetime.now(timezone.utc).date(), help='UTC YYYY-MM-DD (testing only)')
    args = parser.parse_args()
    try:
        checked, matched, retained = run(args.date)
        print(f'Partial scan: {checked} direct pages checked, {matched} matching today, {retained} retained. Not exhaustive.')
    except Exception as exc:
        print(f'Scan failed; existing data untouched: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(1)

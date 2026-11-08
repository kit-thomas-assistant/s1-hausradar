import json
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import date
from urllib.error import URLError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import update as u

TODAY = date(2026, 11, 8)
URL = u.BASE + '/immobilie/493283/'
ROBOTS = 'User-agent: *\nDisallow: /immobilie/list/\n'
SITEMAP = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{URL}</loc><lastmod>2026-11-08</lastmod></url><url><loc>https://www.ohne-makler.net/immobilie/list/not-a-home</loc><lastmod>2026-11-08</lastmod></url></urlset>'
PAGE = f'''<html><head><meta name="original-source" content="{URL}"><meta property="og:title" content="Example - Einfamilienhaus - Nürnberg"><meta property="og:description" content="Einfamilienhaus in Nürnberg von privat"></head><body>125 m² Wohnfläche 540 m² Grundstücksfläche Kaufpreis 549.000 €<script>Kaufpreis 1 €</script></body></html>'''

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'listings.json'
        self.seed = {'schema_version': 1, 'updated_at': None, 'scan_state': 'not_run', 'listings': []}
        self.path.write_text(json.dumps(self.seed))
    def tearDown(self):
        self.tmp.cleanup()
    def transport(self, url, maximum, allow_missing=False):
        return {u.ROBOTS: ROBOTS, u.SITEMAP: SITEMAP, URL: PAGE}[url]
    def read(self): return json.loads(self.path.read_text())

    def test_nominal_and_dedup_first_seen(self):
        self.assertEqual(u.run(TODAY, self.transport, self.path), (1, 1, 1))
        first = self.read()['listings'][0]
        self.assertEqual((first['first_seen'], first['last_seen'], first['status']), ('2026-11-08','2026-11-08','candidate'))
        self.assertIsNone(first['usable_garden_m2'])
        self.assertNotIn('address', first)
        u.run(date(2026,11,9), self.transport, self.path)
        self.assertEqual(len(self.read()['listings']), 1)
        self.assertEqual(self.read()['listings'][0]['first_seen'], '2026-11-08')

    def test_no_result_keeps_old_and_no_archive(self):
        u.run(TODAY, self.transport, self.path)
        nonmatch = PAGE.replace('549.000 €', '649.000 €')
        def source(url, maximum, allow_missing=False):
            return nonmatch if url == URL else self.transport(url, maximum, allow_missing)
        u.run(date(2026,11,9), source, self.path)
        self.assertEqual(self.read()['listings'][0]['status'], 'candidate')
        self.assertEqual(self.read()['listings'][0]['last_seen'], '2026-11-08')

    def test_no_data_fails_without_replacing(self):
        before = self.path.read_bytes()
        with self.assertRaises(ValueError): u.run(TODAY, lambda url, m, allow_missing=False: ROBOTS if url == u.ROBOTS else '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>', self.path)
        self.assertEqual(before, self.path.read_bytes())

    def test_transport_failure_rolls_back_all(self):
        before = self.path.read_bytes()
        def broken(url, maximum, allow_missing=False):
            if url == URL: raise URLError('network')
            return self.transport(url, maximum, allow_missing)
        with self.assertRaises(URLError): u.run(TODAY, broken, self.path)
        self.assertEqual(before, self.path.read_bytes())

    def test_robots_denial_fails_closed(self):
        before = self.path.read_bytes()
        def denied(url, maximum, allow_missing=False):
            return 'User-agent: *\nDisallow: /sitemap-immobilien.xml\n' if url == u.ROBOTS else self.transport(url, maximum, allow_missing)
        with self.assertRaises(ValueError): u.run(TODAY, denied, self.path)
        self.assertEqual(before, self.path.read_bytes())

    def test_archive_only_after_two_explicit_absences(self):
        u.run(TODAY, self.transport, self.path)
        def missing(url, maximum, allow_missing=False):
            return None if url == URL else self.transport(url, maximum, allow_missing)
        u.run(date(2026,11,9), missing, self.path)
        self.assertEqual(self.read()['listings'][0]['status'], 'candidate')
        u.run(date(2026,11,10), missing, self.path)
        self.assertEqual(self.read()['listings'][0]['status'], 'archived')

    def test_invalid_category_and_private_fields_not_exported(self):
        self.assertFalse(u.valid_url(u.BASE + '/immobilie/list/'))
        self.assertFalse(u.valid_url('https://www.immobilienscout24.de/'))
        record = u.parse_detail(PAGE.replace('</body>', 'Seller Jane Doe jane@example.com 1 Main Street</body>'), URL)
        self.assertIsNotNone(record)
        self.assertNotIn('Jane', json.dumps(record))
        self.assertIsNone(u.parse_detail(PAGE.replace('549.000 €', '€ undisclosed'), URL))

    def test_plot_below_required_garden_is_rejected(self):
        self.assertIsNone(u.parse_detail(PAGE.replace('540 m² Grundstücksfläche', '220 m² Grundstücksfläche'), URL))

    def test_optional_rooms_and_construction_year_require_source_evidence(self):
        record = u.parse_detail(PAGE.replace('125 m² Wohnfläche', '7 Zimmer 125 m² Wohnfläche Baujahr 1933'), URL)
        self.assertEqual((record['rooms'], record['year_built']), (7, 1933))
        record = u.parse_detail(PAGE.replace('125 m² Wohnfläche', '125 m² Wohnfläche 7 Zimmer 124 m² Wohnfläche'), URL)
        self.assertIsNone(record['rooms'])

    def test_manual_source_untouched(self):
        manual = {'id':'sparkasse-FID-F14-176-636','url':'https://immobilien.sparkasse.de/expose/FID-F14-176-636.html','source':'Sparkassen-Immobilien','status':'candidate','first_seen':'2026-11-08','last_seen':'2026-11-08','rooms':6,'buyer_commission_pct':3.57}
        self.seed['listings'] = [manual]
        self.path.write_text(json.dumps(self.seed))
        u.run(TODAY, self.transport, self.path)
        self.assertIn(manual, self.read()['listings'])

if __name__ == '__main__': unittest.main()

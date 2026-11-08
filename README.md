# S1 Hausradar

A small, source-linked house watch along the S1 corridor between Erlangen and Lauf. Static site, no cookies, analytics, third-party assets, API keys or inbound server. Intended for a **public** repository. The current three manual candidates were checked on original pages on 2026-11-08; they are **leads to verify**, not confirmed matches.

## Local run

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update.py                         # live bounded outgoing fetch, changes site/data/listings.json
python3 -m http.server 8765 --bind 127.0.0.1 --directory site
# open http://127.0.0.1:8765/ locally; Ctrl-C to stop
```

The page works without a build step; do not open `file://` because fetch of JSON may be blocked. To run the scan without network, use the mocked unit tests. `python3 scripts/update.py --date YYYY-MM-DD` accepts UTC date for testing only; never backdate a production scan.

## Schema and provenance

`site/data/listings.json` is the only published data source. Each record has a source name and a **direct canonical listing URL**, coarse city/district, source-observed price, living/plot area (plot may be null), house type, `first_seen`, `last_seen`, `status` (`candidate` / `archived`) and explicit `uncertainties`. `usable_garden_m2` and `bike_minutes_to_s1` are null until independently checked. **Plot area is not usable garden area.** The source page, not this project, is authoritative for price, availability and contact. `updated_at` reflects a scan date, not a verification of every archived or manual record. Manual Sparkasse records remain unchanged by the automatic source scanner and must be checked by a person again. `absence_checks` increments only on explicit HTTP 404/410 of known Ohne-Makler pages; archive after two such successful checks. A changed price/type or no match does not imply sale.

No address, owner/seller name, contact information, source photo, listing description, precise station route or verbatim title is stored. The manual inspection notes are local-only, excluded from the public repository. Do not automatically import external submissions without manual verification.

## Source policy and scope

As checked **2026-11-08**, [Ohne-Makler robots.txt](https://www.ohne-makler.net/robots.txt) excludes `/immobilie/list/` and print pages but not `/sitemap-immobilien.xml` or `/immobilie/<numeric id>/`. Its [AGB](https://www.ohne-makler.net/allgemeine-geschaeftsbedingungen/) describes free public search and contains no express general permission for republishing listings; this project therefore republishes **only minimal factual fields and direct attribution**, no text/images/contact details. This is a cautious interpretation, not a legal opinion or blanket grant of scraping permission. Recheck policies before activating and periodically thereafter; stop on objections/changes. The scanner requests `robots.txt` first **on every run** and aborts if it cannot establish access. It never uses ImmoScout24 or Kleinanzeigen, never logs in, bypasses anti-bot measures, follows category pages, or fetches seller media. Sparkasse records were manually checked, **not scraped on schedule**; its automation policy has not been established.

The daily scanner reads one public sitemap, considers only the most recent 14-day entries and the freshest 1,000 as a bounded sampling pool, rotates deterministic 24-entry daily slices, plus previously seen Ohne-Makler records, with **at most 30 detail requests/day**. It excludes a listing when the entire plot is known to be below 250 m², while treating larger plots as unconfirmed garden size. It checks exact allowlisted URLs and rejects redirects, category pages, robots denials, unparseable facts, off-corridor cities, homes beyond the price/area cutoffs and missing canonical detail metadata. The corridor city allowlist is a broad geography gate **not a claim of 10 minutes by bike to S1**. This is **not comprehensive discovery**; zero new results is not proof of no homes. `scan_state: partial_sample` makes that explicit. On fetch/parse-policy/network error, it exits nonzero before touching the JSON. On a successful zero-match scan it keeps the prior history. A page not matching the current filters is retained, not silently archived. Page HTML can change and the conservative parser may miss valid results. Older listings outside the recent sampling window will not be discovered unless manually seeded.

## GitHub Pages setup (not yet published)

1. Create public `kit-thomas-assistant/s1-hausradar` repository, review all files for public-only content, push this directory to its default branch. Do not push credentials or private research files.
2. Repository **Settings → Pages → Build and deployment → Source: GitHub Actions**. The workflow asks for `contents: write` only on the scan job and `pages: write` / `id-token: write` only on the deploy job; do not relax repository-wide safeguards preemptively. If a direct Actions push is blocked by policy or branch protection, switch to a reviewed PR flow rather than weakening safeguards silently.
3. Actions → `Scan and publish` → `Run workflow` for a first test. On success, GitHub Pages deploys only `site/`. Daily schedule is 06:17 UTC, not fixed Berlin local time, and GitHub schedules can be delayed or skipped. No cron is installed on the home machine. A scan failure blocks deployment and retains the previous committed JSON; check the Actions run status rather than assuming the site refreshed. GitHub Actions artifacts contain only `site/`.

The workflow uses standard `GITHUB_TOKEN` only and never creates an account, buys anything or opens an inbound port. **It is prepared, not deployed or enabled here.** Public Pages can expose even a private repository's Pages output; this project is explicitly intended for public facts only.

## Design

Editorial green-and-paper layout with an abstract, CSS-only route diagram, responsive grid, keyboard focus and reduced-motion support. No copied photography or remote fonts. The requested “Fontaine Design” plugin was not identifiable in the available catalog; nothing was installed. Design follows the available `frontend-design` skill instead.

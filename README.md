# S1 Hausradar

A small, source-linked house watch along the S1 corridor between Erlangen and Lauf. Static site, no cookies, analytics, third-party assets, API keys or inbound server. Intended for a **public** repository. The current three candidates (one automatic Ohne-Makler, two manually checked Sparkasse) were checked on original pages on 2026-11-08; they are **leads to verify**, not confirmed matches.

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

No address, owner/seller name, contact information, source photo, listing description, precise station route or verbatim title is stored. Optional public facts such as number of rooms, year built or stated buyer commission appear only when checked on the source; they are not guarantees. For automated records, room and year fields are parsed from the detail page only if identifiable, and can be null. The manual inspection notes are local-only, excluded from the public repository. Do not automatically import external submissions without manual verification.

## Source policy and scope

As checked **2026-11-08**, [Ohne-Makler robots.txt](https://www.ohne-makler.net/robots.txt) excludes `/immobilie/list/` and print pages but not `/sitemap-immobilien.xml` or `/immobilie/<numeric id>/`. Its [AGB](https://www.ohne-makler.net/allgemeine-geschaeftsbedingungen/) describes free public search and contains no express general permission for republishing listings; this project therefore republishes **only minimal factual fields and direct attribution**, no text/images/contact details. This is a cautious interpretation, not a legal opinion or blanket grant of scraping permission. Recheck policies before activating and periodically thereafter; stop on objections/changes. The scanner requests `robots.txt` first **on every run** and aborts if it cannot establish access. It never uses ImmoScout24 or Kleinanzeigen, never logs in, bypasses anti-bot measures, follows category pages, or fetches seller media. Sparkasse records were manually checked, **not scraped on schedule**; its automation policy has not been established.

The daily scanner reads one public sitemap, considers only the most recent 14-day entries and the freshest 1,000 as a bounded sampling pool, rotates deterministic 24-entry daily slices, plus previously seen Ohne-Makler records, with **at most 30 detail requests/day**. It excludes a listing when the entire plot is known to be below 250 m², while treating larger plots as unconfirmed garden size. It checks exact allowlisted URLs and rejects redirects, category pages, robots denials, unparseable facts, off-corridor cities, homes beyond the price/area cutoffs and missing canonical detail metadata. The corridor city allowlist is a broad geography gate **not a claim of 10 minutes by bike to S1**. This is **not comprehensive discovery**; zero new results is not proof of no homes. `scan_state: partial_sample` makes that explicit. On fetch/parse-policy/network error, it exits nonzero before touching the JSON. On a successful zero-match scan it keeps the prior history. A page not matching the current filters is retained, not silently archived. Page HTML can change and the conservative parser may miss valid results. Older listings outside the recent sampling window will not be discovered unless manually seeded.

## GitHub Pages and daily workflow

The public page is live at **https://kit-thomas-assistant.github.io/s1-hausradar/**. GitHub Pages serves only `site/` from the [public repository](https://github.com/kit-thomas-assistant/s1-hausradar). The first manual [scan and deployment](https://github.com/kit-thomas-assistant/s1-hausradar/actions/runs/42488665620) succeeded on 2026-11-08, and an anonymous GET returned HTTP 200 for both the index and data file. Three initial records are candidates to verify, not confirmed matches. No manual inputs, account credentials, or private research notes are committed.

The workflow is active and scheduled daily at **06:17 UTC**, which is not a fixed Berlin time. GitHub schedules can be delayed/skipped and may be disabled after long public-repo inactivity, so check the `updated_at` stamp and [Actions history](https://github.com/kit-thomas-assistant/s1-hausradar/actions/workflows/daily.yml). A scan failure blocks deployment and retains the last successful site; no home-machine cron is installed. Run `gh workflow run daily.yml --ref main` for a manual test. The workflow asks for `contents: write` only on the scan job and `pages: write` / `id-token: write` only on the deploy job. If a future direct Actions push is blocked by policy or branch protection, use a reviewed PR flow rather than weakening safeguards silently. The workflow uses standard `GITHUB_TOKEN` only and never creates an account, buys anything or opens an inbound port.

## Design and image rights

The French homepage prioritizes the house cards over methodology: announced price, habitable area, plot (not usable garden), optional sourced room/year/commission facts and a link to the original listing. Archive and city filters remain. The short methodological caveat is collapsed. The decorative house drawings are CSS illustrations **not depictions of the advertised houses**. The original listing is the place to see its photographs.

No source photography is downloaded, mirrored or hotlinked. The [Ohne-Makler AGB](https://www.ohne-makler.net/allgemeine-geschaeftsbedingungen/) permit distribution of advertiser images on that portal and selected partner portals, not a blanket third-party license. Sparkasse listing images may have rights reserved by individual providers; a private site or OTP would not transfer their copyrights. Contact the rights holder for explicit reuse permission before changing this. The requested “Fontaine Design” plugin was not identifiable in the available catalog; nothing was installed. Design follows the available `frontend-design` skill instead.

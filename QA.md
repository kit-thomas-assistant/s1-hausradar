# Local verification, 2026-11-08

- `python3 -m unittest discover -s tests -q`: 9 tests passed (nominal, stable first_seen/dedup, zero matches, empty sitemap, network rollback, robots refusal, two-absence archival, no private-field export, plot too small, manual-source preservation).
- `node --check site/app.js`: passed.
- `python3 scripts/update.py`: live bounded scan succeeded, 30 direct pages checked, one existing Ohne-Makler candidate matched, three public-safe candidates retained. `site/data/listings.json` checked for strict public fields, direct URLs, null usable-garden and bike-time metrics.
- `site/` static preview server bound to `127.0.0.1` only, then stopped. No service exposed or publication made.
- Visual screenshot QA **not performed**: visual-checker preflight refused browser startup with `High browser instance count: 25 top-level browsers (threshold 8)`. Did not bypass this safeguard. A screenshot/viewport review remains for the parent or a later low-load run before publication.
- GitHub Actions [run 42488665620](https://github.com/kit-thomas-assistant/s1-hausradar/actions/runs/42488665620) completed successfully (scan + deployment), workflow active. Anonymous HTTP GET of `https://kit-thomas-assistant.github.io/s1-hausradar/` and `data/listings.json` returned 200; the served JSON had three candidate records, no personal/contact fields, and null garden/route metrics. The daily schedule is configured; the next scheduled execution has not yet happened, so recurring reliability is not proven.

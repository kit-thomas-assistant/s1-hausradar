# Local verification, 2026-11-08

- `python3 -m unittest discover -s tests -q`: 8 tests passed (nominal, stable first_seen/dedup, zero matches, empty sitemap, network rollback, robots refusal, two-absence archival, no private-field export, manual-source preservation).
- `node --check site/app.js`: passed.
- `python3 scripts/update.py`: live bounded scan succeeded, 30 direct pages checked, one existing Ohne-Makler candidate matched, three public-safe candidates retained. `site/data/listings.json` checked for strict public fields, direct URLs, null usable-garden and bike-time metrics.
- `site/` static preview server bound to `127.0.0.1` only, then stopped. No service exposed or publication made.
- Visual screenshot QA **not performed**: visual-checker preflight refused browser startup with `High browser instance count: 25 top-level browsers (threshold 8)`. Did not bypass this safeguard. A screenshot/viewport review remains for the parent or a later low-load run before publication.
- GitHub Actions workflow **not executed remotely**; repository and Pages not created/published. Set up and test per README before asserting production status.

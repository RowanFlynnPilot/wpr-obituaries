# STATUS

## 2026-07-01 — Home onboarding CLI (`scripts/add_home.py`)

**What moved.** Added a self-service onboarding tool so a new newsroom can add a
funeral home without reverse-engineering it: `python scripts/add_home.py <url>`
fetches the home's obituaries page (Python-side, since the fetch is cross-origin
and Cloudflare-fronted — a browser can't do it), detects the platform, extracts
+ verifies the Tukios `siteAlias` against the live API, and with `--write`
inserts the `data/funeral_homes.json` entry preserving the one-home-per-line
format. Tribute Technology sites are reported as recognized-but-not-scrapable.
Added `tukios.site_summary` for the verify step. Tests cover the pure helpers
(platform detect, match derive, entry format, clean insert); live-checked
against Helke (verified + dedup) and Schmidt & Schulta (Tribute). This is the
engine the planned in-browser admin panel will call server-side.

**What's next (admin panel).** The requested in-browser "add a home" UI needs a
server-side path for the same detection (CORS blocks it client-side) plus a
place to persist requests — i.e. the deferred Supabase/hosted-backend tier.
Design to be confirmed before building: likely a small form → serverless
function running `add_home`'s detection → a review queue → a committed config
edit. Sequenced after the scraper itself is confirmed live.

## 2026-07-01 — Funeral-home scraper (`funeral_home_scrape` adapter)

**What moved.** Added a third write-source, `extract/adapters/funeral_home_scrape.py`,
behind the existing `Unit` seam — it scrapes the area funeral homes' own sites
*upstream* of WPR's compiled batch posts. New `extract/tukios.py` is the Tukios
JSON-API client (public read token, per-site alias, death-date windowed
pagination); the adapter maps each already-structured Tukios record straight to
an `Obituary` with no model extraction. Seven verified Tukios homes are wired in
`data/funeral_homes.json` (`platform` + `siteAlias`); `homes.load_homes` now
carries those fields, `enabled_sources` registers the adapter, `newsroom.config.json`
enables it (`windowDays: 45`), and `main.py`'s normal-cron window resolution is
no longer hard-tied to the wordpress adapter. Scraped homes auto-publish (a
configured home is a trusted source); cross-source overlap with the WPR batch is
collapsed by the existing render-time dedupe. Docs: `docs/funeral-home-scraping.md`;
CLAUDE.md updated. Test suite extended (adapter mapping, town facet, stable id,
hash revision, alias regex, windowed stop) — **all pass**. Verified live end-to-end
against Brainard (real records mapped correctly) and through a full isolated
render (cross-source dedupe collapsed a real WPR+funeral-home duplicate to one
canonical entry; sitemap well-formed). `--render-only` on the committed master is
unchanged (585 cards reused, no tracked-file diff).

**What's next.**
- **Go-live decision (owner):** the adapter is enabled in the working tree but
  not committed/pushed. The first cron after push begins scraping (45-day window
  per home) and will add recent obits — including duplicates of WPR-batch people,
  which dedupe collapses in the register but which double the raw page count.
- **Confirm the home list with Shereen** — the seven scraped homes are the
  republication permission set; the outer-ring ones (Merrill, Marshfield,
  Wittenberg-adjacent, Rhinelander) especially.
- **Tribute Technology platform** (Schmidt & Schulta, Buettgen, Mid-Wisconsin,
  Carlson) — the second scraper platform, not yet built (raises if configured).
- **Longer term:** once scraping covers a home fully, its WPR-batch coverage is
  redundant and `wordpress_scrape` could be retired, removing Shereen's manual
  compilation entirely — a separate decision.

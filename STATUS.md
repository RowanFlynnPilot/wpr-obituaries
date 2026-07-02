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

## 2026-07-01 — Staff admin page + add-home workflow

**What moved.** Built the in-browser "add a home" surface as the staff-only,
git-native design (no Supabase). `.github/workflows/add-home.yml` is a
`workflow_dispatch` (inputs: url, optional name/match) that runs
`scripts/add_home.py --write` and, if the config changed, opens a PR for review;
already-configured / not-scrapable outcomes report to the run summary without a
PR. `web/public/admin.html` is a self-contained, brand-styled staff page (no
build step, fork-portable) that dispatches that workflow via the GitHub API
using the staff member's own fine-grained PAT (Actions: read+write) — the token
stays in the browser, since a static site can't safely hold a repo credential
and the detection fetch can't run client-side (CORS/Cloudflare). Verified: page
renders with correct brand styling and no JS errors; workflow YAML valid; tests
pass. **Requires** "Allow GitHub Actions to create and approve pull requests"
(repo Settings → Actions), and the workflow must be on `main` before the API can
dispatch it — so this activates when PR #28 merges.

**Possible follow-ups.** GitHub OAuth device flow instead of a pasted PAT
(nicer sign-in, still no backend); folding the admin page into the Vite build so
the repo slug comes from config rather than being entered.

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

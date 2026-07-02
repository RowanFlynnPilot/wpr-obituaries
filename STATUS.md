# STATUS

## 2026-07-01 — Go-live + refinement pass (both scrapers live on main)

**What moved.** Merged the scraper (PR #28) and went live; the extract workflow
now runs `wordpress_scrape` + `funeral_home_scrape`. Verifying the first live
scrape under observation (rather than waiting for the cron) caught two real
coverage bugs, both fixed: (1) some Tukios homes pin an older "featured"
obituary at the top, which the windowing treated as end-of-window and returned
zero — Helke/Beste came back empty (PR #30); (2) the shared poll window let
WordPress's 14 days override the funeral homes' configured 45, so every home
under-collected — now each source polls its own window (PR #31). Also hardened
cross-source dedupe: normalized first+last name matching (PR #29) and folding
WPR year-only records into the same person's full-date group (PR #32); and added
a town facet for Tribute records (PR #30). With the 45-day window, the live scrape
pulls ~192 obituaries across the 11 homes; the hardened dedupe collapses ~125
WPR↔funeral-home duplicates that would otherwise have shown twice.

**wordpress_scrape retirement analysis.** Within the overlapping 45-day window,
**~93% of WPR's obituaries are now covered directly by funeral-home scraping**
(~96% counting records the year-only dedupe fix reconciles). The genuine
WPR-only residual is ~3–4%: obituaries with no funeral home on record (can't be
attributed — e.g. an out-of-town family) and ones a scraped home hadn't posted
yet when WPR did (publish-timing). **Recommendation: keep `wordpress_scrape` as
the safety net for now** — it is clearly secondary (funeral-home scraping is
primary), but retiring it would drop that residual. Path to retirement: watch the
residual over a few weeks; if it is consistently just publish-timing (the home
posts a day later) plus intake-coverable unattributable ones, WPR can be dropped
— which removes Shereen's manual batch-compilation step, the end goal.

**Still open.** Admin sign-in polish (OAuth device flow instead of a pasted PAT)
needs a GitHub OAuth app registered on the WPR account first — owner action.
Folding the admin page into the Vite build (config-driven repo slug) is optional.
The repo setting "Allow GitHub Actions to create and approve pull requests" is
still needed for the add-home workflow to open its PR — owner action.

## 2026-07-01 — Tribute Technology platform (second scraper)

**What moved.** `funeral_home_scrape` now supports the second platform, Tribute
Technology (Frazer/TCO), covering Schmidt & Schulta, Buettgen (honorone.com),
Mid-Wisconsin Cremation Society, and Carlson. New `extract/tribute.py`:
discovery via each home's Recent-Obituaries RSS (windowed by pubDate; obituary
sitemaps for `--backfill`), and per-person extraction from the schema.org
`Person` JSON-LD (full text, both dates, portrait) — no model extraction, same
as Tukios. The adapter now dispatches per `platform`; the Tribute revision is the
RSS pubDate / sitemap lastmod, so `is_processed` skips unchanged obituaries
without fetching the page (the person page is fetched only for new/changed
units). Tribute records carry no town facet (no structured city) and age is
computed from the two dates. The four homes are wired in `funeral_homes.json`
(`platform: "tribute"`, keyed by url). The onboarding CLI + admin workflow now
detect and onboard Tribute homes too (verified via RSS; name from the site's
business JSON-LD / og:site_name / title). Tests extended (Tribute client +
mapping, optional-siteAlias entry format); live-verified end-to-end against
Schmidt & Schulta (9 obituaries mapped, dates/age/body correct, UTF-8 clean) and
the CLI against all four homes. All pass.

**What's next.** With both platforms live, the scraper covers 11 in-area homes.
Gunderson/Conroe stay on the manual intake path (out-of-area one-offs). Remaining
open items are unchanged: the go-live merge decision (PR #28), confirming the
home list with Shereen, and — longer term — retiring `wordpress_scrape` once
scraping fully covers a home.

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

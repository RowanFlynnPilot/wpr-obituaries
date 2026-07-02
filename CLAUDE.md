# CLAUDE.md — WPR Obituaries

Operating notes for any Claude session working in this repo. Read this first.

## What this is

A sponsorable obituary tool for Wausau Pilot & Review. WPR already publishes
daily batch obituary posts (e.g. "Wausau area obituaries June 19, 2026"), each
containing several people. This tool turns those batches into a searchable,
SEO-ranking experience without changing the newsroom's submission workflow.

The whole point is **individual discoverability**: when someone Googles
"<name> obituary Wausau" they should land on WPR, not Legacy.com. A batch post
buries each person, so we extract them into individually addressable pages.

## Architecture (the one correct path)

Source of truth → static output → embedded widget:

1. `extract/wp_client.py` — pulls obituary batch posts from the Newspack/
   WordPress REST API. WPR is behind Cloudflare, so every request routes
   through a Webshare residential proxy (same mechanism as the gas-prices
   widget). Fails loudly if `WEBSHARE_PROXY_URL` is unset. The endpoint
   (`apiBase`/`categorySlug`) comes from the newsroom config, not constants.
2. `extract/extractor.py` — Claude Haiku reads each batch post and returns one
   structured record per person. Regex parsing is wrong here: obituary
   formatting varies too much. The model extracts only what is present and
   never invents detail. `wp_client` + `extractor` are wrapped by
   `extract/adapters/wordpress_scrape.py` behind the generic *write-source*
   contract (`adapters/base.Unit`): a source yields units of work, the sync loop
   never knows where a record came from. This is the seam that makes the tool a
   forkable template (see `docs/multi-tenant-reshape.md`). Two other write-sources
   ride the same seam: `extract/adapters/funeral_home_scrape.py` reads the area
   funeral homes' own sites *upstream* of WPR's batches (Tukios JSON API — already
   structured, no model extraction; see `docs/funeral-home-scraping.md`), and
   `extract/adapters/intake.py` folds in reviewed manual submissions.
3. `extract/templates.py` — renders one crawlable HTML page per person plus a
   `sitemap.xml`. **This is the SEO layer.** Each page has the name in the title
   and H1, schema.org `Obituary` structured data, canonical, and OG tags.
4. `extract/store.py` — the **persistent master** (`data/obituaries_master.json`,
   `{posts, records}`). This is the source of truth that lets pages outlive the
   fetch window. It is committed to the repo and grows over time.
5. `extract/main.py` — two phases:
   - **Sync** (skipped by `--render-only`): loop over every enabled write-source
     and extract only *new or changed* units (the `posts` map tracks each
     processed unit by its `modified_gmt`, keyed `<source>:<unit_id>` so two
     sources can't collide; v1 bare-id files migrate on load). Upsert them into
     the master. Per-unit failures are quarantined to `data/failures.json` and
     exit the run non-zero, but the master is still saved first — no silent gaps,
     no lost catalogue.
   - **Render** (always): rebuild `web/public/data/obituaries.json` (light
     index), every `web/public/o/<slug>.html`, and `web/public/sitemap.xml`
     from the **entire master**. Rendering is free (no API), so the window only
     bounds extraction cost, never what stays published. A 0-record render is
     refused (`--allow-empty` to override) so a bad fetch can't wipe the site.
   The rendered files are gitignored build artifacts; only the master is
   committed. `python extract/main.py --render-only` regenerates them locally
   (and reaches every existing page after a template/brand change).
6. `web/` — React 18 / Vite memorial register. The **browse + search** layer
   only. It fetches the JSON index and links each card to the static page.
7. `.github/workflows/extract.yml` — cron Mon/Wed/Fri 6 AM Central. Runs sync +
   render, commits the updated master back (`contents: write`), then builds the
   widget and deploys to Pages. A failed extract skips the deploy (the last good
   deploy stays live) but still persists the master.

The React widget is the iframe embed on WordPress. The static `o/*.html` pages
are what actually get crawled and ranked. Do not collapse these two layers —
an iframe cannot rank individual names; the parent WP page absorbs indexing.

## Engineering rules (do not drift)

- Don't overengineer. Simple beats complex.
- One correct path, no fallbacks. Absent optional data (photo, dates) is null,
  not an error — but a broken precondition (missing env, no name, bad JSON)
  raises immediately and loudly.
- One way to do a thing. Single responsibility per function.
- Surgical changes only. Fix root causes, not symptoms.
- `CLAUDE.md` stays current in this repo.

## Configuration

`newsroom.config.json` (repo root) is the **one per-newsroom file** — identity,
branding (logo, accent, fonts, seal), widget copy, and which `adapters` are
enabled. Read by both runtimes: Python via `extract/config.py` (validates,
raises on a missing required key), and the widget via `web/vite.config.js`
(injected at build, no runtime fetch). A fork rebrands by editing this file — no
code change (or run `python scripts/bootstrap.py` to generate it; fork quickstart
in `docs/forking.md`). Secrets never live here (they stay in env, below). The
static-page renderer and the React widget both read it, so the two surfaces stay
in lockstep. The template ships **intake-only** and runs with no API keys — the
Anthropic client and the Webshare proxy are built lazily, only when the
`wordpress_scrape` source actually runs, so `ANTHROPIC_API_KEY` /
`WEBSHARE_PROXY_URL` are needed only by newsrooms that enable scraping.

Environment (extractor):

- `ANTHROPIC_API_KEY` — for Haiku extraction.
- `WEBSHARE_PROXY_URL` — e.g. `http://user:pass@proxy.webshare.io:80`.
- `PUBLIC_BASE_URL` — where pages are served and indexed. **Required, no
  default**, because the canonical URL must point at the real location.
  Currently `https://rowanflynnpilot.github.io/wpr-obituaries` until a custom
  subdomain is in place.

Analytics are optional and config-driven (`analytics` block: `provider` +
`domain`/`site`/`headHtml`). `extract/analytics.py` and `web/vite.config.js`
inject the same cookieless provider snippet (plausible/goatcounter/cloudflare/
custom) into both the static pages and the widget, so pageviews — which double as
sponsor impressions — and sponsor-logo click events report to one account. Empty
`provider` renders nothing. See `docs/forking.md`.

Sponsors live in `web/public/data/sponsor.json`:
`{ "label", "sponsors": [ { "name", "url", "logo" }, ... ] }`. Each sponsor's
`name` is required; `url` and `logo` (repo-relative path, e.g. `assets/helke.png`,
served identically by the widget and the static pages) are optional. All
sponsors render together in the masthead, the footer card, every obituary page,
and the schema.org `sponsor`. Vendor logos under `web/public/assets/` rather
than hotlinking. Current sponsors: **Helke** and **Brainard** (co-owned). Swap
them all there — no code change. Per-funeral-home attribution still appears as
arrangement metadata on each record.

`web/vite.config.js` `base` must match the serving path
(`/wpr-obituaries/` for a Pages project site, `/` for a custom domain root).

Funeral-home scraping (`adapters.funeral_home_scrape`, `windowDays` in config)
reads the homes' own sites directly. Per-home scrape config lives in
`data/funeral_homes.json` (`platform` + its key). Two platforms are wired:
**Tukios** (seven homes, keyed by `siteAlias`, JSON API) and **Tribute
Technology** (four homes, keyed by `url`, RSS discovery + `Person` JSON-LD). The
scraped-home list is also the republication permission list — full details, both
platforms' mechanics, and the cross-source dedupe/overlap note are in
`docs/funeral-home-scraping.md`.

## Known decisions and open items

- **Duplicate content**: per-person pages reproduce the full obit text, which
  overlaps the original batch posts. Each page is self-canonical with unique
  title/H1/URL + schema, so it should win on specificity; the WordPress-side
  playbook (sitemap, batch-post linking, when to trim batch posts) is in
  `docs/seo-batch-posts.md`.
- **SEO domain**: pointing `obituaries.wausaupilotandreview.com` at Pages keeps
  ranking equity on the brand domain. Recommended before heavy promotion — the
  exact DNS + repo steps are prepped in `docs/custom-subdomain.md` (apply after
  DNS resolves; don't merge the `base: "/"` change before then).
- **Seeding the master**: the chosen migration is a one-time **6-month seed**,
  `python extract/main.py --days 180` (or workflow dispatch with `seed_days=180`)
  — ~73 posts, ~15-20 min, a few dollars. The full `--backfill` (every post since
  Oct 2017, ~1,309 posts / multiple hours, risks the 6 h Actions timeout) exists
  but is not needed; deep history isn't wanted. After seeding, the cron's
  `WINDOW_DAYS` (currently **14**) only bounds *new-post extraction* — the master
  accumulates forward forever, so the published catalogue only grows.
- **Persistence (fixed)**: pages used to be regenerated from only the window and
  would 404 once they aged out — fatal for the SEO premise. The master store +
  render-everything design fixes this; a published page is permanent.
- **Sitemap (done)**: `web/public/sitemap.xml` is generated from the master each
  render. Submit it in Search Console. (A root `robots.txt` only helps once a
  custom domain serves the site at root — a project Pages subpath ignores it.)
- **Incremental render (done)**: composing the branded share-cards (`og.py`, PIL)
  is the dominant render cost, so `_write_pages` memoizes them — a card is rebuilt
  only when its inputs change (name, dates, portrait bytes, or brand), keyed by a
  content hash in `.cache/og-cards.json` (gitignored, not deployed). HTML is cheap
  and always rewritten. Warm renders are ~8× faster (585 cards: ~34s → ~4s). CI
  restores the cards + manifest via `actions/cache` (key tracks config + master),
  so a clean checkout doesn't regenerate everything. This is the headroom that
  keeps render cheap as the catalogue grows.
- **Vendored photos (done)**: `extract/photos.py` downloads each portrait once
  (through the proxied session, since images sit behind the same Cloudflare),
  downscales to ~450px JPEG, and saves it to `web/public/assets/photos/<slug>.jpg`,
  committed alongside the master. Vendoring runs in the sync phase, capped at
  `PER_RUN_LIMIT` per run so a first-run backlog drains over a few runs; render
  prefers the local copy and falls back to the remote URL for anything not yet
  vendored. The widget's `photoSrc` prepends the base path for these repo-relative
  photos.
- **Cross-post dedupe (done)**: `main._dedupe_people` collapses the same person
  (name + death date) appearing in two posts to one canonical record for the
  index/feed/home pages/sitemap (the fullest body wins); the duplicate page still
  renders but `rel=canonical`s at its primary, so no URL 404s and ranking isn't
  split.
- **Robustness (done)**: `wp_client._get` retries the fetch with exponential
  backoff (the Anthropic client also retries); `extractor.sanity_warnings` logs
  implausible dates/ages (non-fatal); `extract/test_pipeline.py` is a no-dep
  regression suite run in CI before the extract step (a broken build never
  deploys).
- **Open follow-up**: **Soft-failure deploys** — today any per-post failure skips
  the deploy that run; a follow-up could deploy the good catalogue and surface
  failures via a separate red report job.
- **Editorial controls** (`data/`, documented in `data/README.md`):
  `manual.json` adds hand-entered obituaries that don't come through the WPR
  batches (a stray notice, an out-of-town home) — each becomes a full page, merged
  at render; `suppressed.json` omits a page by slug on request (the record stays
  in the master but is dropped from the site, index, and sitemap). Both are
  committed and applied at render. `data/intake/<id>.json` is the **reviewed
  submission path** (the intake write-source, `data/intake/README.md`): approved
  files flow through *sync* into the master (deduped + vendored like scraped
  obits), and the widget's SubmitForm composes a prefilled email to the
  submissions address to start one. `manual.json` is the quick hatch; intake is
  the reviewed, universal path. The register draws from these funeral homes: Brainard,
  Helke, Peterson/Kraemer, Schmidt & Schulta (Wittenberg), John J. Buettgen +
  Mid-Wisconsin Cremation Society, and Ascend (Weston). Submissions go to
  darren@wausaupilotandreview.com (shown in the masthead).
- **Front-end brand**: the widget (`web/src/index.css`) and the per-person pages
  (`extract/templates.py`) share one WPR newsroom type system — **Oswald** for
  the nameplate/labels (WPR's heading face), **Merriweather** for names and body
  (WPR's reading serif), and **Courier Prime** as the typewriter accent for
  datelines and metadata — on a warm newsprint palette with an oxblood accent
  (`#7c2e36`). Keep the two surfaces visually in sync. `--render-only` reaches
  every existing page after a brand/template change (no API needed).

## v2 (deferred, by decision)

Condolences / guestbook. Drives return visits but needs Supabase plus active
moderation, and grief content attracts abuse. Ship the index first; add the
guestbook once the editorial side is ready to moderate.

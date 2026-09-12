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
   never invents detail (`clean_summary` strips the one placeholder it has
   been seen to narrate — "of an unspecified town" — so an absence is never
   published as a fact). `wp_client` + `extractor` are wrapped by
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
   fetch window. It is committed to the repo and grows over time. Each record
   carries a `source` stamp (applied at upsert) so record ownership is
   namespaced per write-source, and a **persisted `slug`** that is carried
   forward across re-extractions — a correction (a death year the first pass
   missed, a fixed middle initial, an added nickname) can never move a
   published URL: one-person units carry the slug unconditionally, multi-person
   batches match people by first + last name (`models.name_key`, shared with
   the cross-source dedupe).
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
   only. It fetches the JSON index and links each card to the static page. The
   name search is the product: it sits directly under the lede, matches by
   name-token prefix (`lib/search.js` — "Allan Jensen" finds Allan Guy
   Jensen; diacritics folded; records that only *mention* the query list in a
   second tier), and the register is grouped by **date of death** (`eventDate`,
   falling back to the publication date for the 2% without one) with honest
   "Died …" / "Published …" headings. Browse (month / last name, with town /
   home behind a second-tier line) is a secondary path behind one disclosure.
   The search or filter mirrors into the widget's URL (`lib/urlState.js`:
   `?q=`, `?month=`, `?letter=`, `?town=`, `?home=`, validated on read) so Back
   from a person page and a shared link reopen the same list; embedded, the
   same search string is posted to the parent (`wpr-obituaries:state`) and the
   embed snippet mirrors it onto the WordPress URL and forwards it back into
   the iframe on load. The sponsor logos ride in the masthead as a
   "presented by" line above the ink rule (the footer card is the full-size
   placement), so nothing sits between the search and its results; the
   featured strip (five of the week's portraits, newest first) is hidden on
   phones. Vite
   builds **two embeds** from this one app: `index.html` (the full register,
   paginated 60 rows at a time — "Show earlier obituaries" — so the embed's
   height and portrait loads stay bounded as the catalogue grows) and
   `mini.html` (a compact article/sidebar carousel — `MiniWidget.jsx`, flips
   through recent obituaries, carries the sponsor logos, links back to the full
   page via `?link=`, http(s)-validated; it fetches the small `data/recent.json`
   feed, never the full index). Both post their height to the parent
   (`lib/frame.js`, measured from `body.offsetHeight` so the frame can shrink
   as well as grow); copy-paste snippets + a live `embed-test.html` harness are
   in `docs/embedding.md`.
7. `.github/workflows/extract.yml` — cron Mon/Wed/Fri 6 AM Central. Runs sync +
   render, commits the updated master back (`contents: write`), then builds the
   widget and deploys to Pages. Quarantined units (exit 2) still deploy the rest
   and go red in a separate `report` job; a crashed extract (exit 1) skips the
   deploy (the last good deploy stays live) but still persists the master.

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
  `https://obituaries.wausaupilotandreview.com` (the brand subdomain; set as an
  Actions variable). The old `rowanflynnpilot.github.io/wpr-obituaries` URLs
  301-redirect here.

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

`web/vite.config.js` `base` must match the serving path — it is `/`, since the
site serves from the custom-domain root (`obituaries.wausaupilotandreview.com`).
A Pages project sub-path would instead need `/wpr-obituaries/`.

Funeral-home scraping (`adapters.funeral_home_scrape`, `windowDays` in config)
reads the homes' own sites directly. Per-home scrape config lives in
`data/funeral_homes.json` (`platform` + its key). Two platforms are wired:
**Tukios** (nine homes, keyed by `siteAlias`, JSON API — Buettgen and Mid-Wisconsin
migrated here from Tribute in Sept 2026) and **Tribute
Technology** (two homes, keyed by `url`; the RSS `pubDate` decides what is
recent, the sitemap `lastmod` — which moves on edits — is the unit revision so
corrections re-extract; `lastmod` alone can't window, the platform bumps it on
decades-old entries; + `Person` JSON-LD). The
scraped-home list is also the republication permission list — full details, both
platforms' mechanics, and the cross-source dedupe/overlap note are in
`docs/funeral-home-scraping.md`.

## Known decisions and open items

- **Duplicate content**: per-person pages reproduce the full obit text, which
  overlaps the original batch posts. Each page is self-canonical with unique
  title/H1/URL + schema, so it should win on specificity; the WordPress-side
  playbook (sitemap, batch-post linking, when to trim batch posts) is in
  `docs/seo-batch-posts.md`.
- **SEO domain (done)**: the site serves from `obituaries.wausaupilotandreview.com`
  (Cloudflare `CNAME obituaries → rowanflynnpilot.github.io`, **proxied** —
  orange-cloud, not DNS-only; Pages custom domain + enforced HTTPS; `base: "/"`;
  `PUBLIC_BASE_URL` variable set to the subdomain). Ranking equity now accrues
  to the brand domain and the old `github.io/wpr-obituaries` URLs 301-redirect
  here. Because the subdomain is proxied, Cloudflare's zone settings apply:
  managed content signals **rewrite robots.txt in flight** (AI crawlers hard-
  blocked; Google search still allowed) and plain non-browser fetchers get 403.
  Runbook + what to verify in Search Console: `docs/custom-subdomain.md`.
  Follow-ups: re-submit the sitemap in Search Console under the new domain, and
  confirm Googlebot crawl health there (Cloudflare bot rules over Pages is
  where over-blocking would silently cost rankings).
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
- **Vendored photos (done)**: `extract/photos.py` downloads each portrait
  (through the proxied session, since images sit behind the same Cloudflare),
  downscales to ~450px JPEG, and saves it to `web/public/assets/photos/<slug>.jpg`,
  committed alongside the master. A manifest (`data/photos.json`, slug → source
  URL) makes a portrait *corrected upstream* re-vendor instead of staying stale,
  and a portrait *removed* upstream is deleted locally on the next sync;
  suppressed records are never vendored, manual one-offs are. Vendoring runs in the sync phase,
  capped at `PER_RUN_LIMIT` per run so a first-run backlog drains over a few
  runs; render prefers the local copy and falls back to the remote URL for
  anything not yet vendored. The widget's `photoSrc` prepends the base path for
  these repo-relative photos.
- **Cross-post dedupe (done)**: `main._dedupe_people` collapses the same person
  (name + death date) appearing in two posts to one canonical record for the
  index/feed/home pages/sitemap (the fullest body wins); the duplicate page still
  renders but `rel=canonical`s at its primary, so no URL 404s and ranking isn't
  split.
- **Robustness (done)**: `wp_client._get` retries the fetch with exponential
  backoff (the Anthropic client also retries); `extractor.sanity_warnings` logs
  implausible dates/ages (non-fatal); a source's *discovery* failure is
  quarantined like a per-unit failure (other sources still sync, the master
  still saves); `save_master` writes atomically; the cron's commit-back push
  rebases + retries so a human push mid-run can't reject it; runs are queued,
  never cancelled (`cancel-in-progress: false` — a cancelled run loses paid
  extractions or a staff submission); `extract/test_pipeline.py` is a no-dep
  regression suite run in CI before the extract step (a broken build never
  deploys).
- **Soft-failure deploys (done)**: `main.py` exits **2** when units were
  quarantined but the render succeeded; the workflow deploys the good catalogue
  and a separate `report` job goes red with `data/failures.json` (handed over as
  a workflow artifact — the file is gitignored build state, never on `main`), so
  a persistently broken upstream page can never hold the catalogue hostage. Exit
  1 (an exception) still skips the deploy. Inside the funeral-home source, one
  home's feed being down is isolated too: the other homes still yield, and the
  outage is raised once, after the loop.
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
  The WPR fleet's brand invariants (see the `wpr-brand` skill) are applied on
  every surface: the **flag** (press seal beside the wordmark, one link home,
  the tagline beneath) closed by a **thick-over-thin rule in ink** with the
  tool's own title always *below* it; a **colophon** (seal + provenance line +
  `name · phone — tagline`) at the foot of the widget and every static page;
  and paid sponsor links carrying `rel="noopener sponsored"` plus UTM tags
  (`sponsor_href` in Python, `lib/sponsor.js` in the widget, same params).
  Accent-topped cards are square-cornered (the house convention marks cards on
  the top edge only). The tagline, phone, and provenance are optional config
  keys (`identity.tagline`, `identity.phone`, `copy.provenance`); absent = hidden.

## v2 (deferred, by decision)

Condolences / guestbook. Drives return visits but needs Supabase plus active
moderation, and grief content attracts abuse. Ship the index first; add the
guestbook once the editorial side is ready to moderate.

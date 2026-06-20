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
   widget). Fails loudly if `WEBSHARE_PROXY_URL` is unset.
2. `extract/extractor.py` — Claude Haiku reads each batch post and returns one
   structured record per person. Regex parsing is wrong here: obituary
   formatting varies too much. The model extracts only what is present and
   never invents detail.
3. `extract/templates.py` — renders one crawlable HTML page per person plus a
   `sitemap.xml`. **This is the SEO layer.** Each page has the name in the title
   and H1, schema.org `Obituary` structured data, canonical, and OG tags.
4. `extract/store.py` — the **persistent master** (`data/obituaries_master.json`,
   `{posts, records}`). This is the source of truth that lets pages outlive the
   fetch window. It is committed to the repo and grows over time.
5. `extract/main.py` — two phases:
   - **Sync** (skipped by `--render-only`): fetch the window, extract only *new
     or changed* batch posts (`posts` map tracks each processed post id by its
     `modified_gmt`), and upsert them into the master. Per-post failures are
     quarantined to `data/failures.json` and exit the run non-zero, but the
     master is still saved first — no silent gaps, no lost catalogue.
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

Environment (extractor):

- `ANTHROPIC_API_KEY` — for Haiku extraction.
- `WEBSHARE_PROXY_URL` — e.g. `http://user:pass@proxy.webshare.io:80`.
- `PUBLIC_BASE_URL` — where pages are served and indexed. **Required, no
  default**, because the canonical URL must point at the real location.
  Currently `https://rowanflynnpilot.github.io/wpr-obituaries` until a custom
  subdomain is in place.

The single anchor sponsor lives in `web/public/data/sponsor.json`:
`{ "name", "url", "logo", "tagline" }`. `name` + `url` are required; `logo`
(repo-relative path, e.g. `assets/peterson-kraemer.png`, served identically by
the widget and the static pages) and `tagline` are optional and drive the
sponsor card. Vendor the logo under `web/public/assets/` rather than hotlinking
the sponsor's CDN. Swap it all there — no code change. This is the "one premium
check" sponsorship model; per-funeral-home attribution still appears as
arrangement metadata on each record.

`web/vite.config.js` `base` must match the serving path
(`/wpr-obituaries/` for a Pages project site, `/` for a custom domain root).

## Known decisions and open items

- **Duplicate content**: per-person pages reproduce the full obit text, which
  overlaps the original batch posts. v1 sets each page canonical to itself. The
  clean follow-up is to manage `rel=canonical`/noindex on the WP batch posts so
  the per-person pages own the ranking. Not solved in v1.
- **SEO domain**: pointing `obituaries.wausaupilotandreview.com` at Pages keeps
  ranking equity on the brand domain. Recommended before heavy promotion.
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
- **Open follow-ups**: (a) **cross-post dedupe** — the slug keys on the source
  post, so the same person in two posts (notice + full obituary) yields two
  pages; needs an identity key (name + dates). (b) **Vendor photos** — portraits
  still hotlink WPR's Cloudflare CDN. (c) **Fetch retries** — `wp_client` has no
  backoff yet (the Anthropic client now retries). (d) **Soft-failure deploys** —
  today any per-post failure skips the deploy that run; a follow-up could deploy
  the good catalogue and surface failures via a separate red report job.
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

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
3. `extract/templates.py` — renders one crawlable HTML page per person. **This
   is the SEO layer.** Each page has the name in the title and H1, schema.org
   `Obituary` structured data, canonical, and OG tags. Google ranks these.
4. `extract/main.py` — orchestrates fetch → extract → dedupe → write. Outputs:
   - `web/public/data/obituaries.json` (light index for the widget)
   - `web/public/o/<slug>.html` (per-person pages)
   Any post that fails to parse aborts the run with exit 1 — no silent gaps.
5. `web/` — React 18 / Vite memorial register. The **browse + search** layer
   only. It fetches the JSON index and links each card to the static page.
6. `.github/workflows/extract.yml` — cron Mon/Wed/Fri 6 AM Central, then
   builds the widget (which bundles the static pages) and deploys to Pages.

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
- **Backfill cost**: `python extract/main.py --backfill` parses every obituary
  post ever published (one Haiku call per post). The default run uses a recent
  window (`WINDOW_DAYS` in `main.py`) for the cron — bounded cost. Currently set
  to **14 days** while runs are being tuned; the intended steady-state is 45.
  Note the index is rebuilt from only that window each run (it does not
  accumulate), so the register shows exactly the trailing window of names.
- **Sitemap**: not yet generated. A `sitemap.xml` of the per-person pages would
  speed up indexing; add to `main.py` when ready.
- **Front-end brand**: the widget (`web/src/index.css`) and the per-person pages
  (`extract/templates.py`) share one WPR newsroom type system — **Oswald** for
  the nameplate/labels (WPR's heading face), **Merriweather** for names and body
  (WPR's reading serif), and **Courier Prime** as the typewriter accent for
  datelines and metadata — on a warm newsprint palette with an oxblood accent
  (`#7c2e36`). Keep the two surfaces visually in sync. A template change only
  reaches already-published `o/*.html` pages on the next `main.py` run, since the
  full body text needed to re-render lives only in the source posts.

## v2 (deferred, by decision)

Condolences / guestbook. Drives return visits but needs Supabase plus active
moderation, and grief content attracts abuse. Ship the index first; add the
guestbook once the editorial side is ready to moderate.

# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primary: the searcher.** Someone in the Wausau / Marathon County area — often
grieving, often older, often on a phone — who googles a name (or opens the
obituaries page on wausaupilotandreview.com) to find the right notice, read it,
and share it with family. When priorities conflict, this user wins.

Other confirmed audiences, in order:

- **The newsroom** (Wausau Pilot & Review staff; submissions go to Darren).
  Publishes obituaries free of charge Mon/Wed/Fri, sells the anchor
  sponsorship, and approves intake submissions. Wants the section to run
  itself: little editorial time, no lost notices, a visible failure when an
  upstream source breaks.
- **Funeral homes and families.** The eleven area homes the newsroom has an
  arrangement with are read directly; families and homes without a feed
  submit through the widget's prefilled email → reviewed intake path.
- **Sponsors** (currently Helke and Brainard, co-owned). Judge the placement
  by pageviews-as-impressions and click-through per placement.

## Product Purpose

Turn WPR's hand-compiled daily batch obituary posts — where every person is
buried inside one long post — into individually addressable, crawlable,
permanent pages plus a searchable register embedded on the newsroom's site.
The whole point is **individual discoverability**: when someone searches
"<name> obituary Wausau" they should land on WPR, not on a national aggregator.

Success is judged on three things (confirmed):

1. **Search rankings** — name searches land on WPR (Search Console
   impressions/clicks on the brand subdomain).
2. **Sponsor revenue** — the anchor sponsors renew because the placement is
   demonstrably worth it (pageviews as impressions, per-placement click-through).
3. **Reader sharing** — families share the pages (Facebook, email, print /
   "Save as PDF") and treat them as the keepsake copy.

Editorial time saved is a benefit, not a success measure.

## Positioning

**Local, permanent, free.** Every area obituary as its own permanent page on
the local newsroom's domain (`obituaries.wausaupilotandreview.com`), published
free of charge, sourced from the funeral homes themselves and from the
newsroom's own notices — not a paywalled national aggregator (Legacy.com), not
a single home's site that only lists its own clients, not a WordPress category
that buries names in batch posts. A published page never moves and never
disappears.

Secondary (real but not first-class for design decisions): the codebase is a
forkable, config-driven template another small newsroom can own outright —
the WPR instance is the reference deployment for that story.

## Operating Context

- Embedded on wausaupilotandreview.com (WordPress/Newspack) as two iframes: the
  full register on the Obituaries page and a compact carousel in articles /
  the sidebar. The static per-person pages are what search engines index; the
  iframe is only the browse surface.
- Runs unattended on a Mon/Wed/Fri GitHub Actions cron: sync (three
  write-sources — WPR batch posts via Claude Haiku extraction, funeral-home
  sites via the Tukios API and Tribute Technology feeds, reviewed intake
  files) → persistent master → render everything → deploy to GitHub Pages.
  Quarantined failures still deploy the good catalogue and report red.
- The subdomain sits behind Cloudflare (proxied); its zone rules rewrite
  `robots.txt` and block non-browser fetchers. Search Console is the source of
  truth for crawl health.
- Staff tools: a staff-only submit form and a funeral-home onboarding page
  (both unlinked, `noindex`), and the `data/` editorial files (manual entries,
  suppressions, intake).
- Catalogue: ~1,360 records and growing forever; ~11 funeral homes scraped
  (nine on Tukios, two on Tribute Technology), the list doubling as the
  republication-permission list.

## Capabilities and Constraints

- One record contract for every source; per-person pages with schema.org
  `Obituary` data, canonical, OG/Twitter tags, a branded 1200×630 share card,
  a vendored portrait, share/print controls, related links, and a colophon.
- Register: search (name, town, funeral home), browse by month / letter /
  town / home, paginated rows, submit-an-obituary form.
- Slugs are persisted: a correction can never move a published URL.
- Suppression by slug on family request; the record stays in the master.
- Content is third-party text (extracted, scraped, submitted) — always
  escaped, never trusted.
- No API keys are needed for an intake-only fork; scraping needs the Haiku
  key and a residential proxy.
- **Undecided / deferred:** condolences / guestbook (v2, needs moderation and
  a backend); a hosted intake backend (shelved in favour of the file-based
  path); retiring the WordPress batch scrape once the homes are fully covered.

## Brand Commitments

Wausau Pilot & Review's identity is binding (see the `wpr-brand` skill and
CLAUDE.md's front-end brand section): the press-seal + wordmark flag with the
tagline "Where Locals Look First For News" and a thick-over-thin newspaper
rule; the Newspack "Joseph" type pairing (Oswald nameplate, Merriweather
reading serif, Courier Prime as the typewriter accent) on a warm newsprint
palette; an oxblood accent (`#7c2e36`) chosen for a memorial surface in place
of the site's teal; the "In Memoriam" kicker; a colophon with provenance and
`Wausau Pilot & Review · 715-301-5539`. Paid sponsor links carry
`rel="sponsored"` and UTM tags. Tone is dignified and restrained — this is a
grieving family's first touchpoint. All identity strings and assets live in
`newsroom.config.json` and `web/public/data/sponsor.json`, never in code.

## Evidence on Hand

- The live site and its real catalogue (`data/obituaries_master.json`,
  vendored portraits under `web/public/assets/photos/`).
- Sponsor logos (`web/public/assets/helke.png`, `brainard.png`) and the WPR
  wordmark/seal (`web/public/assets/wpr-logo.png`, `wpr-seal.png`).
- Runbooks and design records in `docs/` and `CLAUDE.md`.
- **Not on hand — do not fabricate:** testimonials, traffic or ranking
  numbers (Search Console is the source; none are recorded here), sponsor
  pricing, submission volumes.

## Product Principles

1. **The name search is the product.** Every decision is judged by whether a
   grieving searcher finds and trusts the right page faster.
2. **A published page is permanent.** URLs never move; the catalogue only
   grows; corrections and upstream changes are absorbed, never exposed.
3. **Dignity over delight.** Restraint in motion, colour, and copy; nothing
   that would feel wrong on a memorial.
4. **One correct path, fail loudly.** No fallbacks; a broken precondition is
   an error, an absent optional fact is null; failures are quarantined and
   visible, never silent.
5. **The newsroom owns it.** Config-driven identity, committed data, no
   central service — the same tool is a template any newsroom can run.

## Accessibility & Inclusion

The audience skews older and is often reading in distress. The working bar
applied throughout is WCAG 2.1 AA: measured text contrast on the newsprint
ground, visible focus rings on every control, touch-reachable pause for
auto-advancing content, screen-reader announcements for loading and
pagination, reduced-motion honoured in CSS and JS, and a print layout that
reads as a keepsake. No formal standard has been mandated by the newsroom;
AA is the floor this repo holds itself to.

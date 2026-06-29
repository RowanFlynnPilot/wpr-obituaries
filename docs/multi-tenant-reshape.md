# Multi-tenant reshape: WPR tool → forkable newsroom template

Turn the WPR-specific obituary tool into a template another local newsroom can
fork, rebrand, and run — without touching code. Distribution model is
**template-fork** (each newsroom gets its own repo, config, Pages site, and
intake), which is what the static-pages + git-committed-master architecture
already wants.

## Guiding constraint

Each step is validated against one acceptance check: after the config/branding
extraction, `python extract/main.py --render-only` produces **byte-identical**
output to before (the config's defaults *are* the WPR values). That proves
constants were relocated, not behavior changed. WPR keeps working at every step.

## The config contract

One declarative `newsroom.config.json` at the repo root, read by **both**
runtimes — Python (`extract/config.py`) and Vite (`web/vite.config.js`, injected
at build time). Secrets never live here (API keys, proxy URL stay in env;
`PUBLIC_BASE_URL` stays in the deploy env because the canonical URL must point at
the real serving location). A missing required key raises immediately.

```
identity   { name, shortName, url, coverageArea, submissionsEmail }
branding   { logoUrl, sealPath, accent, paper, fontsUrl, serif, nameplate, mono }
copy       { lede, footerTagline }          # widget editorial copy
adapters   { wordpress_scrape{enabled,apiBase,categorySlug,windowDays},
             intake{enabled,backend} }
```

## Sequenced steps

- [x] **Step 0 — Config loaders.** `newsroom.config.json` + `extract/config.py`
  (`Newsroom` dataclass, validate + raise) + `web/src/config.js`.
- [x] **Step 1 — Python render side reads config.** Threaded a `newsroom` object
  through `render_person_page`, `render_home_page`, `render_feed`,
  `_structured_data`, and `og.render_card`. Replaced every WPR literal (name,
  logo, fonts, accent, schema.org publisher, OG card colors/text). The shared
  `:root` CSS vars come from config via `_root_vars_wide`.
  *Verified byte-identical across all 591 HTML/XML/JSON files.*
- [x] **Step 2 — React widget reads config.** `vite.config.js` reads the root
  JSON, injects it via `define` (`__NEWSROOM__`) and a **`pre`**
  `transformIndexHtml` (pre-order so `%FONTS_URL%` is replaced before Vite's
  decodeURI pass). `main.jsx` sets `--accent`/`--paper` as inline `:root` styles
  (win over index.css, no flash). Masthead/Footer read identity + copy.
  *Verified: dev render clean, production build passes, full rebrand smoke test
  (Acme County Times / blue accent) propagated with zero WPR leakage.*
- [ ] **Step 3 — Source-adapter seam.** Move `wp_client` + `extractor` into
  `adapters/wordpress_scrape.py` behind a single `fetch_new(master)` interface
  (internals untouched). `main.sync()` loops over enabled adapters. Namespace the
  master's `posts` processed-map key per source (`"wordpress_scrape:12345"`) so
  multiple sources can't collide — the one honest `store.py` change. Wire
  `windowDays`/`apiBase`/`categorySlug` from config.
- [ ] **Step 4 — Intake adapter, lightweight backend.** `adapters/intake.py`
  with a backend abstraction; `backend: "manual"` reads approved local JSON and
  emits `Obituary` records. Public React intake form → emits a PR / submission
  file reviewed at merge. CMS-agnostic; the path that generalizes to newsrooms
  without batch-post obits.
- [ ] **Step 5 — Supabase upgrade (opt-in tier).** `backend: "supabase"`:
  submissions table (pending/approved/rejected + payload + source), Auth, RLS,
  auth-gated review-queue React surface. Gated behind a newsroom enabling it.
- [ ] **Step 6 — Generalize deploy + bootstrap.** `extract.yml` already reads
  base URL from vars + secrets from secrets, so identity needs no workflow
  change. Add conditional Supabase secrets. New `scripts/bootstrap.py`: write
  config interactively → `gh` set secrets/vars → point subdomain.

## Notes / decisions

- `wordpress_scrape` is a WPR artifact (Newspack batch posts) and ships
  **disabled by default** in the template. Intake is the reusable path.
- `sponsor.json` and `funeral_homes.json` already live in the repo as
  per-newsroom data — part of the "what a fork edits" set, no code change.
- Intake backends: ship **lightweight (manual/PR) as default**, **Supabase as an
  opt-in upgrade** for newsrooms that will staff a moderation queue.

## Follow-up cleanup (deferred, low priority)

- The two near-duplicate `:root` CSS blocks (funeral-home page vs person page)
  differ only in whitespace; they could be unified once byte-identical is no
  longer the active proof.

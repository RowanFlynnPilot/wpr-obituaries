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
- [x] **Step 3 — Source-adapter seam.** Added `extract/adapters/` — `base.Unit`
  (the contract: `source`/`unit_id`/`modified`/`ref`/`extract()`), `wordpress_scrape`
  (lifts `wp_client` + `extractor` behind it, internals untouched), and a registry
  (`enabled_sources`) driven by the config `adapters` block. `main.sync()` now
  loops over enabled sources, source-agnostic. `store` namespaces the processed-map
  per source (`wordpress_scrape:12345`) with a v1→v2 on-load migration; the
  committed master was migrated in this PR. `apiBase`/`categorySlug`/`windowDays`
  come from config. *Verified: render still byte-identical, tests pass (incl.
  migration + namespacing), sync loop smoke-tested without network (extract,
  skip-unchanged, re-extract-on-revision, failure quarantine, enabled_sources).*
- [x] **Step 4 — Intake adapter, lightweight backend.** `adapters/intake.py`
  (`IntakeManual`) reads approved `data/intake/<id>.json`, maps each to an
  `Obituary` (shared `Obituary.from_submission`, also now used by `load_manual`),
  and emits via the Step-3 `Unit` contract — so approved submissions flow through
  sync→master (deduped, vendored, permanent). The unit revision is a content
  hash (edits auto-re-emit). Registered in `enabled_sources` behind
  `adapters.intake` (`backend: "manual"`; `supabase` raises until Step 5). WPR
  runs intake **alongside** wordpress_scrape; the template ships intake-only.
  Public **SubmitForm** widget composes a prefilled email to the submissions
  address (the lightweight, no-infra path). *Verified: tests pass (intake emit,
  pending-skip, hash-revision, enabled_sources); end-to-end submission→sync→
  master→page proven without network; render still byte-identical with no
  submissions; widget builds.*
- [ ] **Step 5 — Supabase upgrade (opt-in tier).** `backend: "supabase"`:
  submissions table (pending/approved/rejected + payload + source), Auth, RLS,
  auth-gated review-queue React surface. Gated behind a newsroom enabling it.
- [x] **Step 6 — Generalize deploy + bootstrap.** `scripts/bootstrap.py` writes
  + validates `newsroom.config.json` interactively (pure `make_config` with
  shared brand defaults, intake-only by default), and offers to set the
  `PUBLIC_BASE_URL` repo var via `gh` (secrets are printed for the user to set,
  never handled by the script). Made the template **run with no keys when
  intake-only**: the Anthropic client is built lazily inside `wordpress_scrape`
  (not at registry time), and `make_session` proxies only when
  `WEBSHARE_PROXY_URL` is set. `extract.yml` documents that the two scraper
  secrets are optional for intake-only forks. Fork quickstart in
  [`forking.md`](forking.md). *Verified: tests pass (incl. bootstrap config gen
  + loader validation); bootstrap CLI run end-to-end; intake-only config builds
  sources with the scraper secrets unset.*

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

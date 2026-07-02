# Funeral-home scraping (`funeral_home_scrape`)

WPR's daily batch obituary posts are compiled by hand from the area funeral
homes' own websites. This adapter goes one step **upstream** and reads those
homes directly, so the register can be fed without the manual batch step. It
runs alongside `wordpress_scrape` (see the overlap note below), behind the same
`Unit` seam as every other write-source.

## The two platforms

Every in-area home sits on one of two website platforms, with mirror-image
scraping characteristics:

| Platform | Homes | Discovery | Obituary body |
|---|---|---|---|
| **Tukios** | Brainard, Helke, Peterson/Kraemer, Ascend, Beste, Rembs, Taylor-Stine-Waid | JS-rendered listing, but a public JSON API enumerates everything | Fully structured in the API response |
| **Tribute Technology** (Frazer) | Schmidt & Schulta, Buettgen (honorone.com), Mid-Wisconsin, Carlson | Server-rendered listing + obituary sitemaps/RSS | Embedded JSON / JSON-LD in the person-page HTML |

**Both platforms are implemented**, and both serve fully structured records, so
there is *no model extraction* — one source record maps straight to one
`Obituary` in `adapters/funeral_home_scrape.py`. A home configured with any other
`platform` raises loudly rather than half-working.

- **Tukios** (keyed by `siteAlias`): discovery and records come from one JSON
  API — name, both dates, age, city, full text, portrait, permanent URL.
- **Tribute Technology** (keyed by the site `url`): discovery is the home's
  Recent-Obituaries RSS (`/rss.xml`), windowed by pubDate, or the obituary
  sitemaps for a `--backfill`; each person page carries a schema.org `Person`
  JSON-LD with the full obituary, both dates, and the portrait. Tribute has no
  structured city, so those records carry no town facet (summary is name + age +
  death date), and age is computed from the two dates.

Gunderson (Madison) and Conroe (Texas) appear in WPR only as one-off
out-of-town arrangements — they are **not** scraped; the manual `data/intake/`
path covers those.

## The Tukios API

```
GET https://websites.tukios.com/api/v1/obituaries?siteAlias=<alias>&page=<n>&per_page=<n>
Authorization: Bearer <token>
Accept: application/json
```

- The **bearer token** ships in the clear inside every Tukios site's obituary
  widget bundle — it is a public read key, not a secret, and lives as a constant
  in `extract/tukios.py`. If it ever stops working, re-read it from any Tukios
  home's `/obituaries` page (the value after `Authorization: Bearer` in the
  widget's requests) and update the constant.
- The response is a Laravel paginator (`total`, `last_page`, `next_page_url`,
  `data[]`), sorted by **date of death, newest first** — so a windowed poll
  stops as soon as it pages past the cutoff.
- Each record carries `display_name`, `date_of_birth`, `date_of_death`, `age`,
  `city`, `branch`, `obituary_text` (HTML), `public_url`, `default_image`, and
  `is_published`.

## Adding / maintaining a scraped home

Homes live in `data/funeral_homes.json`. A scraped home carries a `platform`
plus that platform's key:

```json
{ "name": "…", "url": "…", "match": ["…"], "platform": "tukios", "siteAlias": "7aacd58f" }
{ "name": "…", "url": "…", "match": ["…"], "platform": "tribute" }
```

Tukios needs the `siteAlias`; Tribute is keyed by the site `url` alone.

The easiest way to add one is the onboarding CLI, which does the detection,
verification, and (with `--write`) the edit for you:

```
python scripts/add_home.py https://www.example-fh.com          # detect + verify + print
python scripts/add_home.py https://www.example-fh.com --write  # also insert the entry
```

It fetches the home's obituaries page (in Python, because the fetch is
cross-origin and often Cloudflare-fronted — a browser can't make it), detects
the platform, verifies it (Tukios: the `siteAlias` returns obituaries from the
live API; Tribute: the RSS lists obituaries), and inserts a config line
preserving the one-home-per-line format. Review the derived `match` token — it
must be a lowercase substring of how the home names itself on its obituaries so
scraped records link to the canonical home.

From the browser (staff): `web/public/admin.html` (served at
`<base>/admin.html`, unlinked/`noindex`) is a staff page that runs the same
detection through the **`add-home.yml`** GitHub workflow and opens a PR. Sign-in
is the staff member's own GitHub fine-grained PAT with **Actions: read and
write** on the repo (a static site can't hold a shared credential, and the
detection fetch can't run client-side). Opening the PR needs "Allow GitHub
Actions to create and approve pull requests" enabled in repo Settings → Actions,
and `add-home.yml` must be on the default branch for the dispatch API to see it.

By hand: the **siteAlias** is an 8-hex-char key printed in the home's
`/obituaries` page source as `siteAlias = '…'` or `SiteAlias: '…'` (it is *not*
the `login?site_id=` value); `tukios.find_site_alias()` extracts it. A Tribute
home just needs `platform: "tribute"` and its `url`. A home without `platform` is
name-canonicalized only, never scraped. The current scraped set is the seven
Tukios homes plus four Tribute homes (Schmidt & Schulta, Buettgen, Mid-Wisconsin,
Carlson).

The list of scraped homes doubles as the **republication permission list** —
only add a home the newsroom has an arrangement with.

## Idempotency, windowing, overlap

- Each obituary is one work-unit, keyed by a stable id hashed from its permanent
  `public_url`; the revision stamp is a content hash of the published fields, so
  an edited obituary re-emits automatically (same pattern as intake).
- `adapters.funeral_home_scrape.windowDays` (config) bounds the poll by date of
  death. A late-*published* obituary for an older death can fall outside a short
  window; the window is set generously (45 days) for that reason, and the WPR
  batch still backstops it. `--backfill` ignores the window and walks the full
  catalogue.
- **Cross-source overlap:** because WPR's batch posts are built from these same
  homes, a person can appear from both `wordpress_scrape` and
  `funeral_home_scrape`. The render-time dedupe (`main._dedupe_people`, by name +
  death date) already collapses them to one canonical record for the index and
  register; the duplicate page still renders but `rel=canonical`s at the primary,
  so no URL 404s and ranking isn't split. Dedupe matches on exact name, so a
  middle-name difference between the two sources can slip through as two entries
  — a known limitation, not fixed here. Longer term, once the scraper covers a
  home fully, its WPR batch coverage becomes redundant and `wordpress_scrape`
  could be retired — but that is a separate decision.

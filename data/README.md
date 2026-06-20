# Editorial data

These files are the human-controlled inputs to the obituary site. They are
committed to the repo and read on every build. After editing any of them, the
site updates on the next run of the workflow (or locally via
`python extract/main.py --render-only`).

## `obituaries_master.json` — generated, do not hand-edit
The accumulating source of truth, built automatically from the WPR batch posts.
Each run adds new people and never drops old ones. Hand edits here are
overwritten; use the two files below instead.

## `suppressed.json` — omit an obituary
A list of pages to **never publish** (e.g. a family asked us not to). The page
stays in the master for the record, but is removed from the site, the search
index, and the sitemap.

Find the slug in the page's URL — `…/o/<slug>.html` — and add it:

```json
[
  { "slug": "jane-a-doe-2026-1a2b3c", "reason": "family request, 2026-06-20" }
]
```

A bare `"jane-a-doe-2026-1a2b3c"` string works too; the `reason` is just for us.

## `manual.json` — add an obituary by hand
For one-offs that don't come through the WPR batch posts (a stray notice, an
out-of-town funeral home). Each entry becomes its own page just like the
scraped ones. Only `name` and `source_date` are required:

```json
[
  {
    "name": "John Q. Public",
    "source_date": "2026-06-20",
    "death_year": 2026,
    "birth_date": "1945-03-02",
    "death_date": "2026-06-15",
    "age": 81,
    "funeral_home": "Taylor-Stine Funeral Home",
    "photo_url": null,
    "summary": "John Q. Public, 81, of Merrill, died June 15, 2026.",
    "body": "Full obituary text here.\n\nSeparate paragraphs with a blank line."
  }
]
```

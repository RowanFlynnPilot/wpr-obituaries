# SEO: making the per-person pages win (WordPress side)

The per-person pages (`/o/<name>.html`) are what we want ranking for
"`<name>` obituary Wausau". But each one reproduces text that also appears in the
daily batch post on WordPress ("Wausau area obituaries June 19, 2026"). That's
*duplicate content*, and if Google decides the batch post is the canonical
version, the per-person page can be dropped from results — exactly the opposite
of what we want.

The per-person pages already send strong "I'm the canonical for this person"
signals: the name in the `<title>`, `<h1>`, and URL; a self-referencing
`rel=canonical`; `schema.org/Obituary` structured data; and now a sitemap and
social cards. So in most cases they should win on specificity. The steps below
lock that in.

## Do these now (low effort, no workflow change)

1. **Submit the sitemap in Google Search Console.**
   Add the property, then Sitemaps → submit `…/sitemap.xml`. This is the single
   highest-leverage action — it gets all per-person pages discovered and indexed
   fast. (Use the custom subdomain URL once it's live — see `custom-subdomain.md`.)

2. **Leave the batch posts indexed.** Don't `noindex` them — they have their own
   value (people search "wausau obituaries this week"). They don't compete
   URL-for-URL with the per-person pages; they compete only on name queries,
   where the more specific per-person page should win.

3. **Confirm Yoast/Newspack isn't overriding canonicals.** In the SEO plugin,
   make sure batch posts canonical to *themselves* (the default) — not to a
   category or anything else. Per-person pages are static HTML and already
   self-canonical; nothing to change there.

## If duplication actually hurts (monitor first)

In Search Console → Pages, watch for per-person URLs excluded as
**"Duplicate, Google chose different canonical than user"** pointing at a batch
post. If that shows up at scale, escalate in this order:

1. **Link batch posts → per-person pages.** In each batch post, link each
   person's name/heading to their `/o/<slug>.html` page (or add a "Read the full
   obituary" link). This passes authority to the per-person page and tells Google
   which URL owns the content. Lowest-friction real fix.

2. **Trim the batch posts to blurbs.** Publish only a short notice per person in
   the batch post (name, age, town, service info) plus the "Read the full
   obituary" link, so the *full* text lives only on the per-person page. This
   removes the duplication at the source and is the strongest fix — but it
   changes the newsroom's posting format, so only do it if step 1 isn't enough.

## Note on the embed

The React widget is an `<iframe>`; search engines don't credit the parent page
for links inside an iframe. So discovery of the per-person pages relies on the
**sitemap** (step 1) and any **direct links** on the WordPress obituaries page —
not on the embedded widget. The widget is for humans; the sitemap is for crawlers.

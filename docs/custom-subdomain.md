# The brand subdomain: obituaries.wausaupilotandreview.com

Serving the tool from the brand domain (instead of `rowanflynnpilot.github.io`)
keeps all ranking equity on Wausau Pilot & Review, looks professional in shares,
and lets a real `robots.txt` work at the domain root.

**Status: done.** This is now a runbook — the record of how the WPR migration
was applied, and the path a fork follows for its own subdomain
(`scripts/bootstrap.py` and `docs/forking.md` reference these steps).

## What was applied

1. **DNS** (at the host for `wausaupilotandreview.com`) — one record:

   ```
   Type:  CNAME
   Name:  obituaries
   Value: rowanflynnpilot.github.io
   ```

   Note: the record sits behind Cloudflare and is currently **proxied**
   (orange-cloud), not DNS-only. That means Cloudflare's zone settings apply to
   the subdomain — see "Cloudflare proxy effects" below.

2. **Repo** — `web/public/CNAME` contains exactly
   `obituaries.wausaupilotandreview.com`, and `web/vite.config.js` has
   `base: "/"` (the site serves from the domain root; a project sub-path would
   need `/<repo>/` instead).

3. **Actions variable** — `PUBLIC_BASE_URL` is
   `https://obituaries.wausaupilotandreview.com`. It flows into every page's
   canonical, OG/Twitter tags, the sitemap, the share cards, and the per-person
   photo/OG URLs on each run.

4. **GitHub Pages** — Settings → Pages → Custom domain set to the subdomain,
   with **Enforce HTTPS** on. The old `…github.io/wpr-obituaries/` URLs
   301-redirect to the subdomain, so previously indexed/shared links keep
   working.

## Cloudflare proxy effects (verify periodically)

Because the CNAME is proxied, Cloudflare rewrites what crawlers see:

- **`robots.txt` is rewritten in flight.** The repo-rendered file still appears
  at the end, but Cloudflare's "managed content signals" block is prepended —
  including hard `Disallow: /` rules for AI crawlers (ClaudeBot, GPTBot, CCBot,
  Bytespider, Google-Extended, …). Google *search* remains allowed
  (`search=yes`, Googlebot not blocked), so rankings are unaffected as long as
  that stays true.
- **Bot blocking returns 403** to plain (non-browser) HTTPS fetchers.

Both are zone-wide WPR settings, not something this repo controls. The check
worth repeating after any Cloudflare settings change: Search Console → URL
Inspection / Crawl stats, confirming Googlebot fetches succeed. Over-aggressive
bot rules in front of GitHub Pages is exactly where rankings silently erode.

## Standing follow-up

- **Re-submit the sitemap** in Search Console under the subdomain property (if
  not already done) and keep the property on the subdomain, not the github.io
  host.

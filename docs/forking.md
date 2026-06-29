# Forking this template for a new newsroom

This repo is a template: a second local-news organization can stand up its own
searchable, SEO-ranking obituary site without touching code. One file
(`newsroom.config.json`) holds the identity and branding; everything else is
shared. The architecture and the seams are described in
[`multi-tenant-reshape.md`](multi-tenant-reshape.md).

## Quick start

1. **Fork / "Use this template"** on GitHub, then clone.
2. **Run the bootstrap script** — it writes and validates `newsroom.config.json`:

   ```
   python scripts/bootstrap.py
   ```

   It asks for your name, short name, URL, coverage area, submissions email,
   logo URL, and accent color. The shared newsprint type system (Oswald /
   Merriweather / Courier Prime) is the default; edit the `branding` block
   afterward if you want a different look.

3. **Drop in your assets**: a masthead seal at `web/public/<branding.sealPath>`
   and your sponsor logos referenced from `web/public/data/sponsor.json`.
4. **Set the Pages URL** (the bootstrap can do this if `gh` is installed):

   ```
   gh variable set PUBLIC_BASE_URL --body https://<you>.github.io/<repo>
   ```

5. **Enable GitHub Pages** (Settings → Pages → GitHub Actions) and run the
   **Build and deploy obituaries** workflow.

## Sources

The template ships **intake-only**: families and funeral homes submit obituaries
through the widget's "Submit an obituary" form, an editor approves them as
`data/intake/<id>.json`, and they publish on the next run. This path works for
any newsroom and needs **no API keys** — see [`../data/intake/README.md`](../data/intake/README.md).

Enable the **WordPress scraper** (`adapters.wordpress_scrape.enabled`) only if,
like WPR, you publish batch obituary posts in an `obituaries` category. It needs
two secrets:

```
gh secret set ANTHROPIC_API_KEY     # Haiku splits each batch post into people
gh secret set WEBSHARE_PROXY_URL    # only if your site is behind Cloudflare
```

then seed the back-catalogue once: `python extract/main.py --days 180`.

## Analytics (recommended)

Turning on analytics is what proves the section's value — pageviews are both your
traffic report *and* your sponsor-impression count (every page shows the
sponsor), and sponsor-logo clicks are tracked as events. All providers below are
cookieless, so no consent banner is needed. Set the `analytics` block in
`newsroom.config.json`:

```json
"analytics": { "provider": "plausible", "domain": "obituaries.yourpaper.com" }
```

- **plausible** — set `domain`. Supports sponsor-click events.
- **goatcounter** — set `site` (the `<code>` in `<code>.goatcounter.com`). Free; supports events.
- **cloudflare** — set `site` (the beacon token). Free; pageviews only.
- **custom** — set `headHtml` to your own `<script>` (any other provider).

Both the static obituary pages and the embedded widget report to the same
account. Leave `provider` empty to disable.

## Custom domain

Pointing a subdomain (e.g. `obituaries.yourpaper.com`) at Pages keeps SEO equity
on your brand domain. The DNS + repo steps are in
[`custom-subdomain.md`](custom-subdomain.md).

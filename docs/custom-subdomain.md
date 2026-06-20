# Moving to obituaries.wausaupilotandreview.com

Serving the tool from the brand domain (instead of `rowanflynnpilot.github.io`)
keeps all ranking equity on Wausau Pilot & Review, looks professional in shares,
and lets a real `robots.txt` work at the domain root.

These changes are **documented, not applied** — applying them before DNS is in
place would break the live site (it's currently served from the `/wpr-obituaries/`
sub-path). Do the steps in order.

## 1. DNS (at the host for `wausaupilotandreview.com`)

Add one record:

```
Type:  CNAME
Name:  obituaries
Value: rowanflynnpilot.github.io
```

Wait for it to resolve (`nslookup obituaries.wausaupilotandreview.com`).

## 2. Repo changes (a tiny PR — merge after DNS resolves)

- **Add `web/public/CNAME`** containing exactly:
  ```
  obituaries.wausaupilotandreview.com
  ```
- **`web/vite.config.js`** — change the base to the domain root:
  ```diff
  - base: "/wpr-obituaries/",
  + base: "/",
  ```
- **Update the `PUBLIC_BASE_URL` Actions variable** (repo Settings → Secrets and
  variables → Actions → Variables) to:
  ```
  https://obituaries.wausaupilotandreview.com
  ```
  This automatically flows into every page's canonical, OG/Twitter tags, the
  sitemap, the share cards, and the per-person photo/og URLs on the next run.

## 3. GitHub Pages settings

Settings → Pages → Custom domain → `obituaries.wausaupilotandreview.com` → Save,
then check **Enforce HTTPS** once the certificate is issued.

## 4. Deploy and verify

Run the workflow (Actions → Run workflow). Then confirm:
- `https://obituaries.wausaupilotandreview.com/` loads the widget,
- a per-person page's `<link rel="canonical">` uses the new domain,
- `https://obituaries.wausaupilotandreview.com/sitemap.xml` resolves.

## 5. Follow-ups

- **Re-submit the sitemap** in Search Console under the new domain.
- A root **`robots.txt`** (pointing at the sitemap) now works — add
  `web/public/robots.txt` if desired (it was ignored under the project sub-path).
- The old `…github.io/wpr-obituaries/` URLs will 404; if any were shared/indexed,
  that's fine for a fresh tool, but avoid promoting them once the subdomain is live.

# WPR Obituaries

A searchable, SEO-ranking obituary tool for Wausau Pilot & Review. Daily batch
obituary posts are split into individual, crawlable pages so name searches find
WPR first. A React widget provides browse and search; static per-person pages
do the ranking.

## Layout

```
extract/   Python pipeline: REST pull → Haiku extraction → persistent master → pages + sitemap
web/       React 18 / Vite memorial-register widget (the iframe embed)
data/      Committed source of truth: obituaries_master.json, plus manual.json / suppressed.json
.github/   Mon/Wed/Fri cron that extracts, commits the master, and deploys to GitHub Pages
```

## Prerequisites

- Python 3.12+
- Node 20+
- A Webshare residential proxy (WPR sits behind Cloudflare)
- An Anthropic API key

## Setup

```powershell
# Python deps
pip install -r requirements.txt

# Web deps
cd web; npm install; cd ..
```

Set the environment (PowerShell):

```powershell
$env:ANTHROPIC_API_KEY  = "sk-ant-..."
$env:WEBSHARE_PROXY_URL = "http://user:pass@proxy.webshare.io:80"
$env:PUBLIC_BASE_URL    = "https://rowanflynnpilot.github.io/wpr-obituaries"
```

Set the sponsors in `web/public/data/sponsor.json`:

```json
{
  "label": "Obituaries made possible by",
  "sponsors": [
    { "name": "Helke Funeral Home and Cremation Service", "url": "https://www.helke.com", "logo": "assets/helke.png" },
    { "name": "Brainard Funeral Home and Cremation Center", "url": "https://www.brainardfuneral.com", "logo": "assets/brainard.png" }
  ]
}
```

## Run the extractor

```powershell
python extract/main.py               # recent window: extract new posts, render all
python extract/main.py --days 180    # one-off: seed ~6 months of history
python extract/main.py --backfill    # every obituary post ever published
python extract/main.py --render-only # re-render from the master, no fetch/API
```

The sync phase folds new/changed posts into `data/obituaries_master.json` (the
committed source of truth); the render phase rebuilds
`web/public/data/obituaries.json`, every `web/public/o/<slug>.html`, and
`web/public/sitemap.xml` from the whole master.

## Run the widget locally

```powershell
cd web
npm run dev      # http://localhost:5173/wpr-obituaries/
```

The widget reads `web/public/data/obituaries.json`, a build artifact regenerated
from the committed master. Generate it (and the pages) locally with
`python extract/main.py --render-only` — no API or proxy needed.

## Build and deploy

```powershell
cd web; npm run build   # outputs web/dist (widget + data + per-person pages)
```

GitHub Actions deploys automatically on the Mon/Wed/Fri schedule and on manual
dispatch. In the repo settings, configure:

- **Secrets**: `ANTHROPIC_API_KEY`, `WEBSHARE_PROXY_URL`
- **Variables**: `PUBLIC_BASE_URL`
- **Pages**: source = GitHub Actions

## Embedding on WordPress

Add an iframe pointing at the deployed widget URL on the Obituaries page. The
per-person pages are linked from each card and are crawled directly by Google.

See `CLAUDE.md` for architecture, engineering rules, and open items.

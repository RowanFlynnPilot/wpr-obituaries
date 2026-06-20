# WPR Obituaries

A searchable, SEO-ranking obituary tool for Wausau Pilot & Review. Daily batch
obituary posts are split into individual, crawlable pages so name searches find
WPR first. A React widget provides browse and search; static per-person pages
do the ranking.

## Layout

```
extract/   Python pipeline: REST pull → Haiku extraction → JSON + static pages
web/       React 18 / Vite memorial-register widget (the iframe embed)
.github/   Mon/Wed/Fri cron that extracts and deploys to GitHub Pages
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

Set the sponsor in `web/public/data/sponsor.json`:

```json
{ "name": "Peterson/Kraemer Funeral Homes & Crematory, Inc.", "url": "https://www.petersonkraemer.com" }
```

## Run the extractor

```powershell
python extract/main.py             # recent window (45 days)
python extract/main.py --backfill  # every obituary post ever published
```

This writes `web/public/data/obituaries.json` and `web/public/o/<slug>.html`.

## Run the widget locally

```powershell
cd web
npm run dev      # http://localhost:5173/wpr-obituaries/
```

A sample `obituaries.json` ships in the repo so the widget renders before the
extractor has run.

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

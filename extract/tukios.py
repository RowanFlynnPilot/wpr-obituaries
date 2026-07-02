"""Tukios obituary API client — the platform behind most Wausau-area homes.

Tukios-hosted funeral homes (Brainard, Helke, Peterson/Kraemer, Ascend, Beste,
Rembs, Taylor-Stine-Waid) publish their obituaries through one public JSON API.
Every record is *already structured* — full text, dates, city, portrait — so,
unlike the WordPress batch scrape, there is no model extraction: the adapter
maps fields straight onto the record contract.

The bearer token below ships in the clear inside every Tukios site's obituary
widget bundle; it is a public read key, not a secret, so it lives here rather
than in the environment. If it ever stops working, re-read it from a site's
`/obituaries` page source (the value after `Authorization: Bearer` in the
widget's requests) — see docs/funeral-home-scraping.md.

Results are sorted by date of death, newest first, so a windowed poll stops as
soon as it pages past the cutoff.
"""

from __future__ import annotations

import re
import sys
import time
from collections.abc import Iterator

from wp_client import make_session

API = "https://websites.tukios.com/api/v1/obituaries"
TOKEN = "k9PMgGzdKda2PGocioyUBzAtVwFj7FsKZlpxORi6"  # public read key (see module docstring)
PER_PAGE = 50
TIMEOUT = 30
RETRIES = 4

# The site alias is an 8-hex-char key printed in the obituaries page source as
# `siteAlias = '...'` or `SiteAlias: '...'`. It is NOT the `login?site_id=` value.
_ALIAS_RE = re.compile(r"[sS]iteAlias['\"]?\s*[:=]\s*['\"]([0-9a-f]{6,})['\"]")


def find_site_alias(page_html: str) -> str | None:
    """Extract a home's Tukios site alias from its obituaries page HTML."""
    m = _ALIAS_RE.search(page_html)
    return m.group(1) if m else None


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}


def _get_page(session, site_alias: str, page: int) -> dict:
    """Fetch one page of the paginator, retrying transient transport/5xx errors."""
    params = {"siteAlias": site_alias, "page": page, "per_page": PER_PAGE}
    last_error: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            resp = session.get(API, params=params, headers=_headers(), timeout=TIMEOUT)
            if resp.status_code < 500:
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict) or "data" not in data:
                    raise ValueError(
                        f"Unexpected Tukios response for alias {site_alias} "
                        f"(is the alias valid?)"
                    )
                return data
            last_error = RuntimeError(f"{resp.status_code} from Tukios API")
        except Exception as exc:  # noqa: BLE001 — network/proxy/TLS blips
            last_error = exc
        if attempt < RETRIES:
            wait = 2**attempt
            print(f"  tukios retry {attempt + 1}/{RETRIES} after {wait}s: {last_error}", file=sys.stderr)
            time.sleep(wait)
    raise last_error


def site_summary(site_alias: str) -> dict:
    """Verify an alias against the live API: {total, location_name}.

    A wrong alias resolves to an empty parent site (total 0, a corporate
    location_name), so the caller can tell a real home from a bad key.
    """
    payload = _get_page(make_session(), site_alias, 1)
    return {
        "total": int(payload.get("total") or 0),
        "location_name": payload.get("location_name"),
    }


def fetch_obituaries(site_alias: str, cutoff: str | None) -> Iterator[dict]:
    """Yield published obituary records for one site, newest death date first.

    Stops paging once a record's date of death is older than `cutoff`
    (ISO ``YYYY-MM-DD``); pass ``None`` to walk the entire back-catalogue. A
    record without a death date never triggers the stop (we can't place it on
    the timeline) but is still yielded for the caller to judge.
    """
    session = make_session()
    page = 1
    while True:
        payload = _get_page(session, site_alias, page)
        rows = payload.get("data") or []
        if not rows:
            return
        for row in rows:
            if not row.get("is_published", True):
                continue
            dod = row.get("date_of_death")
            if cutoff and dod and dod < cutoff:
                return  # sorted by death date desc — everything after is older
            yield row
        if page >= (payload.get("last_page") or page):
            return
        page += 1

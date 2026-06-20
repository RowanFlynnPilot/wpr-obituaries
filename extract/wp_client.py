"""Fetch obituary batch posts from the Newspack/WordPress REST API.

Wausau Pilot & Review sits behind Cloudflare, so every request is routed
through a Webshare residential proxy — the same mechanism the gas-prices
widget already relies on. Fail loudly the moment a precondition is missing.
"""

from __future__ import annotations

import os

from curl_cffi import requests

BASE = "https://wausaupilotandreview.com/wp-json/wp/v2"
CATEGORY_SLUG = "obituaries"
TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _proxies() -> dict[str, str]:
    """Read the Webshare proxy URL from the environment or raise."""
    url = os.environ.get("WEBSHARE_PROXY_URL")
    if not url:
        raise RuntimeError(
            "WEBSHARE_PROXY_URL is not set. Expected a value like "
            "http://user:pass@proxy.webshare.io:80"
        )
    return {"http": url, "https": url}


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    session.proxies.update(_proxies())
    return session


def _category_id(session: requests.Session) -> int:
    """Resolve the obituaries category ID. Raise if it cannot be found."""
    resp = session.get(
        f"{BASE}/categories",
        params={"slug": CATEGORY_SLUG, "_fields": "id,slug"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    rows = resp.json()
    if not rows:
        raise RuntimeError(f"No category found for slug '{CATEGORY_SLUG}'.")
    return int(rows[0]["id"])


def fetch_batch_posts(window_days: int | None) -> list[dict]:
    """Return raw obituary batch posts, newest first.

    window_days bounds the pull for the Mon/Wed/Fri cron (cost control).
    Pass None for a full backfill.
    """
    session = _session()
    category = _category_id(session)

    params = {
        "categories": category,
        "per_page": 100,
        "orderby": "date",
        "order": "desc",
        "_fields": "id,date,link,title.rendered,content.rendered",
    }
    if window_days is not None:
        from datetime import datetime, timedelta, timezone

        after = datetime.now(timezone.utc) - timedelta(days=window_days)
        params["after"] = after.isoformat()

    posts: list[dict] = []
    page = 1
    while True:
        resp = session.get(
            f"{BASE}/posts", params={**params, "page": page}, timeout=TIMEOUT
        )
        if resp.status_code == 400:
            # WordPress returns 400 once page exceeds the available range.
            break
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        posts.extend(batch)
        page += 1

    return posts

"""Fetch obituary batch posts from the Newspack/WordPress REST API.

Wausau Pilot & Review sits behind Cloudflare, so every request routes through a
Webshare residential proxy and impersonates Chrome at the TLS layer (curl_cffi)
to clear Cloudflare's bot detection. Fail loudly the moment a precondition is
missing.
"""

from __future__ import annotations

import os
import sys
import time

from curl_cffi import requests

TIMEOUT = 30
RETRIES = 5  # the residential proxy + Cloudflare are flaky (incl. TLS blips); ride them out


def _get(session: requests.Session, url: str, params: dict) -> requests.Response:
    """GET with bounded exponential backoff on transport errors and 5xx.

    Returns 4xx responses as-is (the caller distinguishes the 400 that marks the
    end of pagination); only server errors and exceptions are retried.
    """
    last_error: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            resp = session.get(url, params=params, timeout=TIMEOUT)
            if resp.status_code < 500:
                return resp
            last_error = RuntimeError(f"{resp.status_code} from {url}")
        except Exception as exc:  # noqa: BLE001 — network/proxy/TLS blips
            last_error = exc
        if attempt < RETRIES:
            wait = 2**attempt  # 1s, 2s, 4s
            print(f"  fetch retry {attempt + 1}/{RETRIES} after {wait}s: {last_error}", file=sys.stderr)
            time.sleep(wait)
    raise last_error


def _proxies() -> dict[str, str]:
    """Read the Webshare proxy URL from the environment or raise."""
    url = os.environ.get("WEBSHARE_PROXY_URL")
    if not url:
        raise RuntimeError(
            "WEBSHARE_PROXY_URL is not set. Expected a value like "
            "http://user:pass@p.webshare.io:80"
        )
    return {"http": url, "https": url}


def _session() -> requests.Session:
    """Browser-impersonating session that routes through the residential proxy."""
    return requests.Session(impersonate="chrome", proxies=_proxies())


def make_session() -> requests.Session:
    """Public proxied, browser-impersonating session (e.g. for vendoring photos
    that sit behind the same Cloudflare as the posts)."""
    return _session()


def _category_id(session: requests.Session, api_base: str, category_slug: str) -> int:
    """Resolve the obituaries category ID. Raise if it cannot be found."""
    resp = _get(
        session, f"{api_base}/categories", {"slug": category_slug, "_fields": "id,slug"}
    )
    resp.raise_for_status()
    rows = resp.json()
    if not rows:
        raise RuntimeError(f"No category found for slug '{category_slug}'.")
    return int(rows[0]["id"])


def fetch_batch_posts(
    window_days: int | None, api_base: str, category_slug: str
) -> list[dict]:
    """Return raw obituary batch posts, newest first.

    window_days bounds the pull for the Mon/Wed/Fri cron (cost control).
    Pass None for a full backfill. api_base/category_slug come from the newsroom
    config so a fork points at its own WordPress install.
    """
    session = _session()
    category = _category_id(session, api_base, category_slug)

    params = {
        "categories": category,
        "per_page": 100,
        "orderby": "date",
        "order": "desc",
        "_fields": "id,date,modified_gmt,link,title.rendered,content.rendered",
    }
    if window_days is not None:
        from datetime import datetime, timedelta, timezone

        after = datetime.now(timezone.utc) - timedelta(days=window_days)
        params["after"] = after.isoformat()

    posts: list[dict] = []
    page = 1
    while True:
        resp = _get(session, f"{api_base}/posts", {**params, "page": page})
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
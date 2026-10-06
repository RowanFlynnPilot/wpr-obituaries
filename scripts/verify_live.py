"""Does the deployed site actually serve a reader?

A green deploy says nothing about whether the result is reachable. In October
2026 the edge returned 526 for five days — the origin TLS certificate had
expired and Cloudflare, set to validate it, refused every request — while each
scheduled run reported success, because nothing ever asked the public URL.

This runs after the deploy and fails the workflow when a reader could not load
the register, the index the widget fetches, or a person's page. It checks the
published site from outside, which is the only check that would have caught it.

    PUBLIC_BASE_URL=https://… python scripts/verify_live.py
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Identifies itself rather than impersonating a browser: this is the newsroom
# checking its own site, and a blocked health check should be visible, not
# disguised.
UA = "WPR-Obituaries-HealthCheck/1.0 (+https://github.com/RowanFlynnPilot/wpr-obituaries)"
ATTEMPTS = 4  # a Pages deploy can take a few seconds to reach the edge
BACKOFF = 10
TIMEOUT = 30


def fetch(url: str) -> tuple[int, bytes]:
    """(status, body) for a URL, retrying while it is unreachable or 5xx."""
    last = (0, b"")
    for attempt in range(1, ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:  # a real answer, just not a good one
            last = (e.code, e.read()[:400])
            if e.code < 500 and e.code != 429:
                return last  # 404/403 won't improve by waiting
        except Exception as e:  # DNS, TLS, timeout — no answer at all
            last = (0, str(e).encode()[:400])
        if attempt < ATTEMPTS:
            time.sleep(BACKOFF)
    return last


def cert_days_left(host: str) -> int | None:
    """Days until the certificate the edge presents expires, or None if unknown."""
    try:
        import socket

        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                expires = tls.getpeercert()["notAfter"]
        when = datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        return (when - datetime.now(timezone.utc)).days
    except Exception:
        return None


def main() -> int:
    base = (os.environ.get("PUBLIC_BASE_URL") or "").rstrip("/")
    if not base:
        print("PUBLIC_BASE_URL is unset — nothing to verify", file=sys.stderr)
        return 1

    failures: list[str] = []
    notes: list[str] = []

    def check(path: str, label: str) -> bytes | None:
        status, body = fetch(f"{base}{path}")
        if status == 200:
            print(f"ok    {label}: {base}{path}")
            return body
        failures.append(f"{label} returned {status or 'no response'} — {base}{path}")
        print(f"FAIL  {label}: {status or 'no response'} — {base}{path}", file=sys.stderr)
        return None

    check("/", "register")
    index = check("/data/obituaries.json", "widget index")
    check("/sitemap.xml", "sitemap")

    # The person pages are the whole SEO premise, so prove one is reachable
    # rather than trusting that the index implies it.
    if index:
        try:
            obituaries = json.loads(index)["obituaries"]
        except Exception as e:
            failures.append(f"widget index is not valid JSON — {e}")
            obituaries = []
        if not obituaries:
            failures.append("widget index served 0 records")
        else:
            print(f"ok    widget index lists {len(obituaries)} records")
            check(f"/o/{obituaries[0]['slug']}.html", "a person's page")

    # Not fatal: with the edge set to Full the site serves regardless, but a
    # lapsing certificate is worth seeing long before it matters again.
    days = cert_days_left(base.split("//", 1)[-1].split("/")[0])
    if days is not None:
        notes.append(f"edge certificate expires in {days} days")
        print(f"note  edge certificate expires in {days} days")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            if failures:
                fh.write("## The published site is not serving\n\n")
                for f in failures:
                    fh.write(f"- {f}\n")
                fh.write("\nThe deploy succeeded, so this is the edge or DNS, not the build.\n")
            else:
                fh.write(f"## Live site verified\n\n{base} is serving.\n")
            for n in notes:
                fh.write(f"\n{n}\n")

    if failures:
        print(f"\n{len(failures)} check(s) failed", file=sys.stderr)
        return 1
    print("\nlive site verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Tribute Technology (Frazer / Tribute Center Online) obituary client.

The second scrape platform, behind Schmidt & Schulta, John J. Buettgen
(honorone.com), Mid-Wisconsin Cremation Society, and Carlson. Mirror image of
Tukios: discovery is easy (a Recent-Obituaries RSS feed, plus obituary sitemaps
for a full backfill), and each person page carries a schema.org `Person` JSON-LD
block with the complete obituary text, both dates, and the portrait — so, like
Tukios, there is no model extraction; the adapter maps the parsed record
straight to an `Obituary`.

Discovery is keyed by the home's own site URL (no per-site token). Some of these
sites are Cloudflare-fronted and some are plain IIS; the shared curl_cffi
Chrome-impersonating session (`wp_client.make_session`) clears both.
"""

from __future__ import annotations

import gzip
import html
import json
import re
import sys
import time
from collections.abc import Iterator
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

TIMEOUT = 30
RETRIES = 4

_OBID_RE = re.compile(r"obId=(\d+)")


def obid(url: str) -> str | None:
    """The stable numeric obituary id embedded in a person-page URL."""
    m = _OBID_RE.search(url)
    return m.group(1) if m else None


def _get(session, url: str):
    """GET with bounded backoff on transport errors and 5xx."""
    last_error: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT)
            if resp.status_code < 500:
                resp.raise_for_status()
                return resp
            last_error = RuntimeError(f"{resp.status_code} from {url}")
        except Exception as exc:  # noqa: BLE001 — network/proxy/TLS blips
            last_error = exc
        if attempt < RETRIES:
            wait = 2**attempt
            print(f"  tribute retry {attempt + 1}/{RETRIES} after {wait}s: {last_error}", file=sys.stderr)
            time.sleep(wait)
    raise last_error


def _rfc822_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError):
        return None


def _maybe_gunzip(data: bytes) -> bytes:
    return gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data


def recent_urls(session, base: str, cutoff: str | None) -> Iterator[tuple[str, str | None]]:
    """(person_url, pubdate_iso) from the Recent-Obituaries RSS, newest first.

    Stops once an item's pubDate is older than `cutoff`. If the feed runs out
    before reaching the cutoff, the window reaches past the feed — warn, because
    a busier home could have obituaries in that gap (the Mon/Wed/Fri cron makes
    this a non-issue in practice, but a silent gap would not be honest).
    """
    resp = _get(session, base.rstrip("/") + "/rss.xml")
    root = ET.fromstring(resp.content)
    reached_cutoff = False
    for item in root.iter("item"):
        link = (item.findtext("link") or "").strip()
        iso = _rfc822_to_iso(item.findtext("pubDate"))
        if cutoff and iso and iso < cutoff:
            reached_cutoff = True
            break
        if link:
            yield link, iso
    if cutoff and not reached_cutoff:
        print(
            f"  tribute: RSS feed for {base} ran out before the {cutoff} cutoff — "
            f"older obituaries in the window may be missed until the next run.",
            file=sys.stderr,
        )


def all_urls(session, base: str) -> Iterator[tuple[str, str | None]]:
    """(person_url, lastmod_iso) for every obituary, from the sitemaps (backfill)."""
    idx = _get(session, base.rstrip("/") + "/sitemap.xml")
    index = ET.fromstring(_maybe_gunzip(idx.content))
    sitemaps = [
        el.text for el in index.iter()
        if el.tag.endswith("loc") and el.text and "obituaries-sitemap" in el.text
    ]
    for sm in sitemaps:
        tree = ET.fromstring(_maybe_gunzip(_get(session, sm).content))
        for url_el in tree.iter():
            if not url_el.tag.endswith("url"):
                continue
            loc = lastmod = None
            for child in url_el:
                if child.tag.endswith("loc"):
                    loc = child.text
                elif child.tag.endswith("lastmod"):
                    lastmod = child.text
            if loc and "obId=" in loc:
                yield loc, (lastmod[:10] if lastmod else None)


def _iter_ld(page_html: str) -> Iterator[dict]:
    """Every JSON-LD object on a page; malformed blocks are skipped."""
    for block in re.findall(
        r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page_html, re.S
    ):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue  # a malformed block never sinks the whole page
        yield from data if isinstance(data, list) else [data]


def _find_type(page_html: str, typename: str) -> dict | None:
    for obj in _iter_ld(page_html):
        types = obj.get("@type")
        if typename in (types if isinstance(types, list) else [types]):
            return obj
    return None


def _parse_person_ld(page_html: str) -> dict | None:
    """The schema.org Person block from a person page, or None if absent."""
    return _find_type(page_html, "Person")


_SITE_NAME_RE = re.compile(
    r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)', re.I
)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def firm_name(session, url: str) -> str | None:
    """Best-effort funeral home name for onboarding.

    Business JSON-LD when present, else the home page's og:site_name or <title>
    (person pages often carry only Person data, so pass the site root here).
    """
    page = _get(session, url).text
    for typename in ("FuneralHome", "LocalBusiness", "Organization"):
        obj = _find_type(page, typename)
        if obj and obj.get("name"):
            return obj["name"].strip()
    m = _SITE_NAME_RE.search(page)
    if m:
        return html.unescape(m.group(1)).strip()
    m = _TITLE_RE.search(page)
    if m:
        title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
        title = re.split(r"\s[|–-]\s", title)[0].strip()  # drop " | Obituaries" boilerplate
        return title or None
    return None


def person_record(session, url: str) -> dict | None:
    """Fetch a person page and return its Person data, or None if unusable.

    Keys mirror the JSON-LD: name, birthDate/deathDate (human-readable strings),
    description (HTML-entity-encoded obituary), image. Adds url + obId.
    """
    person = _parse_person_ld(_get(session, url).text)
    if not person:
        return None
    return {
        "name": (person.get("name") or "").strip(),
        "birthDate": person.get("birthDate"),
        "deathDate": person.get("deathDate"),
        "description": person.get("description") or "",
        "image": person.get("image"),
        "url": url,
        "obId": obid(url),
    }


def parse_date(value: str | None) -> str | None:
    """Human-readable "Month D, YYYY" -> ISO date, or None if not that shape."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def body_text(description_html: str) -> str:
    """Obituary HTML (entity-encoded in the JSON-LD) -> paragraphs split by blank lines."""
    soup = BeautifulSoup(html.unescape(description_html or ""), "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    blocks = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    blocks = [b for b in blocks if b]
    if not blocks:
        text = soup.get_text("\n", strip=True)
        blocks = [b.strip() for b in text.split("\n") if b.strip()]
    return "\n\n".join(blocks)

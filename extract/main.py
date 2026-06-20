"""Build the obituary master, then render the whole site from it.

  python -m extract.main               # recent window: extract new posts, render all
  python -m extract.main --days 180    # one-off seed: extract the last ~6 months
  python -m extract.main --backfill    # extract every obituary post ever published
  python -m extract.main --render-only # re-render from the master, no fetch/API

The pipeline is split in two so that per-person pages outlive the fetch window:

  1. Sync  — fetch the window, extract only *new or changed* batch posts (Haiku),
             and upsert them into the persistent master (`data/obituaries_master.json`).
  2. Render — rebuild the search index, every per-person page, and sitemap.xml
             from the *entire* master. Rendering is free (no API), so the window
             only bounds extraction cost, never what stays published.

Requires WEBSHARE_PROXY_URL and ANTHROPIC_API_KEY for sync (not for --render-only).
A post that fails to extract is quarantined to `data/failures.json` and the run
exits non-zero, but the master is still saved and the site still rendered — so a
single bad post never costs us the rest of the catalogue.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic

from extractor import extract_obituaries
from homes import load_homes, resolve_home
from models import Obituary
from og import render_card
from photos import vendor_photos, vendored_slugs
from store import Master, load_manual, load_master, load_suppressed, save_master
from templates import render_feed, render_home_page, render_person_page, render_sitemap
from wp_client import fetch_batch_posts, make_session

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "web" / "public" / "data"
PAGES_DIR = ROOT / "web" / "public" / "o"
HOME_PAGES_DIR = ROOT / "web" / "public" / "funeral-home"
PHOTOS_DIR = ROOT / "web" / "public" / "assets" / "photos"
OG_DIR = ROOT / "web" / "public" / "assets" / "og"
SITEMAP_FILE = ROOT / "web" / "public" / "sitemap.xml"
FEED_FILE = ROOT / "web" / "public" / "feed.xml"
SPONSOR_FILE = DATA_DIR / "sponsor.json"
INDEX_FILE = DATA_DIR / "obituaries.json"
MASTER_FILE = ROOT / "data" / "obituaries_master.json"
MANUAL_FILE = ROOT / "data" / "manual.json"
SUPPRESSED_FILE = ROOT / "data" / "suppressed.json"
HOMES_FILE = ROOT / "data" / "funeral_homes.json"
FAILURES_FILE = ROOT / "data" / "failures.json"
WINDOW_DAYS = 14  # days to look back for new/changed posts each run; a safety
#                   buffer (covers missed crons), not a retention limit — the
#                   master keeps every published page forever.


def _load_sponsor() -> dict:
    if not SPONSOR_FILE.exists():
        raise RuntimeError(f"Missing sponsor config at {SPONSOR_FILE}")
    return json.loads(SPONSOR_FILE.read_text(encoding="utf-8"))


def _require_base_url() -> str:
    base_url = os.environ.get("PUBLIC_BASE_URL")
    if not base_url:
        raise RuntimeError(
            "PUBLIC_BASE_URL is not set. This is where the pages are served and "
            "indexed, e.g. https://rowanflynnpilot.github.io/wpr-obituaries"
        )
    return base_url.rstrip("/")


def _post_modified(post: dict) -> str:
    """Revision stamp for a post; falls back to publish date if absent."""
    return post.get("modified_gmt") or post.get("modified") or post["date"]


def sync(master: Master, client: Anthropic, window: int | None) -> list[tuple[str, str]]:
    """Fetch the window and fold new/changed posts into the master.

    Returns the list of (url, error) for posts that failed to extract.
    """
    posts = fetch_batch_posts(window)
    print(f"Fetched {len(posts)} batch posts.")
    if not posts:
        print("WARNING: 0 posts fetched — possible proxy/Cloudflare block.", file=sys.stderr)

    failures: list[tuple[str, str]] = []
    extracted = skipped = 0
    for post in posts:
        post_id = int(post["id"])
        modified = _post_modified(post)
        if master.is_processed(post_id, modified):
            skipped += 1
            continue
        try:
            people = extract_obituaries(post, client)
        except Exception as exc:  # noqa: BLE001 — quarantine and report loudly
            failures.append((post.get("link", "unknown"), str(exc)))
            continue
        master.upsert_post(post_id, modified, people)
        extracted += len(people)

    print(f"Extracted {extracted} obituaries from new/changed posts; {skipped} unchanged.")
    return failures


def _index_photo(ob: Obituary, vendored: set[str]) -> str | None:
    """Repo-relative local path if vendored (widget prepends BASE), else remote."""
    if ob.slug in vendored:
        return f"assets/photos/{ob.slug}.jpg"
    return ob.photo_url


def _page_photo(ob: Obituary, vendored: set[str], base_url: str) -> str | None:
    """Absolute local URL if vendored, else the remote URL — for static pages."""
    if ob.slug in vendored:
        return f"{base_url}/assets/photos/{ob.slug}.jpg"
    return ob.photo_url


def _write_index(records: list[Obituary], vendored: set[str], homes: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Newest batch first, then alphabetical by name within a date.
    ordered = sorted(records, key=lambda r: r.name)
    ordered = sorted(ordered, key=lambda r: r.source_date, reverse=True)
    obituaries = []
    for r in ordered:
        record = r.to_index_dict()
        record["photoUrl"] = _index_photo(r, vendored)
        home = resolve_home(r.funeral_home, homes)
        record["funeralHomeUrl"] = f"funeral-home/{home['slug']}.html" if home else None
        obituaries.append(record)
    payload = {"count": len(ordered), "obituaries": obituaries}
    INDEX_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _lifespan_str(ob: Obituary) -> str:
    birth = ob.birth_date[:4] if ob.birth_date else ""
    death = ob.death_date[:4] if ob.death_date else (str(ob.death_year) if ob.death_year else "")
    return f"{birth} – {death}" if birth and death else death


def _sponsor_line(sponsor: dict) -> str:
    names = [s["name"].split()[0] for s in (sponsor.get("sponsors") or []) if s.get("name")]
    return "Obituaries  ·  " + " + ".join(names) if names else "Obituaries"


def _dedupe_people(
    records: list[Obituary],
) -> tuple[list[Obituary], dict[str, Obituary]]:
    """Collapse one person (name + death date) appearing in two batch posts.

    Returns (canonical, primary_by_slug): `canonical` has one record per person
    for the index/feed/home pages; `primary_by_slug` maps every record's slug to
    its chosen primary, so a duplicate page can rel=canonical at the primary
    instead of competing with it (and without 404ing the duplicate URL).
    """
    groups: dict[tuple, list[Obituary]] = {}
    for r in records:
        stamp = r.death_date or (str(r.death_year) if r.death_year else r.source_date)
        groups.setdefault((r.name.lower().strip(), stamp), []).append(r)
    canonical: list[Obituary] = []
    primary_by_slug: dict[str, Obituary] = {}
    for group in groups.values():
        # the fullest record wins (longest body), then the later post
        primary = max(group, key=lambda r: (len(r.body or ""), r.source_date, r.slug))
        canonical.append(primary)
        for r in group:
            primary_by_slug[r.slug] = primary
    return canonical, primary_by_slug


def _write_pages(
    records: list[Obituary],
    sponsor: dict,
    base_url: str,
    vendored: set[str],
    homes: list[dict],
    primary_by_slug: dict[str, Obituary],
) -> None:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    OG_DIR.mkdir(parents=True, exist_ok=True)
    for stale in PAGES_DIR.glob("*.html"):
        stale.unlink()  # render is authoritative: never leave an orphaned page
    sponsor_line = _sponsor_line(sponsor)
    recent = sorted(records, key=lambda r: r.source_date, reverse=True)[:7]
    for ob in records:
        related = [r for r in recent if r.slug != ob.slug][:6]
        portrait = PHOTOS_DIR / f"{ob.slug}.jpg" if ob.slug in vendored else None
        render_card(ob.name, _lifespan_str(ob), portrait, OG_DIR / f"{ob.slug}.png", sponsor_line)
        og_image = f"{base_url}/assets/og/{ob.slug}.png"
        home = resolve_home(ob.funeral_home, homes)
        home_url = f"{base_url}/funeral-home/{home['slug']}.html" if home else None
        primary = primary_by_slug.get(ob.slug, ob)
        canonical_url = f"{base_url}/o/{primary.slug}.html"
        (PAGES_DIR / f"{ob.slug}.html").write_text(
            render_person_page(
                ob, sponsor, base_url, related, _page_photo(ob, vendored, base_url),
                og_image, home_url, canonical_url,
            ),
            encoding="utf-8",
        )


def _write_home_pages(
    records: list[Obituary], sponsor: dict, base_url: str, homes: list[dict]
) -> list[str]:
    """A landing page per canonical funeral home. Returns the home slugs (sitemap)."""
    HOME_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for stale in HOME_PAGES_DIR.glob("*.html"):
        stale.unlink()
    groups: dict[str, list[Obituary]] = {}
    meta: dict[str, dict] = {}
    for r in records:
        home = resolve_home(r.funeral_home, homes)
        if not home:
            continue
        groups.setdefault(home["slug"], []).append(r)
        meta[home["slug"]] = home
    for slug, recs in groups.items():
        recs = sorted(recs, key=lambda r: r.name)
        recs = sorted(recs, key=lambda r: r.source_date, reverse=True)
        (HOME_PAGES_DIR / f"{slug}.html").write_text(
            render_home_page(meta[slug], recs, sponsor, base_url), encoding="utf-8"
        )
    return list(groups)


def render(master: Master, sponsor: dict, base_url: str, allow_empty: bool) -> None:
    """Rebuild index, pages, and sitemap from the master + manual records.

    Manual one-offs are merged in; suppressed slugs (family requests) are removed
    from everything published, though they remain in the master for the record.
    Portraits resolve to the vendored local copy when present, else the remote URL.
    """
    suppressed = load_suppressed(SUPPRESSED_FILE)
    manual = load_manual(MANUAL_FILE)
    records = [
        r for r in (master.records + manual) if r.slug not in suppressed
    ]
    if not records and not allow_empty:
        raise RuntimeError(
            "Refusing to render an empty site (0 records after manual/suppression). "
            "Seed the master with `--backfill`, or pass --allow-empty if intended."
        )
    # One canonical record per person for the visible surfaces; every record
    # still gets a page (duplicates rel=canonical at their primary).
    canonical, primary_by_slug = _dedupe_people(records)
    vendored = vendored_slugs(PHOTOS_DIR)
    homes = load_homes(HOMES_FILE)
    _write_index(canonical, vendored, homes)
    _write_pages(records, sponsor, base_url, vendored, homes, primary_by_slug)
    home_slugs = _write_home_pages(canonical, sponsor, base_url, homes)
    SITEMAP_FILE.write_text(
        render_sitemap(canonical, base_url, home_slugs), encoding="utf-8"
    )
    FEED_FILE.write_text(render_feed(canonical, base_url), encoding="utf-8")
    extras = []
    dupes = len(records) - len(canonical)
    if dupes:
        extras.append(f"{dupes} cross-post dupes deduped")
    if manual:
        extras.append(f"+{len(manual)} manual")
    if suppressed:
        extras.append(f"-{len(suppressed)} suppressed")
    note = f" ({', '.join(extras)})" if extras else ""
    print(
        f"Rendered {len(records)} pages, {len(home_slugs)} funeral-home pages, "
        f"index, and sitemap{note}."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--backfill", action="store_true", help="extract all history")
    scope.add_argument(
        "--days", type=int, metavar="N",
        help="one-off: extract the last N days instead of the default window "
        "(e.g. --days 180 to seed ~6 months)",
    )
    parser.add_argument(
        "--render-only", action="store_true", help="re-render from master; no fetch/API"
    )
    parser.add_argument("--allow-empty", action="store_true", help="permit a 0-record render")
    args = parser.parse_args()

    sponsor = _load_sponsor()
    base_url = _require_base_url()
    master = load_master(MASTER_FILE)

    failures: list[tuple[str, str]] = []
    if not args.render_only:
        client = Anthropic(max_retries=4)
        if args.backfill:
            window = None
        elif args.days is not None:
            window = args.days
        else:
            window = WINDOW_DAYS
        failures = sync(master, client, window)
        save_master(master, MASTER_FILE)  # persist successes before anything can fail
        saved = vendor_photos(master.records, PHOTOS_DIR, make_session())
        if saved:
            print(f"Vendored {saved} new portrait(s).")

    render(master, sponsor, base_url, args.allow_empty)

    if not args.render_only:
        FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
        FAILURES_FILE.write_text(
            json.dumps([{"url": u, "error": e} for u, e in failures], indent=2),
            encoding="utf-8",
        )
    if failures:
        print(f"\n{len(failures)} post(s) failed to extract:", file=sys.stderr)
        for url, err in failures:
            print(f"::error::extract failed for {url}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from adapters import enabled_sources
from config import load_newsroom
from homes import load_homes, resolve_home
from models import Obituary
from og import render_card
from photos import vendor_photos, vendored_slugs
from store import Master, load_manual, load_master, load_suppressed, save_master
from templates import (
    render_feed,
    render_home_page,
    render_person_page,
    render_robots,
    render_sitemap,
)
from wp_client import make_session

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "web" / "public" / "data"
PAGES_DIR = ROOT / "web" / "public" / "o"
HOME_PAGES_DIR = ROOT / "web" / "public" / "funeral-home"
PHOTOS_DIR = ROOT / "web" / "public" / "assets" / "photos"
OG_DIR = ROOT / "web" / "public" / "assets" / "og"
# slug -> input hash; lets render skip unchanged cards. Kept outside the deployed
# public/ tree (it's build state, not site output) but cached in CI alongside og/.
OG_CACHE_FILE = ROOT / ".cache" / "og-cards.json"
OG_CARD_VERSION = "1"  # bump when og.render_card's output changes, to force regen
SITEMAP_FILE = ROOT / "web" / "public" / "sitemap.xml"
FEED_FILE = ROOT / "web" / "public" / "feed.xml"
ROBOTS_FILE = ROOT / "web" / "public" / "robots.txt"
SPONSOR_FILE = DATA_DIR / "sponsor.json"
INDEX_FILE = DATA_DIR / "obituaries.json"
MASTER_FILE = ROOT / "data" / "obituaries_master.json"
MANUAL_FILE = ROOT / "data" / "manual.json"
SUPPRESSED_FILE = ROOT / "data" / "suppressed.json"
HOMES_FILE = ROOT / "data" / "funeral_homes.json"
FAILURES_FILE = ROOT / "data" / "failures.json"
DEFAULT_WINDOW_DAYS = 14  # fallback if the wordpress_scrape adapter omits
#                           windowDays; a safety buffer (covers missed crons),
#                           not a retention limit — the master keeps every page.


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


def sync(
    master: Master, sources: list, *, backfill: bool, days: int | None
) -> list[tuple[str, str]]:
    """Fold new/changed units from every enabled source into the master.

    Each source yields work-units; we skip those the master already processed at
    the same revision, extract the rest, and upsert them. Returns the list of
    (ref, error) for units that failed to extract.

    Window per source: `--backfill` fetches all history, `--days N` overrides
    every source to N, otherwise each source polls its own configured window
    (`default_window`) — so a 14-day WordPress poll and a 45-day funeral-home
    poll coexist without one clobbering the other.
    """
    failures: list[tuple[str, str]] = []
    extracted = skipped = 0
    for source in sources:
        if backfill:
            window = None
        elif days is not None:
            window = days
        else:
            window = getattr(source, "default_window", DEFAULT_WINDOW_DAYS)
        for unit in source.units(window):
            if master.is_processed(unit.source, unit.unit_id, unit.modified):
                skipped += 1
                continue
            try:
                people = unit.extract()
            except Exception as exc:  # noqa: BLE001 — quarantine and report loudly
                failures.append((unit.ref, str(exc)))
                continue
            master.upsert_post(unit.source, unit.unit_id, unit.modified, people)
            extracted += len(people)

    print(f"Extracted {extracted} obituaries from new/changed units; {skipped} unchanged.")
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


# The model-written summary reads "Name, age, of <Town>, passed away…", so the
# town is the capitalized run right after "of " — up to a comma, the state, or a
# lowercase word. Deriving from the clean summary (not the raw obit) keeps this a
# safe best-effort facet; an unmatched summary just yields no town.
_TOWN_RE = re.compile(r"\bof ([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)")


def _derive_town(summary: str) -> str | None:
    """Best-effort town for the browse facet, from the summary. None if unclear."""
    m = _TOWN_RE.search(summary or "")
    if not m:
        return None
    town = m.group(1).strip(" ,.")
    if town.lower() in {"wisconsin", "wi"}:  # bare state slipped through
        return None
    return town or None


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
        record["homeName"] = home["name"] if home else None  # canonical, for the facet
        record["town"] = _derive_town(r.summary)
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


_NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def _name_key(name: str) -> str:
    """First + last name, lowercased, stripping middles, initials, suffixes, and
    punctuation.

    The same person reaches us from two sources under slightly different names —
    a WPR batch may say "Ryan Johnson" where the funeral home says "Ryan Paul
    Johnson", or one carries a middle initial, suffix, or quoted nickname the
    other drops. Keying on first + last collapses those to one person; the death
    date in the dedupe key keeps two different same-named people apart.
    """
    tokens = re.sub(r"[^\w\s]", " ", name.lower()).split()
    tokens = [t for t in tokens if t not in _NAME_SUFFIXES]
    if not tokens:
        return name.lower().strip()
    if len(tokens) == 1:
        return tokens[0]
    return f"{tokens[0]} {tokens[-1]}"


def _reconcile_year_only(groups: dict[tuple, list[Obituary]]) -> None:
    """Fold a year-only group into the same person's full-date group, in place.

    WPR sometimes yields only a death *year* while the funeral-home scrape has
    the full date, so the same person lands in two groups — ("jane doe", "2026")
    and ("jane doe", "2026-05-27") — and shows up twice. When a bare-year group
    has exactly one dated group sharing its name and year, merge them. The
    exactly-one guard keeps two same-named people who died the same year apart.
    """
    dated: dict[tuple, list[tuple]] = {}
    for (name_key, stamp) in groups:
        if len(stamp) == 10:  # YYYY-MM-DD
            dated.setdefault((name_key, stamp[:4]), []).append((name_key, stamp))
    for (name_key, stamp) in list(groups):
        if len(stamp) == 4 and stamp.isdigit():  # bare year
            targets = dated.get((name_key, stamp), [])
            if len(targets) == 1:
                groups[targets[0]].extend(groups.pop((name_key, stamp)))


def _dedupe_people(
    records: list[Obituary],
) -> tuple[list[Obituary], dict[str, Obituary]]:
    """Collapse one person (name + death date) appearing in more than one source.

    Returns (canonical, primary_by_slug): `canonical` has one record per person
    for the index/feed/home pages; `primary_by_slug` maps every record's slug to
    its chosen primary, so a duplicate page can rel=canonical at the primary
    instead of competing with it (and without 404ing the duplicate URL).
    """
    groups: dict[tuple, list[Obituary]] = {}
    for r in records:
        stamp = r.death_date or (str(r.death_year) if r.death_year else r.source_date)
        groups.setdefault((_name_key(r.name), stamp), []).append(r)
    _reconcile_year_only(groups)
    canonical: list[Obituary] = []
    primary_by_slug: dict[str, Obituary] = {}
    for group in groups.values():
        # the fullest record wins (longest body), then the later post
        primary = max(group, key=lambda r: (len(r.body or ""), r.source_date, r.slug))
        canonical.append(primary)
        for r in group:
            primary_by_slug[r.slug] = primary
    return canonical, primary_by_slug


def _og_brand_fingerprint(newsroom, sponsor_line: str) -> str:
    """Everything global to a share-card — change it and every card regenerates."""
    return "|".join([OG_CARD_VERSION, newsroom.name, newsroom.accent, newsroom.paper, sponsor_line])


def _og_input_hash(ob: Obituary, portrait: Path | None, brand_fp: str) -> str:
    """Content hash of a card's inputs (brand, name, dates, portrait bytes)."""
    parts = [brand_fp, ob.name, _lifespan_str(ob)]
    if portrait and portrait.exists():
        parts.append(hashlib.sha1(portrait.read_bytes()).hexdigest())
    else:
        parts.append("no-portrait")
    return hashlib.sha1("\x00".join(parts).encode()).hexdigest()


def _load_og_cache() -> dict[str, str]:
    if not OG_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(OG_CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}  # a corrupt cache just means a cold render, never a failure


def _save_og_cache(cache: dict[str, str]) -> None:
    OG_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    OG_CACHE_FILE.write_text(
        json.dumps(dict(sorted(cache.items())), indent=0), encoding="utf-8"
    )


def _prune_og_orphans(live_slugs: set[str]) -> None:
    """Delete cards for obituaries no longer rendered (suppressed/removed)."""
    for png in OG_DIR.glob("*.png"):
        if png.stem not in live_slugs:
            png.unlink()


def _write_pages(
    records: list[Obituary],
    sponsor: dict,
    base_url: str,
    vendored: set[str],
    homes: list[dict],
    primary_by_slug: dict[str, Obituary],
    newsroom,
) -> None:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    OG_DIR.mkdir(parents=True, exist_ok=True)
    for stale in PAGES_DIR.glob("*.html"):
        stale.unlink()  # render is authoritative: never leave an orphaned page
    sponsor_line = _sponsor_line(sponsor)
    # Composing the branded share-card (PIL) is the expensive part of a render, so
    # memoize it: a card is regenerated only when its inputs change (name, dates,
    # portrait bytes, or the brand). The HTML is cheap and always rewritten — that
    # sidesteps the "recent obituaries" cross-link making every page interdependent.
    brand_fp = _og_brand_fingerprint(newsroom, sponsor_line)
    og_cache = _load_og_cache()
    fresh_cache: dict[str, str] = {}
    og_made = og_kept = 0
    recent = sorted(records, key=lambda r: r.source_date, reverse=True)[:7]
    for ob in records:
        related = [r for r in recent if r.slug != ob.slug][:6]
        portrait = PHOTOS_DIR / f"{ob.slug}.jpg" if ob.slug in vendored else None
        og_path = OG_DIR / f"{ob.slug}.png"
        digest = _og_input_hash(ob, portrait, brand_fp)
        if og_cache.get(ob.slug) == digest and og_path.exists():
            og_kept += 1
        else:
            render_card(ob.name, _lifespan_str(ob), portrait, og_path, newsroom, sponsor_line)
            og_made += 1
        fresh_cache[ob.slug] = digest
        og_image = f"{base_url}/assets/og/{ob.slug}.png"
        home = resolve_home(ob.funeral_home, homes)
        home_url = f"{base_url}/funeral-home/{home['slug']}.html" if home else None
        primary = primary_by_slug.get(ob.slug, ob)
        canonical_url = f"{base_url}/o/{primary.slug}.html"
        (PAGES_DIR / f"{ob.slug}.html").write_text(
            render_person_page(
                ob, sponsor, base_url, newsroom, related, _page_photo(ob, vendored, base_url),
                og_image, home_url, canonical_url,
            ),
            encoding="utf-8",
        )
    _prune_og_orphans({ob.slug for ob in records})
    _save_og_cache(fresh_cache)
    print(f"OG cards: {og_made} generated, {og_kept} reused from cache.")


def _write_home_pages(
    records: list[Obituary], sponsor: dict, base_url: str, homes: list[dict], newsroom
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
            render_home_page(meta[slug], recs, sponsor, base_url, newsroom), encoding="utf-8"
        )
    return list(groups)


def render(master: Master, sponsor: dict, base_url: str, newsroom, allow_empty: bool) -> None:
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
    _write_pages(records, sponsor, base_url, vendored, homes, primary_by_slug, newsroom)
    home_slugs = _write_home_pages(canonical, sponsor, base_url, homes, newsroom)
    SITEMAP_FILE.write_text(
        render_sitemap(canonical, base_url, home_slugs), encoding="utf-8"
    )
    FEED_FILE.write_text(render_feed(canonical, base_url, newsroom), encoding="utf-8")
    ROBOTS_FILE.write_text(render_robots(base_url), encoding="utf-8")
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
    newsroom = load_newsroom()
    base_url = _require_base_url()
    master = load_master(MASTER_FILE)

    failures: list[tuple[str, str]] = []
    if not args.render_only:
        sources = enabled_sources(newsroom)
        failures = sync(master, sources, backfill=args.backfill, days=args.days)
        save_master(master, MASTER_FILE)  # persist successes before anything can fail
        saved = vendor_photos(master.records, PHOTOS_DIR, make_session())
        if saved:
            print(f"Vendored {saved} new portrait(s).")

    render(master, sponsor, base_url, newsroom, args.allow_empty)

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

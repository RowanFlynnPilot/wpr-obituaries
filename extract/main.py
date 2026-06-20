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
from models import Obituary
from store import Master, load_manual, load_master, load_suppressed, save_master
from templates import render_person_page, render_sitemap
from wp_client import fetch_batch_posts

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "web" / "public" / "data"
PAGES_DIR = ROOT / "web" / "public" / "o"
SITEMAP_FILE = ROOT / "web" / "public" / "sitemap.xml"
SPONSOR_FILE = DATA_DIR / "sponsor.json"
INDEX_FILE = DATA_DIR / "obituaries.json"
MASTER_FILE = ROOT / "data" / "obituaries_master.json"
MANUAL_FILE = ROOT / "data" / "manual.json"
SUPPRESSED_FILE = ROOT / "data" / "suppressed.json"
FAILURES_FILE = ROOT / "data" / "failures.json"
WINDOW_DAYS = 14  # temporary: tight recent window while tuning runs; restore to 45


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


def _write_index(records: list[Obituary]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Newest batch first, then alphabetical by name within a date.
    ordered = sorted(records, key=lambda r: r.name)
    ordered = sorted(ordered, key=lambda r: r.source_date, reverse=True)
    payload = {
        "count": len(ordered),
        "obituaries": [r.to_index_dict() for r in ordered],
    }
    INDEX_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_pages(records: list[Obituary], sponsor: dict, base_url: str) -> None:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for stale in PAGES_DIR.glob("*.html"):
        stale.unlink()  # render is authoritative: never leave an orphaned page
    for ob in records:
        (PAGES_DIR / f"{ob.slug}.html").write_text(
            render_person_page(ob, sponsor, base_url), encoding="utf-8"
        )


def render(master: Master, sponsor: dict, base_url: str, allow_empty: bool) -> None:
    """Rebuild index, pages, and sitemap from the master + manual records.

    Manual one-offs are merged in; suppressed slugs (family requests) are removed
    from everything published, though they remain in the master for the record.
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
    _write_index(records)
    _write_pages(records, sponsor, base_url)
    SITEMAP_FILE.write_text(render_sitemap(records, base_url), encoding="utf-8")
    extras = []
    if manual:
        extras.append(f"+{len(manual)} manual")
    if suppressed:
        extras.append(f"-{len(suppressed)} suppressed")
    note = f" ({', '.join(extras)})" if extras else ""
    print(f"Rendered {len(records)} pages, index, and sitemap{note}.")


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

"""Build the obituary index and per-person pages.

  python -m extract.main            # recent window (cron default)
  python -m extract.main --backfill # every obituary post ever published

Requires WEBSHARE_PROXY_URL and ANTHROPIC_API_KEY in the environment.
Any post that fails to parse aborts the run with a non-zero exit so the
GitHub Action surfaces it instead of silently shipping a gap.
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
from templates import render_person_page
from wp_client import fetch_batch_posts

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "web" / "public" / "data"
PAGES_DIR = ROOT / "web" / "public" / "o"
SPONSOR_FILE = DATA_DIR / "sponsor.json"
INDEX_FILE = DATA_DIR / "obituaries.json"
WINDOW_DAYS = 14  # temporary: tight recent window while tuning runs; restore to 45


def _load_sponsor() -> dict:
    if not SPONSOR_FILE.exists():
        raise RuntimeError(f"Missing sponsor config at {SPONSOR_FILE}")
    return json.loads(SPONSOR_FILE.read_text(encoding="utf-8"))


def _dedupe(obituaries: list[Obituary]) -> list[Obituary]:
    """Keep the first occurrence of each slug, preserving newest-first order."""
    seen: set[str] = set()
    unique: list[Obituary] = []
    for ob in obituaries:
        if ob.slug not in seen:
            seen.add(ob.slug)
            unique.append(ob)
    return unique


def _write_index(obituaries: list[Obituary]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(obituaries),
        "obituaries": [ob.to_index_dict() for ob in obituaries],
    }
    INDEX_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_pages(obituaries: list[Obituary], sponsor: dict, base_url: str) -> None:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for ob in obituaries:
        (PAGES_DIR / f"{ob.slug}.html").write_text(
            render_person_page(ob, sponsor, base_url), encoding="utf-8"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", action="store_true")
    args = parser.parse_args()

    sponsor = _load_sponsor()
    client = Anthropic()

    base_url = os.environ.get("PUBLIC_BASE_URL")
    if not base_url:
        raise RuntimeError(
            "PUBLIC_BASE_URL is not set. This is where the pages are served and "
            "indexed, e.g. https://rowanflynnpilot.github.io/wpr-obituaries"
        )
    base_url = base_url.rstrip("/")

    window = None if args.backfill else WINDOW_DAYS
    posts = fetch_batch_posts(window)
    print(f"Fetched {len(posts)} batch posts.")

    people: list[Obituary] = []
    failures: list[tuple[str, str]] = []
    for post in posts:
        try:
            people.extend(extract_obituaries(post, client))
        except Exception as exc:  # noqa: BLE001 — collect and report loudly
            failures.append((post.get("link", "unknown"), str(exc)))

    people = _dedupe(people)
    _write_index(people)
    _write_pages(people, sponsor, base_url)
    print(f"Wrote {len(people)} obituaries and {len(people)} pages.")

    if failures:
        print(f"\n{len(failures)} post(s) failed to parse:", file=sys.stderr)
        for url, err in failures:
            print(f"  {url}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

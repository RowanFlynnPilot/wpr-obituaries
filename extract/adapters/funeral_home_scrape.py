"""Funeral-home-scrape write-source: obituaries straight from the homes' sites.

The WordPress scrape re-indexes WPR's *compiled* batch posts; this source goes
one step upstream and reads the funeral homes those batches are built from. Each
enabled home in `data/funeral_homes.json` carries a `platform` + the key that
platform needs; the source enumerates that home's recent obituaries and maps
each onto the record contract.

Only the **Tukios** platform is implemented here — it covers the core
Wausau-area homes (Brainard, Helke, Peterson/Kraemer, Ascend, and the outer-ring
Beste, Rembs, Taylor-Stine-Waid) and serves fully structured records, so there
is no model extraction: one API record maps directly to one `Obituary`. The
Tribute Technology homes (Schmidt & Schulta, Buettgen, Mid-Wisconsin, Carlson)
are a separate, HTML-shaped platform and raise until built — see
docs/funeral-home-scraping.md.

A configured home is a trusted source, so scraped records publish like the WPR
batch scrape; `data/suppressed.json` remains the per-slug removal hatch.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bs4 import BeautifulSoup

import tukios
from homes import load_homes
from models import Obituary

from .base import Unit

NAME = "funeral_home_scrape"
ROOT = Path(__file__).resolve().parents[2]
HOMES_FILE = ROOT / "data" / "funeral_homes.json"


def _unit_id(public_url: str) -> int:
    """Stable per-person id from the permanent person-page URL.

    A large hash keeps these ids clear of the small WordPress post ids that key
    the other source's records, so the master's per-source-id upsert can't
    collide across sources.
    """
    return int(hashlib.sha1(public_url.encode()).hexdigest()[:12], 16)


def _revision(row: dict) -> str:
    """Content hash of the fields we publish — any edit re-emits the record."""
    material = {
        "name": row.get("display_name"),
        "dob": row.get("date_of_birth"),
        "dod": row.get("date_of_death"),
        "text": row.get("obituary_text"),
        "photo": row.get("default_image"),
    }
    return hashlib.sha1(json.dumps(material, sort_keys=True).encode()).hexdigest()[:12]


def _html_to_paragraphs(html: str) -> str:
    """Flatten obituary HTML to text, preserving paragraphs as blank-line breaks."""
    soup = BeautifulSoup(html or "", "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    blocks = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    blocks = [b for b in blocks if b]
    if not blocks:  # some records aren't wrapped in <p>
        text = soup.get_text("\n", strip=True)
        blocks = [b.strip() for b in text.split("\n") if b.strip()]
    return "\n\n".join(blocks)


def _photo_url(row: dict) -> str | None:
    """The person's portrait — prefer a larger size for downscaling on vendor."""
    sizes = row.get("default_image_sizes") or {}
    return sizes.get("lg") or row.get("default_image") or None


def _summary(name: str, age, city: str | None, formatted_dod: str | None) -> str:
    """One respectful line, shaped so the town facet can read "of <City>"."""
    parts = [name]
    if age is not None:
        parts.append(f", age {age}")
    if city:
        parts.append(f", of {city}")
    if formatted_dod:
        parts.append(f" passed away on {formatted_dod}")
    return "".join(parts) + "."


def to_obituary(row: dict, home_name: str) -> Obituary | None:
    """Map one Tukios record to an Obituary, or None if it can't be placed.

    A scraped obituary needs a name and a death date (the death date orders the
    register and stamps the slug); anything missing those is skipped loudly
    rather than published half-formed.
    """
    name = (row.get("display_name") or "").strip()
    dod = row.get("date_of_death")
    public_url = row.get("public_url")
    if not name or not dod or not public_url:
        print(f"  {NAME}: skipping incomplete record {row.get('id')!r}", file=sys.stderr)
        return None
    city = (row.get("city") or "").strip() or None
    age = row.get("age")
    uid = _unit_id(public_url)
    return Obituary(
        name=name,
        source_id=uid,
        source_url=public_url,
        source_date=dod,  # order the register by date of death
        death_year=int(dod[:4]),
        birth_date=row.get("date_of_birth"),
        death_date=dod,
        age=age,
        funeral_home=row.get("branch") or home_name,
        photo_url=_photo_url(row),
        summary=_summary(name, age, city, row.get("formatted_date_of_death")),
        body=_html_to_paragraphs(row.get("obituary_text", "")),
    )


class FuneralHomeScrape:
    """Enabled funeral-home sites, read from `data/funeral_homes.json`."""

    name = NAME
    _SUPPORTED = {"tukios"}

    def __init__(self, cfg: dict, homes_file: Path = HOMES_FILE) -> None:
        self.cfg = cfg
        self.homes = [h for h in load_homes(homes_file) if h.get("platform")]

    def _cutoff(self, window: int | None) -> str | None:
        if window is None:
            return None
        return (datetime.now(timezone.utc) - timedelta(days=window)).date().isoformat()

    def units(self, window: int | None) -> Iterator[Unit]:
        """Yield one work-unit per recent obituary across every enabled home."""
        cutoff = self._cutoff(window)
        for home in self.homes:
            platform = home["platform"]
            if platform not in self._SUPPORTED:
                raise RuntimeError(
                    f"{NAME}: home '{home['name']}' has unsupported platform "
                    f"'{platform}' (implemented: {sorted(self._SUPPORTED)})."
                )
            alias = home.get("siteAlias")
            if not alias:
                raise RuntimeError(
                    f"{NAME}: home '{home['name']}' is platform tukios but has no siteAlias."
                )
            count = 0
            for row in tukios.fetch_obituaries(alias, cutoff):
                ob = to_obituary(row, home["name"])
                if ob is None:
                    continue
                count += 1
                yield Unit(
                    source=self.name,
                    unit_id=ob.source_id,
                    modified=_revision(row),
                    ref=ob.source_url,
                    extract=lambda o=ob: [o],
                )
            print(f"  {NAME}: {home['name']} — {count} obituaries in window.")

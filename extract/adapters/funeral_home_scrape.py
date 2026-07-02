"""Funeral-home-scrape write-source: obituaries straight from the homes' sites.

The WordPress scrape re-indexes WPR's *compiled* batch posts; this source goes
one step upstream and reads the funeral homes those batches are built from. Each
enabled home in `data/funeral_homes.json` carries a `platform` + the key that
platform needs; the source enumerates that home's recent obituaries and maps
each onto the record contract.

Two platforms are implemented, both serving fully structured records (no model
extraction — one source record maps directly to one `Obituary`):

- **Tukios** — the core Wausau-area homes (Brainard, Helke, Peterson/Kraemer,
  Ascend) plus outer-ring Beste, Rembs, Taylor-Stine-Waid. Discovery + records
  come from one JSON API keyed by a per-site `siteAlias`.
- **Tribute Technology** — Schmidt & Schulta, Buettgen, Mid-Wisconsin, Carlson.
  Discovery is the site's Recent-Obituaries RSS (or the obituary sitemaps on a
  backfill); each person page carries a schema.org `Person` JSON-LD with the full
  record. Keyed by the home's own site `url`.

See docs/funeral-home-scraping.md. A configured home is a trusted source, so
scraped records publish like the WPR batch scrape; `data/suppressed.json`
remains the per-slug removal hatch.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from bs4 import BeautifulSoup

import tribute
import tukios
from homes import load_homes
from models import Obituary
from wp_client import make_session

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


def _age(birth_date: str | None, death_date: str | None) -> int | None:
    """Age at death from ISO dates — derived from stated dates, not invented."""
    if not birth_date or not death_date:
        return None
    b, d = date.fromisoformat(birth_date), date.fromisoformat(death_date)
    years = d.year - b.year - ((d.month, d.day) < (b.month, b.day))
    return years if 0 <= years <= 120 else None


# Tribute has no structured city, but the opening line reads "…, <age>, of
# <Town>, …", so the town is the capitalized run right after the age. Anchoring
# on that age is what keeps a prose opener ("In loving memory of Elizabeth…")
# from yielding the name as the town.
_CITY_RE = re.compile(r",\s*(?:age\s+)?\d{1,3},?\s+of\s+([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,2})")


def _city_from_body(body: str) -> str | None:
    """Best-effort town from a Tribute obituary's opening line, else None."""
    m = _CITY_RE.search(body or "")
    return m.group(1).strip(" ,.") if m else None


def _tribute_summary(name: str, age: int | None, city: str | None, death_str: str | None) -> str:
    """One respectful line, shaped like the Tukios summary so the town facet
    (_derive_town) reads "of <City>" when we could recover the town."""
    parts = [name]
    if age is not None:
        parts.append(f", age {age}")
    if city:
        parts.append(f", of {city}")
    if death_str:
        parts.append(f" passed away on {death_str.strip()}")
    return "".join(parts) + "."


def tribute_to_obituary(rec: dict, home_name: str) -> Obituary | None:
    """Map one Tribute person record (parsed JSON-LD) to an Obituary, or None."""
    name = (rec.get("name") or "").strip()
    death_date = tribute.parse_date(rec.get("deathDate"))
    url = rec.get("url")
    oid = rec.get("obId") or (tribute.obid(url) if url else None)
    if not name or not death_date or not url or not oid:
        print(f"  {NAME}: skipping incomplete record {url!r}", file=sys.stderr)
        return None
    birth_date = tribute.parse_date(rec.get("birthDate"))
    age = _age(birth_date, death_date)
    body = tribute.body_text(rec.get("description", ""))
    return Obituary(
        name=name,
        source_id=int(oid),
        source_url=url,
        source_date=death_date,  # order the register by date of death
        death_year=int(death_date[:4]),
        birth_date=birth_date,
        death_date=death_date,
        age=age,
        funeral_home=home_name,
        photo_url=rec.get("image"),
        summary=_tribute_summary(name, age, _city_from_body(body), rec.get("deathDate")),
        body=body,
    )


class FuneralHomeScrape:
    """Enabled funeral-home sites, read from `data/funeral_homes.json`."""

    name = NAME

    def __init__(self, cfg: dict, homes_file: Path = HOMES_FILE) -> None:
        self.cfg = cfg
        self.default_window = cfg.get("windowDays", 45)  # poll window (days) for this source
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
            if platform == "tukios":
                yield from self._tukios_units(home, cutoff)
            elif platform == "tribute":
                yield from self._tribute_units(home, cutoff, backfill=window is None)
            else:
                raise RuntimeError(
                    f"{NAME}: home '{home['name']}' has unsupported platform "
                    f"'{platform}' (implemented: tukios, tribute)."
                )

    def _tukios_units(self, home: dict, cutoff: str | None) -> Iterator[Unit]:
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

    def _tribute_units(self, home: dict, cutoff: str | None, backfill: bool) -> Iterator[Unit]:
        url = home.get("url")
        if not url:
            raise RuntimeError(
                f"{NAME}: home '{home['name']}' is platform tribute but has no url."
            )
        session = make_session()
        found = tribute.all_urls(session, url) if backfill else tribute.recent_urls(session, url, cutoff)
        count = 0
        for page_url, stamp in found:
            oid = tribute.obid(page_url)
            if not oid:
                continue
            count += 1
            # The revision (RSS pubDate / sitemap lastmod) comes from discovery, so
            # is_processed skips unchanged obituaries without fetching the page; the
            # person page is fetched only when the unit is new or changed.
            yield Unit(
                source=self.name,
                unit_id=int(oid),
                modified=stamp or "",
                ref=page_url,
                extract=lambda s=session, u=page_url, hn=home["name"]: _tribute_extract(s, u, hn),
            )
        print(f"  {NAME}: {home['name']} — {count} obituaries in window.")


def _tribute_extract(session, url: str, home_name: str) -> list[Obituary]:
    """Fetch + map one Tribute person page. Raises so a bad page is quarantined."""
    rec = tribute.person_record(session, url)
    if rec is None:
        raise ValueError(f"no Person data at {url}")
    ob = tribute_to_obituary(rec, home_name)
    if ob is None:
        raise ValueError(f"incomplete obituary at {url}")
    return [ob]

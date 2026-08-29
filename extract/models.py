"""Single source of truth for the Obituary record shape."""

from __future__ import annotations

import dataclasses
import hashlib
import re
import unicodedata
from dataclasses import dataclass


def slugify(value: str) -> str:
    """Lowercase, hyphenated, ASCII-only slug fragment.

    Accents fold to their base letters ("José" -> "jose") rather than passing
    through: \\w is Unicode-aware, and a non-ASCII slug is an invalid character
    in sitemap <loc> URLs and fragile in filenames.
    """
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    return value.strip("-")


@dataclass(frozen=True)
class Obituary:
    """One person, extracted from a daily batch post.

    name and source are required. Everything a real obituary may omit
    (dates, age, photo, funeral home) is nullable — absent data is not an
    error, but a name that cannot be found is.
    """

    name: str
    source_id: int  # WordPress post id of the batch this person came from
    source_url: str
    source_date: str  # ISO date of the batch post, e.g. "2026-06-19"
    death_year: int | None
    birth_date: str | None
    death_date: str | None
    age: int | None
    funeral_home: str | None
    photo_url: str | None
    summary: str  # one respectful sentence for cards and meta description
    body: str  # full obituary text for this person, paragraphs split by "\n\n"
    # Which write-source produced this record (e.g. "wordpress_scrape") — stamped
    # by the store at upsert so two sources can never collide on the same numeric
    # source_id. Empty only for records that never pass through the store (manual).
    source: str = ""
    # The published URL fragment: name + death year disambiguates the common
    # case; a short hash of the source post keeps two same-named people from the
    # same year distinct. Derived once (below) and then persisted in the master —
    # a correction that changes the derivation inputs (say a death year the first
    # extraction missed) must never move a page Google has already indexed, so
    # the store carries the original slug forward across re-extractions.
    slug: str = ""

    def __post_init__(self) -> None:
        if not self.slug:
            stamp = str(self.death_year) if self.death_year else self.source_date[:4]
            digest = hashlib.sha1(self.source_url.encode()).hexdigest()[:6]
            object.__setattr__(self, "slug", f"{slugify(self.name)}-{stamp}-{digest}")

    def lifespan(self) -> str:
        """'1950 – 2026', the death year alone, or '' when nothing is dated.

        The one lifespan formatter — the share card and every template use it,
        so the OG image and the page can never drift apart.
        """
        birth = self.birth_date[:4] if self.birth_date else ""
        death = (
            self.death_date[:4]
            if self.death_date
            else (str(self.death_year) if self.death_year else "")
        )
        return f"{birth} – {death}" if birth and death else death

    def excerpt(self, limit: int = 200) -> str:
        """The opening of the obituary body, trimmed at a word boundary.

        A warmer teaser than the one-line summary — used by the featured
        carousel to show "the beginning of their obituary".
        """
        first = self.body.split("\n\n")[0].strip() if self.body else ""
        if len(first) <= limit:
            return first
        return first[:limit].rsplit(" ", 1)[0].rstrip(",.;:— ") + "…"

    def to_index_dict(self) -> dict:
        """Light record for the searchable JSON index (no full body)."""
        return {
            "slug": self.slug,
            "name": self.name,
            "birthDate": self.birth_date,
            "deathDate": self.death_date,
            "deathYear": self.death_year,
            "age": self.age,
            "funeralHome": self.funeral_home,
            "photoUrl": self.photo_url,
            "summary": self.summary,
            "excerpt": self.excerpt(),
            "sourceUrl": self.source_url,
            "sourceDate": self.source_date,
        }

    def to_record_dict(self) -> dict:
        """Full record (incl. body + source) for the persistent master store."""
        return dataclasses.asdict(self)

    @classmethod
    def from_record_dict(cls, record: dict) -> "Obituary":
        """Rebuild from a master-store record. Field names must match exactly."""
        return cls(**record)

    @classmethod
    def from_submission(
        cls, d: dict, *, source_id: int, source_url: str, source_date: str
    ) -> "Obituary":
        """Build from a loose, human/structured dict (manual entry, intake form).

        The caller supplies provenance (source_id/url/date); everything else is
        read leniently — absent optional fields stay null, summary/body default
        sensibly, and a missing name raises (a record without a name is invalid).
        """
        name = (d.get("name") or "").strip()
        if not name:
            raise ValueError(f"Record with no name: {d}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", source_date or ""):
            # Fail here, where the bad entry is attributable — a malformed date
            # that reaches render would fail the *whole* site (feed/archive
            # parse every record's date), the opposite of one-bad-record safety.
            raise ValueError(
                f"Record '{name}' has invalid source_date {source_date!r} "
                "(need YYYY-MM-DD)"
            )
        summary = (d.get("summary") or f"{name}.").strip()
        body = (d.get("body") or summary).strip()
        return cls(
            name=name,
            source_id=source_id,
            source_url=source_url,
            source_date=source_date,
            death_year=d.get("death_year"),
            birth_date=d.get("birth_date"),
            death_date=d.get("death_date"),
            age=d.get("age"),
            funeral_home=d.get("funeral_home"),
            photo_url=d.get("photo_url"),
            summary=summary,
            body=body,
        )

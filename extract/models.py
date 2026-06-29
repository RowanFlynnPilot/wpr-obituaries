"""Single source of truth for the Obituary record shape."""

from __future__ import annotations

import dataclasses
import hashlib
import re
from dataclasses import dataclass


def slugify(value: str) -> str:
    """Lowercase, hyphenated, ASCII-only slug fragment."""
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

    @property
    def slug(self) -> str:
        """Deterministic, collision-resistant URL slug for this person.

        name + death year disambiguates the common case; a short hash of the
        source post keeps two same-named people from the same year distinct.
        """
        stamp = str(self.death_year) if self.death_year else self.source_date[:4]
        digest = hashlib.sha1(self.source_url.encode()).hexdigest()[:6]
        return f"{slugify(self.name)}-{stamp}-{digest}"

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

"""Single source of truth for the Obituary record shape."""

from __future__ import annotations

import dataclasses
import hashlib
import re
import unicodedata
from dataclasses import dataclass


_PENDING = re.compile(
    r"obituary[^.]*\b(?:pending|forthcoming|to follow|(?:will|to) be posted|will posted|when available)"
    r"|check back",
    re.IGNORECASE,
)

_NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}

# A nickname in parentheses or quotes is not part of the name, and a *trailing*
# one would otherwise be read as the surname: the funeral home's "Patrick
# Michael McFaul (Coach Mac)" keyed as "patrick mac" and so never matched the
# same man arriving from the newsroom's batch as "Patrick Michael McFaul".
# Removing the span beats blanking its punctuation, which is what let the
# nickname's own words become tokens.
_NICKNAME = re.compile(r"[(\[][^)\]]*[)\]]|[\"“”'‘’][^\"“”'‘’]*[\"“”'‘’]")


def name_key(name: str) -> str:
    """First + last name, lowercased, stripping middles, initials, suffixes,
    nicknames, and punctuation.

    The same person reaches us from two sources (or two extractions) under
    slightly different names — "Ryan Johnson" vs "Ryan Paul Johnson", a middle
    initial, a suffix, a quoted or parenthesized nickname. Keying on first +
    last collapses those to one person; callers add the death date to keep two
    same-named people apart.
    """
    bare = _NICKNAME.sub(" ", name)
    if not bare.strip():  # a record that is only a nickname keeps what it has
        bare = name
    tokens = re.sub(r"[^\w\s]", " ", bare.lower()).split()
    tokens = [t for t in tokens if t not in _NAME_SUFFIXES]
    if not tokens:
        return name.lower().strip()
    if len(tokens) == 1:
        return tokens[0]
    return f"{tokens[0]} {tokens[-1]}"


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
    """One person, as produced by any write-source (a WordPress batch post,
    a funeral home's own site, a reviewed intake submission).

    name and source are required. Everything a real obituary may omit
    (dates, age, photo, funeral home) is nullable — absent data is not an
    error, but a name that cannot be found is.
    """

    name: str
    source_id: int  # unit id within its source: WP post id, Tukios hash, Tribute obId, intake id
    source_url: str
    source_date: str  # ISO date that orders the register: batch post date, or death date for scraped/intake
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
    # Two facts only a funeral home's own feed states outright, so they are
    # recorded when a source gives them and never guessed from the text:
    # military service, and the date of the next service (visitation, funeral
    # or burial — the notice itself carries the times and places).
    veteran: bool = False
    service_date: str | None = None
    # A funeral home can hide a date on its own site (a family's wish, or a
    # placeholder it never meant to show). The date stays in the record, because
    # matching one person across sources depends on it, but it is withheld from
    # everything published: see public_birth / public_death.
    hide_birth: bool = False
    hide_death: bool = False

    def __post_init__(self) -> None:
        if not self.slug:
            stamp = str(self.death_year) if self.death_year else self.source_date[:4]
            digest = hashlib.sha1(self.source_url.encode()).hexdigest()[:6]
            object.__setattr__(self, "slug", f"{slugify(self.name)}-{stamp}-{digest}")

    @property
    def public_birth(self) -> str | None:
        """The birth date as it may be published (None when the home hides it)."""
        return None if self.hide_birth else self.birth_date

    @property
    def public_death(self) -> str | None:
        """The death date as it may be published (None when the home hides it)."""
        return None if self.hide_death else self.death_date

    def lifespan(self) -> str:
        """'1950 – 2026', the death year alone, or '' when nothing is dated.

        The one lifespan formatter — the share card and every template use it,
        so the OG image and the page can never drift apart.
        """
        birth = self.public_birth[:4] if self.public_birth else ""
        death = (
            self.public_death[:4]
            if self.public_death
            else (str(self.death_year) if self.death_year and not self.hide_death else "")
        )
        return f"{birth} – {death}" if birth and death else death

    @property
    def awaiting_text(self) -> bool:
        """True when the body is the funeral home's stand-in, not an obituary.

        A home lists a person before the family's text arrives ("The obituary
        will posted when available.", "Full obituary and service details are
        pending."). That line is the home's note to its own visitors; published
        as the notice it reads as if that were all there is to say.
        """
        return len(self.body.split()) < 25 and bool(_PENDING.search(self.body))

    def excerpt(self, limit: int = 200) -> str:
        """The opening of the obituary body, trimmed at a word boundary.

        A warmer teaser than the one-line summary — used by the featured
        carousel to show "the beginning of their obituary".
        """
        if self.awaiting_text:
            return ""
        first = self.body.split("\n\n")[0].strip() if self.body else ""
        if len(first) <= limit:
            return first
        return first[:limit].rsplit(" ", 1)[0].rstrip(",.;:— ") + "…"

    def to_index_dict(self) -> dict:
        """Light record for the searchable JSON index (no full body)."""
        return {
            "slug": self.slug,
            "name": self.name,
            "birthDate": self.public_birth,
            "deathDate": self.public_death,
            "deathYear": None if self.hide_death else self.death_year,
            "age": self.age,
            "funeralHome": self.funeral_home,
            "photoUrl": self.photo_url,
            "summary": self.summary,
            "excerpt": self.excerpt(),
            "sourceDate": self.source_date,
            **({"veteran": True} if self.veteran else {}),
            **({"serviceDate": self.service_date} if self.service_date else {}),
        }

    def to_record_dict(self) -> dict:
        """Full record (incl. body + source) for the persistent master store.

        The two feed-only facts are written only when set, so the thousand-odd
        records that have neither stay byte-identical in the committed master.
        """
        record = dataclasses.asdict(self)
        for optional in ("veteran", "service_date", "hide_birth", "hide_death"):
            if not record[optional]:
                del record[optional]
        return record

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

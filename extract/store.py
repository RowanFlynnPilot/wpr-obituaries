"""The persistent master store — the source of truth that lets pages outlive
the fetch window.

Each run reads this file, adds only the people from *new or changed* batch
posts, writes it back, and re-renders every page from it. Because rendering is
driven entirely by the master (never by just the current window), a per-person
page never disappears once published, and a template change reaches every page
on the next render.

On-disk shape (`data/obituaries_master.json`):

    {
      "version": 2,
      "posts": { "<source>:<unit_id>": "<modified_gmt>" },  # every unit processed
      "records": [ {<full Obituary record>}, ... ]          # sorted oldest-first
    }

`posts` records *every* processed unit — including ones that yielded zero
obituaries — so we never re-spend an extraction call on an unchanged unit. The
key is namespaced by source (`wordpress_scrape:12345`) so two write-sources can
never collide on the same numeric id. v1 files (bare `<unit_id>` keys, all from
the WordPress scraper) are migrated on load.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from models import Obituary, slugify

VERSION = 2


@dataclass
class Master:
    """In-memory view of the master store."""

    posts: dict[str, str] = field(default_factory=dict)
    records: list[Obituary] = field(default_factory=list)

    def is_processed(self, source: str, unit_id: int, modified: str) -> bool:
        """True if this source-unit was already extracted at this exact revision."""
        return self.posts.get(f"{source}:{unit_id}") == modified

    def upsert_post(
        self, source: str, unit_id: int, modified: str, people: list[Obituary]
    ) -> None:
        """Replace this unit's people with a freshly extracted set.

        Dropping the unit's prior records first makes re-extraction (a correction
        to a batch) idempotent, and recording the unit even when `people` is empty
        stops us from re-extracting a person-less unit every run. The processed
        key is namespaced by source so sources can't collide on the same id.
        """
        self.records = [r for r in self.records if r.source_id != unit_id]
        self.records.extend(people)
        self.posts[f"{source}:{unit_id}"] = modified


def _migrate_posts(posts: dict[str, str], version: int) -> dict[str, str]:
    """v1 `posts` keys were bare unit ids, all from the WordPress scraper.

    Namespace them so the processed-map matches the v2 source-qualified scheme.
    Idempotent: keys already namespaced (containing ':') are left alone.
    """
    if version >= 2:
        return posts
    return {
        (k if ":" in k else f"wordpress_scrape:{k}"): v for k, v in posts.items()
    }


def load_master(path: Path) -> Master:
    """Read the master store, or return an empty one if it does not exist yet."""
    if not path.exists():
        return Master()
    data = json.loads(path.read_text(encoding="utf-8"))
    posts = _migrate_posts(dict(data.get("posts", {})), int(data.get("version", 1)))
    return Master(
        posts=posts,
        records=[Obituary.from_record_dict(r) for r in data.get("records", [])],
    )


def _post_sort_key(item: tuple[str, str]) -> tuple:
    """Order processed keys by (source, numeric id) for stable, readable diffs."""
    source, _, rest = item[0].partition(":")
    return (source, int(rest)) if rest.isdigit() else (source, 0, rest)


def save_master(master: Master, path: Path) -> None:
    """Write the master store with deterministic, append-stable ordering.

    Records are sorted oldest-first by (source_date, slug) so that adding a new
    batch appends near the end and produces a small, readable git diff instead
    of rewriting the whole file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(master.records, key=lambda r: (r.source_date, r.slug))
    payload = {
        "version": VERSION,
        "posts": dict(sorted(master.posts.items(), key=_post_sort_key)),
        "records": [r.to_record_dict() for r in ordered],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_suppressed(path: Path) -> set[str]:
    """Slugs the newsroom has asked us never to publish (e.g. a family request).

    Each entry is a slug string, or an object with a `slug` key (an optional
    `reason` is for the editor's own record). Suppression is applied at render,
    so the record stays in the master but never reaches the site or sitemap.
    """
    if not path.exists():
        return set()
    slugs: set[str] = set()
    for item in json.loads(path.read_text(encoding="utf-8")):
        if isinstance(item, str):
            slugs.add(item)
        elif isinstance(item, dict) and item.get("slug"):
            slugs.add(item["slug"])
    return slugs


def load_manual(path: Path) -> list[Obituary]:
    """Hand-entered obituaries that don't come from a WPR batch post.

    For one-offs (a stray notice, an out-of-town funeral home). Only `name` and
    `source_date` (YYYY-MM-DD, used for ordering) are required; everything else
    defaults sensibly. These live only here, so the incremental sync never
    touches them and they persist across runs.
    """
    if not path.exists():
        return []
    out: list[Obituary] = []
    for d in json.loads(path.read_text(encoding="utf-8")):
        name = (d.get("name") or "").strip()
        if not name:
            raise ValueError(f"Manual record with no name: {d}")
        source_date = d.get("source_date") or d.get("date")
        if not source_date:
            raise ValueError(f"Manual record '{name}' is missing source_date")
        summary = (d.get("summary") or f"{name}.").strip()
        body = (d.get("body") or summary).strip()
        out.append(
            Obituary(
                name=name,
                source_id=int(d.get("source_id", 0)),
                source_url=d.get("source_url") or f"manual:{slugify(name)}-{source_date}",
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
        )
    return out

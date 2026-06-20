"""Canonicalize the newsroom's many funeral-home name variants to one home.

The raw `funeral_home` strings vary wildly (chapels, abbreviations, typos), so we
map each to a canonical home via the substrings in data/funeral_homes.json. Used
to link the home name to its website and to group the per-home landing pages.
"""

from __future__ import annotations

import json
from pathlib import Path

from models import slugify


def load_homes(path: Path) -> list[dict]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8")).get("homes", [])
    return [
        {
            "name": h["name"],
            "url": h.get("url"),
            "slug": slugify(h["name"]),
            "match": [m.lower() for m in h.get("match", [])],
        }
        for h in raw
    ]


def resolve_home(funeral_home: str | None, homes: list[dict]) -> dict | None:
    """The canonical home for a raw funeral-home string (first match wins)."""
    if not funeral_home:
        return None
    low = funeral_home.lower()
    for home in homes:
        if any(m in low for m in home["match"]):
            return home
    return None

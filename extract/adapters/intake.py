"""Intake write-source: family / funeral-home submissions — the universal path.

Unlike `wordpress_scrape` (a WPR-shaped batch scraper), intake works for any
newsroom: a submission is *already-structured* obituary data, so there is no
model extraction — a unit just maps fields to an `Obituary`. Approved
submissions live in `data/intake/<id>.json` and flow through sync into the
master, so they are deduped, photo-vendored, and permanent exactly like scraped
records. `manual.json` stays as the quick editor hatch; this is the reviewed
product path.

The unit's revision stamp is a content hash, so any edit to an approved
submission re-emits it automatically — no manual version bumping.

Backends:
- "manual": read approved submission files from `data/intake/` (review by merge).
- "supabase": (Step 5) pull approved rows from the submissions table.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Iterator
from pathlib import Path

from models import Obituary

from .base import Unit

NAME = "intake"
ROOT = Path(__file__).resolve().parents[2]
INTAKE_DIR = ROOT / "data" / "intake"


def _revision(sub: dict) -> str:
    """Stable content hash — changes whenever the submission's data changes."""
    return hashlib.sha1(json.dumps(sub, sort_keys=True).encode()).hexdigest()[:12]


def submission_to_obituary(sub: dict) -> Obituary:
    """Map one approved submission to an Obituary record."""
    sid = int(sub["id"])
    return Obituary.from_submission(
        sub,
        source_id=sid,
        source_url=f"intake:{sid}",
        source_date=sub["source_date"],
    )


class IntakeManual:
    """Approved submissions from `data/intake/<id>.json` (the no-infra backend)."""

    name = NAME

    def __init__(self, intake_dir: Path = INTAKE_DIR) -> None:
        self.dir = intake_dir

    def units(self, window: int | None) -> Iterator[Unit]:
        """Yield a unit per *approved* submission. window does not apply here."""
        if not self.dir.exists():
            return
        for path in sorted(self.dir.glob("*.json")):
            sub = json.loads(path.read_text(encoding="utf-8"))
            if sub.get("status") != "approved":
                continue  # pending / rejected never reach the site
            try:
                sid = int(sub["id"])
            except (KeyError, TypeError, ValueError):
                print(f"  intake: skipping {path.name} — missing/invalid id", file=sys.stderr)
                continue
            yield Unit(
                source=self.name,
                unit_id=sid,
                modified=_revision(sub),
                ref=str(path),
                extract=lambda s=sub: [submission_to_obituary(s)],
            )

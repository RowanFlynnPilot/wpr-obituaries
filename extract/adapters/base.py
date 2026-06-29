"""The contract every write-source conforms to.

A *source* yields *units* of work. A unit is one extractable thing (a WordPress
batch post, an approved intake submission) identified by `source` + `unit_id` at
a given `modified` revision, plus a thunk that produces the people. The sync loop
in `main` is the only consumer — it skips units the master has already processed
at the same revision, then upserts the rest. Sources never touch the master or
the renderer; that's what keeps them swappable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from models import Obituary


@dataclass
class Unit:
    """One unit of extractable work from a source."""

    source: str  # the source name, e.g. "wordpress_scrape" — namespaces the master key
    unit_id: int  # stable id within the source
    modified: str  # revision stamp; an unchanged stamp means "skip, already done"
    ref: str  # human-readable reference for error reporting (e.g. a post URL)
    extract: Callable[[], list[Obituary]]  # produce this unit's people (may be costly)

"""Write-source registry: which adapters are live for this newsroom.

Every adapter conforms to the same `Unit`-yielding contract (see `base.py`), so
the sync loop never knows where a record came from. Enabled sources are declared
in `newsroom.config.json` under `adapters`; secrets (API keys, proxy) stay in the
environment. Intake is added here in a later step.
"""

from __future__ import annotations

from anthropic import Anthropic

from config import Newsroom

from .base import Unit
from .wordpress_scrape import WordpressScrape

__all__ = ["Unit", "enabled_sources"]


def enabled_sources(newsroom: Newsroom, client: Anthropic) -> list:
    """Instantiate the sources this newsroom has switched on."""
    sources = []
    if newsroom.adapter("wordpress_scrape").get("enabled"):
        sources.append(WordpressScrape(newsroom.adapter("wordpress_scrape"), client))
    return sources

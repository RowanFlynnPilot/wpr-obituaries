"""Write-source registry: which adapters are live for this newsroom.

Every adapter conforms to the same `Unit`-yielding contract (see `base.py`), so
the sync loop never knows where a record came from. Enabled sources are declared
in `newsroom.config.json` under `adapters`; secrets (API keys, proxy) stay in the
environment.
"""

from __future__ import annotations

from config import Newsroom

from .base import Unit
from .funeral_home_scrape import FuneralHomeScrape
from .intake import IntakeManual
from .wordpress_scrape import WordpressScrape

__all__ = ["Unit", "enabled_sources"]


def enabled_sources(newsroom: Newsroom) -> list:
    """Instantiate the sources this newsroom has switched on.

    Cheap — no network and no API client. A source builds whatever it needs
    (e.g. the Anthropic client for wordpress_scrape) lazily, on first use.
    """
    sources = []
    if newsroom.adapter("wordpress_scrape").get("enabled"):
        sources.append(WordpressScrape(newsroom.adapter("wordpress_scrape")))
    if newsroom.adapter("funeral_home_scrape").get("enabled"):
        sources.append(FuneralHomeScrape(newsroom.adapter("funeral_home_scrape")))
    intake = newsroom.adapter("intake")
    if intake.get("enabled"):
        backend = intake.get("backend", "manual")
        if backend == "manual":
            sources.append(IntakeManual())
        else:
            raise RuntimeError(
                f"intake backend '{backend}' is not supported yet (Step 5: supabase)."
            )
    return sources

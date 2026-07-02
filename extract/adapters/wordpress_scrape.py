"""WordPress-scrape write-source: the original WPR pull path, lifted as-is.

Wraps `wp_client.fetch_batch_posts` (the proxied Newspack/WP REST pull) and
`extractor.extract_obituaries` (Haiku splits a batch post into people) behind the
generic source interface in this package. The internals are untouched — this is a
WPR-shaped adapter (it assumes batch posts with several people each), shipped
*disabled by default* in the template because most newsrooms don't publish obits
that way. Intake is the universal path.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator

from extractor import extract_obituaries
from wp_client import fetch_batch_posts

from .base import Unit

NAME = "wordpress_scrape"


class WordpressScrape:
    """One enabled WordPress source, configured from `adapters.wordpress_scrape`."""

    name = NAME

    def __init__(self, cfg: dict) -> None:
        # Loud KeyError if a fork enables this source without an apiBase.
        self.api_base = cfg["apiBase"]
        self.category_slug = cfg.get("categorySlug", "obituaries")
        self.default_window = cfg.get("windowDays", 14)  # poll window (days) for this source
        self._client = None

    @property
    def client(self):
        """The Anthropic client, built lazily on first extraction.

        Constructing it here (not at registry time) means an intake-only fork
        never needs ANTHROPIC_API_KEY just to enumerate sources or run tests.
        """
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic(max_retries=4)
        return self._client

    def units(self, window: int | None) -> Iterator[Unit]:
        """Yield one work-unit per batch post in the window (newest first)."""
        posts = fetch_batch_posts(window, self.api_base, self.category_slug)
        print(f"Fetched {len(posts)} batch posts.")
        if not posts:
            print(
                "WARNING: 0 posts fetched — possible proxy/Cloudflare block.",
                file=sys.stderr,
            )
        for post in posts:
            modified = post.get("modified_gmt") or post.get("modified") or post["date"]
            yield Unit(
                source=self.name,
                unit_id=int(post["id"]),
                modified=modified,
                ref=post.get("link", "unknown"),
                extract=lambda p=post: extract_obituaries(p, self.client),
            )

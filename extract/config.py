"""Load and validate the per-newsroom config.

`newsroom.config.json` (repo root) is the single declarative file that turns
this template into a specific newsroom's site: identity, branding, and which
write-source adapters are enabled. Both runtimes read it — Python here, and Vite
on the widget side — so there is exactly one place to rebrand a fork.

Secrets never live here. API keys and the proxy URL stay in the environment, and
`PUBLIC_BASE_URL` stays in the deploy env because the canonical URL must point at
the real serving location. A missing *required* key raises immediately: a broken
precondition is an error, not something to paper over with a default.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "newsroom.config.json"


@dataclass(frozen=True)
class Newsroom:
    """The branding + identity a newsroom's pages render with.

    Adapter settings stay in `raw["adapters"]` — they're consumed by the source
    layer, not the renderer, so they don't belong in this flat view.
    """

    name: str
    short_name: str
    url: str
    coverage_area: str
    submissions_email: str
    logo_url: str
    seal_path: str
    accent: str
    paper: str
    fonts_url: str
    serif: str
    nameplate: str
    mono: str
    raw: dict

    def adapter(self, key: str) -> dict:
        """Settings block for one write-source adapter (empty if unconfigured)."""
        return self.raw.get("adapters", {}).get(key, {})


def _require(section: dict, key: str, where: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"newsroom.config.json: '{where}.{key}' is required and must be a "
            f"non-empty string."
        )
    return value


def load_newsroom(path: Path = CONFIG_FILE) -> Newsroom:
    """Read + validate the newsroom config, raising loudly on anything missing."""
    if not path.exists():
        raise RuntimeError(
            f"Missing newsroom config at {path}. Copy and fill newsroom.config.json."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    identity = data.get("identity") or {}
    branding = data.get("branding") or {}
    return Newsroom(
        name=_require(identity, "name", "identity"),
        short_name=_require(identity, "shortName", "identity"),
        url=_require(identity, "url", "identity"),
        coverage_area=_require(identity, "coverageArea", "identity"),
        submissions_email=_require(identity, "submissionsEmail", "identity"),
        logo_url=_require(branding, "logoUrl", "branding"),
        seal_path=_require(branding, "sealPath", "branding"),
        accent=_require(branding, "accent", "branding"),
        paper=_require(branding, "paper", "branding"),
        fonts_url=_require(branding, "fontsUrl", "branding"),
        serif=_require(branding, "serif", "branding"),
        nameplate=_require(branding, "nameplate", "branding"),
        mono=_require(branding, "mono", "branding"),
        raw=data,
    )

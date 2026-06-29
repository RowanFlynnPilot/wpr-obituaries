"""Instantiate this template for a new newsroom.

Walks you through the few values a fork must set, writes `newsroom.config.json`,
validates it, and (optionally, via the `gh` CLI) sets the Pages URL repo
variable. Secrets are never handled here — the script prints the exact
`gh secret set` commands for you to run yourself.

    python scripts/bootstrap.py            # interactive
    python scripts/bootstrap.py --help

The template ships **intake-only** (families submit via the widget form). Enable
the WordPress scraper only if your newsroom publishes batch obituary posts like
WPR does.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "newsroom.config.json"

# The shared newsroom type system (WPR-derived). A fork keeps these unless it
# wants a different look; only identity + logo + accent normally change.
BRAND_DEFAULTS = {
    "sealPath": "assets/seal.png",
    "paper": "#f6f2ea",
    "fontsUrl": (
        "https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;"
        "0,400;0,700;1,300;1,400&family=Oswald:wght@400;500;600;700&"
        "family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap"
    ),
    "serif": '"Merriweather", Georgia, serif',
    "nameplate": '"Oswald", "Arial Narrow", sans-serif',
    "mono": '"Courier Prime", "Courier New", monospace',
}


def make_config(a: dict) -> dict:
    """Build the newsroom.config.json structure from a flat answers dict.

    Pure (no IO) so it can be tested. Required identity/branding keys must be
    present in `a`; everything else falls back to the shared defaults.
    """
    coverage = a["coverageArea"]
    return {
        "identity": {
            "name": a["name"],
            "shortName": a["shortName"],
            "url": a["url"],
            "coverageArea": coverage,
            "submissionsEmail": a["submissionsEmail"],
        },
        "branding": {
            "logoUrl": a["logoUrl"],
            "sealPath": a.get("sealPath") or BRAND_DEFAULTS["sealPath"],
            "accent": a.get("accent") or "#7c2e36",
            "paper": a.get("paper") or BRAND_DEFAULTS["paper"],
            "fontsUrl": a.get("fontsUrl") or BRAND_DEFAULTS["fontsUrl"],
            "serif": a.get("serif") or BRAND_DEFAULTS["serif"],
            "nameplate": a.get("nameplate") or BRAND_DEFAULTS["nameplate"],
            "mono": a.get("mono") or BRAND_DEFAULTS["mono"],
        },
        "copy": {
            "lede": a.get("lede") or f"Remembering the lives of {coverage}.",
            "footerTagline": a.get("footerTagline") or "local journalism.",
        },
        "adapters": {
            "wordpress_scrape": {
                "enabled": bool(a.get("wp_enabled")),
                "apiBase": a.get("wp_apiBase", ""),
                "categorySlug": a.get("wp_categorySlug") or "obituaries",
                "windowDays": int(a.get("wp_windowDays") or 14),
            },
            "intake": {
                "enabled": a.get("intake_enabled", True),
                "backend": "manual",
            },
        },
    }


def _ask(prompt: str, *, default: str = "", required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{prompt}{suffix}: ").strip() or default
        if value or not required:
            return value
        print("  (required)")


def _ask_yes(prompt: str, *, default: bool = False) -> bool:
    d = "Y/n" if default else "y/N"
    ans = input(f"{prompt} [{d}]: ").strip().lower()
    if not ans:
        return default
    return ans.startswith("y")


def gather() -> dict:
    print("\nNewsroom identity\n-----------------")
    a: dict = {
        "name": _ask("Full name (e.g. Wausau Pilot & Review)", required=True),
        "shortName": _ask("Short name / initials (e.g. WPR)", required=True),
        "url": _ask("Homepage URL", required=True),
        "coverageArea": _ask("Coverage area (e.g. Wausau and Marathon County)", required=True),
        "submissionsEmail": _ask("Submissions email", required=True),
    }
    print("\nBranding\n--------")
    a["logoUrl"] = _ask("Logo image URL", required=True)
    a["accent"] = _ask("Accent color (hex)", default="#7c2e36")
    a["sealPath"] = _ask(
        "Masthead seal image path (place the file at web/public/<path>)",
        default=BRAND_DEFAULTS["sealPath"],
    )
    print("\nSources\n-------")
    print("The template is intake-only by default (families submit via the form).")
    a["wp_enabled"] = _ask_yes("Also scrape a WordPress 'obituaries' category?", default=False)
    if a["wp_enabled"]:
        a["wp_apiBase"] = _ask(
            "WordPress REST base (e.g. https://example.com/wp-json/wp/v2)", required=True
        )
        a["wp_categorySlug"] = _ask("Obituary category slug", default="obituaries")
    return a


def write_config(cfg: dict, path: Path) -> None:
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(path: Path) -> None:
    """Load the written file through the real loader so a bad value fails here."""
    sys.path.insert(0, str(ROOT / "extract"))
    from config import load_newsroom  # noqa: E402 — extract/ is on the path now

    load_newsroom(path)


def _gh_available() -> bool:
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def maybe_set_pages_url(base_url: str) -> None:
    if not base_url or not _gh_available():
        return
    if _ask_yes(f"Set the PUBLIC_BASE_URL repo variable to {base_url} via gh?", default=True):
        subprocess.run(["gh", "variable", "set", "PUBLIC_BASE_URL", "--body", base_url], check=False)


def next_steps(cfg: dict, base_url: str) -> None:
    wp = cfg["adapters"]["wordpress_scrape"]["enabled"]
    print("\nDone. newsroom.config.json written.\n")
    print("Next steps:")
    print(f"  1. Drop your seal image at  web/public/{cfg['branding']['sealPath']}")
    print("  2. Set sponsors in          web/public/data/sponsor.json")
    if not base_url:
        print("  3. Set the Pages URL var:   gh variable set PUBLIC_BASE_URL --body <url>")
    if wp:
        print("  4. Set secrets:             gh secret set ANTHROPIC_API_KEY")
        print("                              gh secret set WEBSHARE_PROXY_URL")
        print("     Then seed the master:    python extract/main.py --days 180")
    else:
        print("  4. Approve a submission:    add data/intake/<id>.json (status approved)")
    print("  5. Preview locally:         python extract/main.py --render-only")
    print("     (set PUBLIC_BASE_URL in your env first)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Instantiate this template for a new newsroom.")
    parser.add_argument(
        "--output", type=Path, default=CONFIG_FILE, help="where to write the config"
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing config without asking"
    )
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        if not _ask_yes(f"{args.output.name} exists — overwrite?", default=False):
            print("Aborted.")
            return 1

    answers = gather()
    base_url = _ask("\nPublic base URL where the site is served (optional now)", default="")
    cfg = make_config(answers)
    write_config(cfg, args.output)
    validate(args.output)
    maybe_set_pages_url(base_url)
    next_steps(cfg, base_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

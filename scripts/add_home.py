"""Onboard a funeral home into data/funeral_homes.json.

Given a funeral home's website, detect its platform, extract + verify the
scraping key, and add the config entry — the friction the funeral_home_scrape
adapter otherwise puts on a new newsroom (know the platform, dig the siteAlias
out of page source, confirm it returns obituaries). This runs in Python, not the
browser, on purpose: the detection fetch is cross-origin and often Cloudflare-
fronted, so a browser app can't make it — curl_cffi can (see
docs/funeral-home-scraping.md).

    python scripts/add_home.py https://www.example-fh.com
    python scripts/add_home.py https://www.example-fh.com --write
    python scripts/add_home.py https://www.example-fh.com --write --match beste

Without --write it prints the verified entry to paste. With --write it inserts
the entry into data/funeral_homes.json, preserving the one-home-per-line format
(existing lines stay byte-identical, so the diff is a single added line). The
derived `match` token is a best guess — review it; it must be a lowercase
substring of how the home names itself on its obituaries, so records link to the
canonical home.

Both implemented platforms are auto-detected: Tukios (keyed by the extracted
siteAlias, verified against the live API) and Tribute Technology (keyed by the
site url, verified via its Recent-Obituaries RSS).
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "extract"))

import tribute  # noqa: E402
import tukios  # noqa: E402
from wp_client import make_session  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HOMES_FILE = ROOT / "data" / "funeral_homes.json"

# Where a home's obituary listing usually lives, relative to its root.
OBIT_PATHS = ("/obituaries", "/obituaries/obituary-listings", "")
_MATCH_JUNK = ("funeralhomes", "funeralhome", "funeralservice", "funeral", "cremation", "fh")


def detect_platform(html: str) -> tuple[str, str | None]:
    """(platform, alias) from a page's HTML. alias is None unless Tukios + found."""
    alias = tukios.find_site_alias(html)
    low = html.lower()
    if alias or "tukios" in low:
        return ("tukios", alias)
    if "tributecenteronline" in low or "frazer" in low:
        return ("tribute", None)
    return ("unknown", None)


def derive_match(name: str, host: str) -> list[str]:
    """Best-guess match token: the brand label from the domain, junk stripped."""
    label = host.split(":")[0].split(".")[0]
    if label == "www":
        label = host.split(".")[1] if "." in host else host
    for junk in _MATCH_JUNK:
        label = label.replace(junk, "")
    label = label.strip("-")
    return [label] if label else [name.split()[0].lower()]


def format_home_line(entry: dict) -> str:
    """One home as a single JSON line matching the file's existing style.

    siteAlias is emitted only for platforms that use one (Tukios); Tribute homes
    are keyed by url alone.
    """
    keys = [k for k in ("name", "url", "match", "platform", "siteAlias") if k in entry]
    body = ", ".join(f"{json.dumps(k)}: {json.dumps(entry[k])}" for k in keys)
    return "    { " + body + " }"


def insert_home(text: str, entry: dict) -> str:
    """Insert one home line before the homes-array close, leaving others intact."""
    lines = text.split("\n")
    closes = [i for i, ln in enumerate(lines) if ln == "  ]"]
    if len(closes) != 1:
        raise RuntimeError("could not locate the homes array — add the entry by hand")
    close = closes[0]
    last = close - 1
    while last > 0 and not lines[last].strip():
        last -= 1
    if not lines[last].rstrip().endswith("}"):
        raise RuntimeError("unexpected format before homes array close")
    lines[last] = lines[last] + ","
    lines.insert(close, format_home_line(entry))
    return "\n".join(lines)


def _fetch_listing(session, base: str) -> tuple[str, str] | None:
    """Return (page_url, html) for the first candidate path that loads, else None."""
    root = base.rstrip("/")
    for path in OBIT_PATHS:
        url = root + path
        try:
            resp = session.get(url, timeout=tukios.TIMEOUT)
        except Exception as exc:  # noqa: BLE001 — try the next candidate path
            print(f"  fetch failed for {url}: {exc}", file=sys.stderr)
            continue
        if resp.status_code < 400 and resp.text:
            return url, resp.text
    return None


def _existing(**criteria: str) -> str | None:
    """Name of an already-configured home matching all given fields, if any."""
    if not HOMES_FILE.exists():
        return None
    for home in json.loads(HOMES_FILE.read_text(encoding="utf-8")).get("homes", []):
        if all(home.get(k) == v for k, v in criteria.items()):
            return home.get("name")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Onboard a funeral home into the scrape config.")
    parser.add_argument("url", help="the funeral home's website (root or obituaries page)")
    parser.add_argument("--write", action="store_true", help="insert into data/funeral_homes.json")
    parser.add_argument("--name", help="override the home name (default: from the live API)")
    parser.add_argument("--match", help="override the match token (default: derived from the domain)")
    args = parser.parse_args()

    session = make_session()
    found = _fetch_listing(session, args.url)
    if not found:
        print(f"Could not load an obituaries page under {args.url}.", file=sys.stderr)
        return 1
    page_url, html = found
    platform, alias = detect_platform(html)
    host = urlsplit(page_url).netloc
    root = f"{urlsplit(page_url).scheme}://{host}"

    if platform == "tukios":
        if not alias:
            print(f"Tukios detected at {page_url} but no siteAlias in the page source.", file=sys.stderr)
            return 1
        dup = _existing(siteAlias=alias)
        if dup:
            print(f"Already configured: '{dup}' uses siteAlias {alias}. Nothing to do.")
            return 0
        summary = tukios.site_summary(alias)
        if summary["total"] < 1:
            print(f"Alias {alias!r} resolved to '{summary['location_name']}' with 0 "
                  f"obituaries — likely the wrong key.", file=sys.stderr)
            return 1
        name = args.name or summary["location_name"]
        entry = {"name": name, "url": root,
                 "match": [args.match] if args.match else derive_match(name, host),
                 "platform": "tukios", "siteAlias": alias}
        print(f"Verified Tukios home: {name} — {summary['total']} obituaries, alias {alias}.")

    elif platform == "tribute":
        session = make_session()
        recent = [u for u, _ in itertools.islice(tribute.recent_urls(session, root, None), 1)]
        if not recent:
            print(f"Tribute Technology detected at {page_url} but its RSS lists no "
                  f"obituaries.", file=sys.stderr)
            return 1
        dup = _existing(url=root)
        if dup:
            print(f"Already configured: '{dup}' at {root}. Nothing to do.")
            return 0
        name = args.name or tribute.firm_name(session, root) or host
        entry = {"name": name, "url": root,
                 "match": [args.match] if args.match else derive_match(name, host),
                 "platform": "tribute"}
        print(f"Verified Tribute Technology home: {name} at {root}.")

    else:
        print(f"Could not recognize the platform at {page_url}. Supported: Tukios, Tribute.", file=sys.stderr)
        return 1

    print(format_home_line(entry).strip())

    if args.write:
        text = HOMES_FILE.read_text(encoding="utf-8")
        HOMES_FILE.write_text(insert_home(text, entry), encoding="utf-8")
        print(f"\nAdded to {HOMES_FILE.relative_to(ROOT)}. Review the `match` token "
              f"(must be a lowercase substring of the home's name on its obituaries).")
    else:
        print("\nRe-run with --write to add it to data/funeral_homes.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Vendor obituary portraits locally.

Portraits otherwise hotlink WPR's Cloudflare CDN — fragile and slow. We download
each one once (through the same proxied, browser-impersonating session as the
posts, since the images sit behind the same Cloudflare), downscale it, and save
it under web/public/assets/photos/<slug>.jpg, committed alongside the master.

Vendoring runs in the sync phase (proxy available). Render then prefers the
local copy and falls back to the remote URL for anything not yet vendored, so a
big first-run backlog can drain over several runs (PER_RUN_LIMIT) without ever
breaking a page.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from PIL import Image

from models import Obituary

MAX_EDGE = 450  # portraits never render larger than this
QUALITY = 82
PER_RUN_LIMIT = 200  # bound the one-time backfill; new photos each run are few


def local_filename(slug: str) -> str:
    return f"{slug}.jpg"


def vendored_slugs(photos_dir: Path) -> set[str]:
    """Slugs that already have a local portrait."""
    if not photos_dir.exists():
        return set()
    return {p.stem for p in photos_dir.glob("*.jpg")}


def _load_manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def vendor_photos(
    records: list[Obituary],
    photos_dir: Path,
    session,
    manifest_file: Path,
    limit: int = PER_RUN_LIMIT,
) -> int:
    """Download + downscale new or changed portraits. Returns the count saved.

    The manifest (slug -> source URL, committed alongside the master) is what
    lets a *corrected* upstream photo re-vendor: a vendored file whose recorded
    source URL no longer matches the record's is stale and downloads again.
    Photos vendored before the manifest existed adopt their current URL as the
    baseline rather than re-downloading the whole catalogue.
    """
    photos_dir.mkdir(parents=True, exist_ok=True)
    have = vendored_slugs(photos_dir)
    manifest = _load_manifest(manifest_file)
    saved = 0
    for ob in records:
        if not ob.photo_url:
            continue
        if ob.slug in have and manifest.setdefault(ob.slug, ob.photo_url) == ob.photo_url:
            continue
        if saved >= limit:
            break
        try:
            resp = session.get(ob.photo_url, timeout=30)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            img.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
            img.save(photos_dir / local_filename(ob.slug), "JPEG", quality=QUALITY, optimize=True)
            manifest[ob.slug] = ob.photo_url
            saved += 1
        except Exception as exc:  # noqa: BLE001 — one bad image must not stop the rest
            print(f"  photo failed for {ob.slug}: {exc}", file=sys.stderr)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(
        json.dumps(dict(sorted(manifest.items())), indent=2), encoding="utf-8"
    )
    return saved

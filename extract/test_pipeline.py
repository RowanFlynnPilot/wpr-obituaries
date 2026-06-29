"""Regression tests for the obituary pipeline.

No framework needed — run it directly (also wired into the GitHub Action so a
broken build never deploys):

    python extract/test_pipeline.py
"""

from __future__ import annotations

import json
import tempfile
import xml.dom.minidom
from pathlib import Path

import config
import extractor
import homes
import main
import store
import templates
from models import Obituary

NEWSROOM = config.load_newsroom()


def mk(name, sid, date, *, body="body text here", death_date=None, death_year=2026,
       birth_date=None, age=None, funeral_home=None, photo_url=None):
    return Obituary(
        name=name, source_id=sid, source_url=f"http://x/{sid}/{name}", source_date=date,
        death_year=death_year, birth_date=birth_date, death_date=death_date, age=age,
        funeral_home=funeral_home, photo_url=photo_url, summary=f"{name} died.", body=body,
    )


def test_models():
    a = mk("Jane Q. Doe", 1, "2026-06-10")
    assert a.slug.startswith("jane-q-doe-2026-")
    assert Obituary.from_record_dict(a.to_record_dict()) == a
    long = mk("X", 1, "2026-06-10", body="First sentence is plenty long. " * 20)
    assert long.excerpt().endswith("…") and len(long.excerpt()) <= 205
    print("ok: models (slug, record round-trip, excerpt)")


def test_store():
    m = store.Master()
    m.upsert_post(10, "m1", [mk("A A", 10, "2026-06-10"), mk("B B", 10, "2026-06-10")])
    m.upsert_post(11, "m1", [])  # person-less post still recorded
    assert m.is_processed(10, "m1") and not m.is_processed(10, "m2") and m.is_processed(11, "m1")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "master.json"
        store.save_master(m, p)
        m2 = store.load_master(p)
        assert len(m2.records) == 2 and set(m2.posts) == {"10", "11"}
        m2.upsert_post(10, "m2", [mk("A A", 10, "2026-06-10")])  # correction
        assert len([r for r in m2.records if r.source_id == 10]) == 1
    print("ok: store (upsert, person-less, correction, round-trip)")


def test_homes():
    hs = homes.load_homes(main.HOMES_FILE)
    assert resolve(hs, "Brainard Funeral Home - Everest Chapel")["url"]
    assert resolve(hs, "HELKE FUNERAL HOME & CREMATION")["name"].startswith("Helke")
    assert resolve(hs, "Some Unknown Home") is None
    print("ok: homes (canonicalize variants, unmatched -> None)")


def resolve(hs, name):
    return homes.resolve_home(name, hs)


def test_dedupe():
    short = mk("Sam Lee", 1, "2026-06-01", body="short", death_date="2026-05-30")
    full = mk("Sam Lee", 2, "2026-06-05", body="the full obituary " * 30, death_date="2026-05-30")
    other = mk("Pat Roe", 3, "2026-06-05", death_date="2026-06-01")
    canonical, primary_by_slug = main._dedupe_people([short, full, other])
    assert len(canonical) == 2  # Sam Lee collapses
    assert primary_by_slug[short.slug].slug == full.slug  # fuller record wins
    assert primary_by_slug[full.slug].slug == full.slug
    print("ok: dedupe (same person collapses, fuller body is primary)")


def test_photo_resolution():
    vend = mk("V V", 1, "2026-06-10", photo_url="http://cdn/x.jpg")
    rem = mk("R R", 2, "2026-06-10", photo_url="http://cdn/y.jpg")
    vendored = {vend.slug}
    assert main._index_photo(vend, vendored) == f"assets/photos/{vend.slug}.jpg"
    assert main._index_photo(rem, vendored) == "http://cdn/y.jpg"
    assert main._page_photo(vend, vendored, "http://b") == f"http://b/assets/photos/{vend.slug}.jpg"
    print("ok: photo resolution (vendored -> local, else remote)")


def test_sitemap_and_feed():
    recs = [mk("A A", 1, "2026-06-10"), mk("B B", 2, "2026-06-09")]
    sm = templates.render_sitemap(recs, "http://b", ["helke"])
    xml.dom.minidom.parseString(sm)
    assert sm.count("<loc>") == 4 and "/funeral-home/helke.html" in sm  # index + 2 + 1 home
    feed = templates.render_feed(recs, "http://b", NEWSROOM)
    xml.dom.minidom.parseString(feed)
    assert feed.count("<item>") == 2 and "<pubDate>" in feed
    print("ok: sitemap + feed (well-formed, correct counts)")


def test_sanity_warnings():
    bad_dates = mk("X", 1, "2026-06-10", birth_date="2026-01-01", death_date="2020-01-01")
    assert any("after death" in w for w in extractor.sanity_warnings(bad_dates))
    bad_age = mk("Y", 1, "2026-06-10", age=200)
    assert any("implausible age" in w for w in extractor.sanity_warnings(bad_age))
    good = mk("Z", 1, "2026-06-10", birth_date="1950-01-01", death_date="2026-01-01", age=76)
    assert extractor.sanity_warnings(good) == []
    print("ok: sanity warnings (flag bad, pass good)")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("\nALL PASS")

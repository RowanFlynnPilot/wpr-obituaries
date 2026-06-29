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
    src = "wordpress_scrape"
    m = store.Master()
    m.upsert_post(src, 10, "m1", [mk("A A", 10, "2026-06-10"), mk("B B", 10, "2026-06-10")])
    m.upsert_post(src, 11, "m1", [])  # person-less unit still recorded
    assert m.is_processed(src, 10, "m1") and not m.is_processed(src, 10, "m2")
    assert m.is_processed(src, 11, "m1")
    assert not m.is_processed("intake", 10, "m1")  # source namespacing isolates ids
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "master.json"
        store.save_master(m, p)
        m2 = store.load_master(p)
        assert len(m2.records) == 2 and set(m2.posts) == {f"{src}:10", f"{src}:11"}
        m2.upsert_post(src, 10, "m2", [mk("A A", 10, "2026-06-10")])  # correction
        assert len([r for r in m2.records if r.source_id == 10]) == 1
    print("ok: store (upsert, person-less, correction, namespacing, round-trip)")


def test_store_migration():
    # A v1 file keyed by bare post ids migrates to source-namespaced keys, so an
    # already-processed post is still recognized and not re-extracted.
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "master.json"
        p.write_text('{"version": 1, "posts": {"42": "m1"}, "records": []}', encoding="utf-8")
        m = store.load_master(p)
        assert m.posts == {"wordpress_scrape:42": "m1"}
        assert m.is_processed("wordpress_scrape", 42, "m1")
    print("ok: store migration (v1 bare ids -> namespaced)")


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


def test_intake():
    from adapters.intake import IntakeManual
    with tempfile.TemporaryDirectory() as d:
        dd = Path(d)
        (dd / "1001.json").write_text(json.dumps({
            "id": 1001, "status": "approved", "name": "Jane Q. Doe",
            "source_date": "2026-06-28", "death_date": "2026-06-20", "body": "Full text.",
        }), encoding="utf-8")
        (dd / "1002.json").write_text(json.dumps({
            "id": 1002, "status": "pending", "name": "Not Yet", "source_date": "2026-06-28",
        }), encoding="utf-8")
        units = list(IntakeManual(dd).units(None))
        assert len(units) == 1, units  # pending is skipped
        u = units[0]
        assert u.source == "intake" and u.unit_id == 1001
        people = u.extract()
        assert len(people) == 1
        ob = people[0]
        assert ob.name == "Jane Q. Doe" and ob.source_url == "intake:1001"
        assert ob.summary == "Jane Q. Doe." and ob.body == "Full text."
        # An edit changes the content-hash revision (so it re-emits on sync).
        before = u.modified
        (dd / "1001.json").write_text(json.dumps({
            "id": 1001, "status": "approved", "name": "Jane Q. Doe",
            "source_date": "2026-06-28", "death_date": "2026-06-20", "body": "Edited text.",
        }), encoding="utf-8")
        assert list(IntakeManual(dd).units(None))[0].modified != before
    print("ok: intake (approved emits, pending skipped, maps to Obituary, hash revisions)")


def test_enabled_sources():
    import config
    from adapters import enabled_sources
    names = [s.name for s in enabled_sources(config.load_newsroom())]
    assert names == ["wordpress_scrape", "intake"], names  # WPR runs both
    print("ok: enabled_sources (wordpress + intake per WPR config)")


def test_bootstrap_config():
    import importlib.util
    root = Path(main.__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("bootstrap", root / "scripts" / "bootstrap.py")
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)
    cfg = bootstrap.make_config({
        "name": "Acme County Times", "shortName": "ACT", "url": "https://acme.example",
        "coverageArea": "Acme County", "submissionsEmail": "obits@acme.example",
        "logoUrl": "https://acme.example/logo.png",
    })
    assert cfg["adapters"]["intake"]["enabled"]                       # intake-only by default
    assert not cfg["adapters"]["wordpress_scrape"]["enabled"]
    assert cfg["branding"]["accent"] == "#7c2e36"                     # default brand applied
    assert cfg["copy"]["lede"] == "Remembering the lives of Acme County."
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "newsroom.config.json"
        bootstrap.write_config(cfg, p)
        config.load_newsroom(p)                                       # must pass the real loader
    print("ok: bootstrap (make_config defaults + validates via loader)")


def test_og_cache_hash():
    a = mk("Jane Doe", 1, "2026-06-10", death_year=2026)
    fp = main._og_brand_fingerprint(NEWSROOM, "Obituaries · Helke")
    h = main._og_input_hash(a, None, fp)
    assert main._og_input_hash(a, None, fp) == h                  # stable
    fp2 = main._og_brand_fingerprint(NEWSROOM, "Obituaries · Other")
    assert main._og_input_hash(a, None, fp2) != h                 # brand change busts
    b = mk("Jane Doe", 1, "2026-06-10", death_year=2025)
    assert main._og_input_hash(b, None, fp) != h                  # record change busts
    print("ok: og cache hash (stable, brand- and record-sensitive)")


def test_analytics():
    import analytics
    assert analytics.head_snippet({}) == ""                          # disabled -> nothing
    assert analytics.event_script({"provider": ""}) == ""
    assert analytics.sponsor_track_attrs({}, "Helke") == ""
    pl = analytics.head_snippet({"provider": "plausible", "domain": "x.org"})
    assert 'data-domain="x.org"' in pl and "plausible.io/js/script.js" in pl
    gc = analytics.head_snippet({"provider": "goatcounter", "site": "wpr"})
    assert "wpr.goatcounter.com/count" in gc
    cf = analytics.head_snippet({"provider": "cloudflare", "site": "tok123"})
    assert "cloudflareinsights.com" in cf and "tok123" in cf
    assert analytics.head_snippet({"provider": "custom", "headHtml": "<b>x</b>"}) == "<b>x</b>"
    on = {"provider": "plausible", "domain": "x.org"}
    assert "trackEvent" in analytics.event_script(on)
    assert 'data-track-event="Sponsor click"' in analytics.sponsor_track_attrs(on, "Helke")
    print("ok: analytics (providers, events, disabled no-ops)")


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

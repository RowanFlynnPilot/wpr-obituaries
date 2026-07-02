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

    # name normalization for cross-source dedupe
    assert main._name_key("Ryan Paul Johnson") == "ryan johnson"        # middle dropped
    assert main._name_key("James Erdman Sr.") == "james erdman"          # suffix dropped
    assert main._name_key('Mildred "Milly" Mary Anne Pries') == "mildred pries"  # nickname dropped
    assert main._name_key("Cher") == "cher"

    # a WPR "Ryan Johnson" and a funeral-home "Ryan Paul Johnson" (same death
    # date) collapse to one; the fuller record wins
    a = mk("Ryan Johnson", 4, "2026-06-10", body="x", death_date="2026-06-08")
    b = mk("Ryan Paul Johnson", 5, "2026-06-11", body="fuller " * 20, death_date="2026-06-08")
    canon2, prim2 = main._dedupe_people([a, b])
    assert len(canon2) == 1 and prim2[a.slug].slug == b.slug
    # but two different people who share a first+last and a death date stay apart
    c = mk("Mary Q. Adams", 6, "2026-06-10", death_date="2026-06-08")
    d = mk("Mary Z. Baker", 7, "2026-06-10", death_date="2026-06-08")
    assert len(main._dedupe_people([c, d])[0]) == 2

    # a WPR record with only a death year folds into the funeral-home record that
    # has the full date (same person, same year)
    yr = mk("Kay Solberg", 8, "2026-06-01", death_date=None, death_year=2026)
    dated = mk("Kay Solberg", 9, "2026-05-27", death_date="2026-05-27", death_year=2026)
    assert len(main._dedupe_people([yr, dated])[0]) == 1
    # but if two same-named people died that year, the ambiguous year-only stays apart
    d1 = mk("Lee Park", 10, "2026-03-02", death_date="2026-03-01", death_year=2026)
    d2 = mk("Lee Park", 11, "2026-09-02", death_date="2026-09-01", death_year=2026)
    yr2 = mk("Lee Park", 12, "2026-06-01", death_date=None, death_year=2026)
    assert len(main._dedupe_people([d1, d2, yr2])[0]) == 3  # not merged into either
    print("ok: dedupe (name-variant + year-only collapse, ambiguous kept apart)")


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
    assert names == ["wordpress_scrape", "funeral_home_scrape", "intake"], names
    print("ok: enabled_sources (wordpress + funeral_home_scrape + intake per WPR config)")


def _tukios_row(**over):
    row = {
        "id": "5e036d4e-776f-4e3f-a9bc-afef025b4523",
        "display_name": "Naomi C. Hardman",
        "date_of_birth": "1943-12-13",
        "date_of_death": "2026-06-26",
        "formatted_date_of_death": "Jun 26, 2026",
        "age": 82,
        "city": "Ringle",
        "branch": "Brainard Funeral Home and Cremation Center- Everest Chapel",
        "is_published": True,
        "public_url": "https://www.brainardfuneral.com/obituaries/naomi-hardman",
        "obituary_text": "<p>Naomi was a redeemed child of God.</p><p>She loved her family.</p>",
        "default_image": "https://cdn.tukioswebsites.com/uuid/md",
        "default_image_sizes": {"lg": "https://cdn.tukioswebsites.com/uuid/lg"},
    }
    row.update(over)
    return row


def test_funeral_home_scrape():
    from adapters import funeral_home_scrape as fhs

    ob = fhs.to_obituary(_tukios_row(), "Brainard Funeral Home & Cremation Center")
    assert ob.name == "Naomi C. Hardman"
    assert ob.death_date == "2026-06-26" and ob.death_year == 2026
    assert ob.source_date == "2026-06-26"  # register orders by date of death
    assert ob.birth_date == "1943-12-13" and ob.age == 82
    assert ob.funeral_home.startswith("Brainard")  # branch preferred
    assert ob.photo_url.endswith("/lg")  # larger size for downscaling
    assert ob.body == "Naomi was a redeemed child of God.\n\nShe loved her family."
    assert main._derive_town(ob.summary) == "Ringle"  # summary shaped for the facet
    # id + slug are stable and derived from the permanent person-page URL
    assert ob.source_id == fhs._unit_id(ob.source_url)
    assert fhs.to_obituary(_tukios_row(), "X").slug == ob.slug

    # branch falls back to the home name; a record missing name/dod is skipped
    assert fhs.to_obituary(_tukios_row(branch=None), "Helke Funeral Home").funeral_home == "Helke Funeral Home"
    assert fhs.to_obituary(_tukios_row(date_of_death=None), "X") is None
    assert fhs.to_obituary(_tukios_row(display_name="  "), "X") is None

    # content-hash revision changes when a published field is edited
    before = fhs._revision(_tukios_row())
    assert fhs._revision(_tukios_row()) == before
    assert fhs._revision(_tukios_row(obituary_text="<p>New.</p>")) != before
    print("ok: funeral_home_scrape (maps Tukios record, town facet, stable id, hash revision)")


def test_tukios_client():
    import tukios

    assert tukios.find_site_alias("var x; siteAlias = '7aacd58f'; more") == "7aacd58f"
    assert tukios.find_site_alias("'SiteAlias': 'cc8364ed'") == "cc8364ed"
    assert tukios.find_site_alias("no alias here") is None

    # Windowing tolerates a pinned out-of-order old record (some homes feature one
    # at the top), drops unpublished rows, and stops only on an all-old page.
    pages = {
        1: {"last_page": 3, "data": [
            {"date_of_death": "2026-04-10", "display_name": "Pinned Old", "is_published": True},
            {"date_of_death": "2026-06-26", "display_name": "New One", "is_published": True},
            {"date_of_death": "2026-06-20", "display_name": "Hidden", "is_published": False},
        ]},
        2: {"last_page": 3, "data": [
            {"date_of_death": "2026-06-05", "display_name": "Also Recent", "is_published": True},
            {"date_of_death": "2026-05-01", "display_name": "Too Old", "is_published": True},
        ]},
        3: {"last_page": 3, "data": [{"date_of_death": "2026-04-01", "display_name": "Older", "is_published": True}]},
    }
    orig = tukios._get_page
    tukios._get_page = lambda session, alias, page: pages[page]
    try:
        got = [r["display_name"] for r in tukios.fetch_obituaries("alias", cutoff="2026-06-01")]
    finally:
        tukios._get_page = orig
    # Pinned Old filtered (not a stop trigger), Hidden skipped, page 3 all-old -> stop
    assert got == ["New One", "Also Recent"], got
    print("ok: tukios client (alias regex, pinned-record windowing, unpublished skipped)")


_PERSON_LD = """
<html><head>
<script type="application/ld+json">{"@type":"Event","name":"Service"}</script>
<script type="application/ld+json">{ bad json }</script>
<script type="application/ld+json">{"@type":"Person","name":"Diane V. Dombeck",
 "birthDate":" October 11, 1952","deathDate":"June 24, 2026",
 "image":"https://cdn/Obituaries/48850499/Thumbnail.jpg",
 "description":"&lt;p&gt;Diane V. Dombeck, 73, of Eland, passed away.&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;She loved gardening.&lt;/p&gt;"}</script>
</head></html>
"""


def test_tribute_client():
    import tribute

    assert tribute.obid("https://x/obituaries/Jane-Doe?obId=48850499") == "48850499"
    assert tribute.parse_date(" October 11, 1952") == "1952-10-11"
    assert tribute.parse_date("June 24, 2026") == "2026-06-24"
    assert tribute.parse_date("2026") is None  # partial dates don't guess
    assert tribute.body_text("&lt;p&gt;One.&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;Two.&lt;/p&gt;") == "One.\n\nTwo."

    # Person JSON-LD is pulled out past sibling/broken blocks
    person = tribute._parse_person_ld(_PERSON_LD)
    assert person["name"] == "Diane V. Dombeck" and person["deathDate"] == "June 24, 2026"

    # RSS discovery yields newest-first and stops at the cutoff — no network
    rss = (b'<?xml version="1.0"?><rss><channel>'
           b'<item><link>https://x/obituaries/A?obId=101</link><pubDate>Fri, 26 Jun 2026 08:00:00 -0500</pubDate></item>'
           b'<item><link>https://x/obituaries/B?obId=102</link><pubDate>Wed, 10 Jun 2026 08:00:00 -0500</pubDate></item>'
           b'<item><link>https://x/obituaries/C?obId=103</link><pubDate>Sun, 01 May 2026 08:00:00 -0500</pubDate></item>'
           b'</channel></rss>')
    orig = tribute._get
    tribute._get = lambda session, url: type("R", (), {"content": rss, "text": ""})()
    try:
        got = [tribute.obid(u) for u, _ in tribute.recent_urls(None, "https://x", cutoff="2026-06-01")]
    finally:
        tribute._get = orig
    assert got == ["101", "102"], got  # stops before the May item
    print("ok: tribute client (obid, date parse, body unescape, JSON-LD, RSS window)")


def test_tribute_mapping():
    from adapters import funeral_home_scrape as fhs

    rec = {
        "name": "Diane V. Dombeck", "birthDate": " October 11, 1952", "deathDate": "June 24, 2026",
        "description": "&lt;p&gt;Diane V. Dombeck, 73, of Eland, passed away.&lt;/p&gt;",
        "image": "https://cdn/Obituaries/48850499/Thumbnail.jpg",
        "url": "https://www.schmidtschulta.com/obituaries/Diane-Veronica-Dombeck?obId=48850499",
        "obId": "48850499",
    }
    ob = fhs.tribute_to_obituary(rec, "Schmidt & Schulta Funeral Home")
    assert ob.name == "Diane V. Dombeck"
    assert ob.birth_date == "1952-10-11" and ob.death_date == "2026-06-24"
    assert ob.source_date == "2026-06-24" and ob.death_year == 2026
    assert ob.age == 73  # computed from the dates (born Oct, died Jun -> not yet 74)
    assert ob.source_id == 48850499 and ob.funeral_home.startswith("Schmidt")
    assert ob.body == "Diane V. Dombeck, 73, of Eland, passed away."
    # town recovered from the opening line (age-anchored) flows into the summary
    assert ob.summary == "Diane V. Dombeck, age 73, of Eland passed away on June 24, 2026."
    assert main._derive_town(ob.summary) == "Eland"
    # a prose opener without an age before "of" yields no false town
    assert fhs._city_from_body("In loving memory of Elizabeth, who was 44.") is None
    assert fhs._city_from_body("Someone, 70, of Rib Mountain, WI, died.") == "Rib Mountain"
    assert fhs.tribute_to_obituary({**rec, "deathDate": None}, "X") is None  # needs a death date
    assert fhs._age("1952-10-11", "2026-06-24") == 73
    assert fhs._age(None, "2026-06-24") is None
    print("ok: tribute mapping (dates parsed, age computed, body unescaped, skip incomplete)")


def _load_add_home():
    import importlib.util
    root = Path(main.__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("add_home", root / "scripts" / "add_home.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_add_home():
    ah = _load_add_home()

    # platform detection from page HTML (no network)
    assert ah.detect_platform("... siteAlias = '7aacd58f'; ...") == ("tukios", "7aacd58f")
    assert ah.detect_platform("powered by Tukios") == ("tukios", None)
    assert ah.detect_platform("api.secure.tributecenteronline.com") == ("tribute", None)
    assert ah.detect_platform("<html>plain site</html>") == ("unknown", None)

    # match token derived from the domain, junk stripped
    assert ah.derive_match("Brainard Funeral Home", "www.brainardfuneral.com") == ["brainard"]
    assert ah.derive_match("Beste Funeral Home", "www.bestefh.com") == ["beste"]

    # the entry line matches the file's style, and inserting keeps other lines intact
    entry = {"name": "Test FH", "url": "https://t.example", "match": ["test"],
             "platform": "tukios", "siteAlias": "abc123ef"}
    line = ah.format_home_line(entry)
    assert line == '    { "name": "Test FH", "url": "https://t.example", "match": ["test"], "platform": "tukios", "siteAlias": "abc123ef" }'
    # a Tribute entry has no siteAlias — the key is omitted, not emitted null
    trib = ah.format_home_line({"name": "T", "url": "https://t", "match": ["t"], "platform": "tribute"})
    assert trib == '    { "name": "T", "url": "https://t", "match": ["t"], "platform": "tribute" }'
    src = '{\n  "homes": [\n    { "name": "A", "url": null, "match": ["a"] }\n  ]\n}'
    out = ah.insert_home(src, entry)
    assert '"name": "A", "url": null, "match": ["a"] },' in out  # prior last gains a comma
    assert out.count(line) == 1
    assert json.loads(out)  # still valid JSON
    print("ok: add_home (platform detect, match derive, entry format, clean insert)")


def test_per_source_window():
    import store
    from adapters.funeral_home_scrape import FuneralHomeScrape
    from adapters.wordpress_scrape import WordpressScrape

    # each source carries its own configured poll window
    assert WordpressScrape({"apiBase": "x", "windowDays": 14}).default_window == 14
    assert FuneralHomeScrape({"windowDays": 45}).default_window == 45
    assert FuneralHomeScrape({}).default_window == 45  # sensible default when unset

    # sync gives each source ITS window normally, --days overrides all, --backfill=all
    seen: dict = {}

    class FakeSrc:
        def __init__(self, name, dw):
            self.name, self.default_window = name, dw

        def units(self, window):
            seen[self.name] = window
            return iter(())

    def run(**kw):
        seen.clear()
        main.sync(store.Master(), [FakeSrc("wp", 14), FakeSrc("fh", 45)], **kw)
        return dict(seen)

    assert run(backfill=False, days=None) == {"wp": 14, "fh": 45}   # own defaults
    assert run(backfill=False, days=7) == {"wp": 7, "fh": 7}         # --days overrides both
    assert run(backfill=True, days=None) == {"wp": None, "fh": None}  # --backfill = all
    print("ok: per-source window (own default, --days overrides, --backfill=all)")


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


def test_derive_town():
    cases = {
        "David A. Pautz, age 68, of Irma, Wisconsin passed away on June 22, 2026.": "Irma",
        "Lori Jane Steinke, age 64, of Wausau passed away on June 18, 2026.": "Wausau",
        "Judy May Kivlin, 90, of Wausau, Wisconsin, passed away.": "Wausau",
        "Kevin R. Damask, 53, of Rib Mountain, passed away unexpectedly.": "Rib Mountain",
        "Julia Katheryn Minter, age 66, passed away on June 22, 2026.": None,  # no town
        "Someone, 70, of Wisconsin Rapids, Wisconsin, died.": "Wisconsin Rapids",
    }
    for summary, expected in cases.items():
        assert main._derive_town(summary) == expected, (summary, main._derive_town(summary))
    print("ok: derive town (clean towns, multi-word, no false positives)")


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

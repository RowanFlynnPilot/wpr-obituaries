"""Browser smoke test of the built site: the things a reader does, against the real catalogue.

`extract/test_pipeline.py` proves the data layer; this proves the register a
reader gets. It serves `web/dist` (after `npm run build`), drives a headless
browser through it, and exits non-zero on the first thing that does not work,
so a change that breaks search or a person's page never deploys.

Nothing here names a person: every check picks its subject from the catalogue
as it stands that day.

Usage: python scripts/smoke_test.py   (needs `pip install playwright` + `playwright install chromium`)
"""

from __future__ import annotations

import functools
import http.server
import json
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

DIST = Path(__file__).resolve().parents[1] / "web" / "dist"
LIVE = "https://obituaries.wausaupilotandreview.com/"


def serve() -> tuple[http.server.ThreadingHTTPServer, str]:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass

    handler = functools.partial(Quiet, directory=str(DIST))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def local(route) -> None:
    """Pages reference the public base URL; answer those requests from the build."""
    path = route.request.url[len(LIVE):].split("?")[0].split("#")[0] or "index.html"
    target = DIST.joinpath(*path.split("/"))
    if target.is_file():
        route.fulfill(path=str(target))
    else:  # as the host does: the not-found page, at the address asked for
        route.fulfill(status=404, path=str(DIST / "404.html"))


def check(condition, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    index = json.loads((DIST / "data" / "obituaries.json").read_text(encoding="utf-8"))
    people = index["obituaries"]
    check(len(people) > 100, f"index has only {len(people)} people")
    httpd, base = serve()
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route(LIVE + "**", local)

        def search(text: str) -> None:
            page.fill("#obit-search", text)
            page.wait_for_timeout(250)

        names = lambda: page.locator(".entry__name").all_inner_texts()

        # the register loads, with its count and rows
        page.goto(base + "/")
        page.wait_for_selector(".entry__link")
        check("names" in page.inner_text(".search__count"), "no count line under the search")
        first = names()[0]
        print(f"ok: register loads ({len(people)} people; first row {first!r})")

        # a surname finds its person; a slip in it still does (close spellings)
        target = next(o["name"] for o in people if len(o["name"].split()[-1].strip('."')) >= 7
                      and o["name"].split()[-1].isalpha())
        surname = target.split()[-1]
        search(surname)
        check(target in names(), f"searching {surname!r} did not list {target!r}")
        slip = surname[:2] + surname[3:]
        search(slip)
        check(any(surname in n for n in names()), f"the misspelling {slip!r} did not reach {surname!r}")
        print(f"ok: search finds {surname!r}, and {slip!r} reaches it")

        # a name nobody has: a way forward, and browsing from it hides the slideshow
        search("zzqxvk")
        check(page.locator(".register__action").count() == 3, "empty state lacks its three ways forward")
        page.click("text=Browse by last name")
        page.wait_for_selector(".browse__panel")
        check(page.locator(".featured").count() == 0, "the slideshow shows while browsing")
        letter = page.locator(".browse__letter").nth(2)
        chosen = letter.text_content().strip()
        letter.click()
        page.wait_for_timeout(250)
        heading = page.locator(".register__date").first.text_content()  # the DOM text, not its uppercase styling
        check(f"beginning with {chosen}" in heading, f"the letter browse is headed {heading!r}")
        check(f"letter={chosen}" in page.url, "the browse is not mirrored into the URL")
        print(f"ok: empty state, browse by last name ({chosen}), URL state")

        # shared links reopen their view
        if any(o.get("veteran") for o in people):
            page.goto(base + "/?veterans=1")
            page.wait_for_selector(".entry__link")
            spans = page.locator(".entry__span").all_inner_texts()
            check(spans and all("Veteran" in s for s in spans), "the veterans view lists someone unmarked")
            print(f"ok: veterans view ({len(spans)} rows shown)")

        # a person's page: name, structured data, the portrait viewer
        page.goto(base + "/")
        page.wait_for_selector(".entry__link")
        page.locator(".entry__link").first.click()
        page.wait_for_selector("h1")
        check(page.inner_text("h1").strip() == first, f"the first row did not open {first!r}")
        for block in page.locator('script[type="application/ld+json"]').all_inner_texts():
            json.loads(block)
        if page.locator("button.portrait").count():
            page.click("button.portrait")
            check(page.evaluate("document.getElementById('lightbox').open"), "the portrait viewer did not open")
            page.keyboard.press("Escape")
            check(not page.evaluate("document.getElementById('lightbox').open"), "Escape did not close the viewer")
        check(page.locator(".share__btn").count() == 4, "the share row is incomplete")
        print("ok: person page (name, structured data, portrait viewer, share row)")

        # a service date carries its calendar file
        served = next((o for o in people if o.get("serviceDate")), None)
        if served:
            page.goto(f"{base}/o/{served['slug']}.html")
            check(page.locator(".service time").count() == 1, "a page with a service date has no Service line")
            ics = (DIST / "o" / f"{served['slug']}.ics").read_text(encoding="utf-8")
            check("BEGIN:VEVENT" in ics and served["serviceDate"].replace("-", "") in ics, "bad calendar file")
            print("ok: service line and calendar file")

        # an address that holds nothing: the not-found page offers the name in it
        page.goto(LIVE + "o/jane-a-nobody-2026-0a1b2c.html")
        check(page.input_value("#lost-q") == "jane a nobody", "the not-found page did not read the name")
        page.fill("#lost-q", surname)
        page.click(".lost__go")
        page.wait_for_selector(".entry__link")
        check(target in names(), f"searching from the not-found page did not list {target!r}")
        print("ok: not-found page carries the reader to a name")

        # the mini widget, the archive, the year page
        page.goto(base + "/mini.html")
        page.wait_for_selector(".mini__card")
        dots = page.locator(".mini__dot")
        check(dots.count() > 1 and page.locator('.mini__dot[tabindex="0"]').count() == 1, "mini dots are not one tab stop")
        check(page.locator(".mini__pause").count() == 1, "the mini widget has no Pause control")
        page.goto(base + "/archive.html")
        check(page.locator(".list li").count() >= len(people), "the archive is missing people")
        for year in index.get("memoriamYears", []):
            page.goto(f"{base}/in-memoriam-{year}.html")
            check(page.locator(".list li").count() > 100, f"In Memoriam {year} is nearly empty")
        print("ok: mini widget, archive, In Memoriam")
        browser.close()
    httpd.shutdown()
    check(not errors, f"page errors: {errors[:3]}")
    print("\nSMOKE PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nSMOKE FAIL: {e}", file=sys.stderr)
        sys.exit(1)

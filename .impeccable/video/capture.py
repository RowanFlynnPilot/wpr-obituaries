"""Capture the WPR Obituaries screens for the walkthrough video: the register, browse, a search typed letter by
letter, the in-text mentions, one person's page, its share row and its printed keepsake. Real web fonts, a pinned
clock and a seeded Math.random (the Recently Remembered draw), at 2.5-3x so the screens stay sharp when the
composition scales them. Requests for the live domain are answered from web/dist, so nothing depends on the edge.
Writes shots/*.png and shots/layout.json (crop sizes and the positions the choreography needs).

Usage: python .impeccable/video/capture.py   (from the repo root, after `npm --prefix web run build`; fonts need network)"""
import datetime, functools, http.server, json, os, shutil, threading
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
DIST = os.path.join(ROOT, 'web', 'dist')
SHOTS = os.path.join(HERE, 'shots')
LIVE = 'https://obituaries.wausaupilotandreview.com/'
NOW = datetime.datetime(2026, 11, 20, 10, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-6)))
TZ = 'America/Chicago'
TYPED = 'Kruger'                        # what the video types: the name spelled by ear, to show close spellings
QUERY = 'Krueger'                       # one name, three notices that name a Krueger parent: the evidence line's case
PERSON = 'donald-g-williams-2026-3e7ba0'   # a veteran with a service date: the page scene shows both, and the calendar button
SEED = 7
HIDE = ('*,*::before,*::after{transition:none!important;animation:none!important;caret-color:transparent!important}'
        ' ::-webkit-scrollbar{display:none}')
SEEDED_RANDOM = """(() => { let s = %d >>> 0; Math.random = () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; })();""" % SEED


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, 'http://127.0.0.1:%d' % httpd.server_address[1]


def local(route):
    """the live domain, answered from the build: pages render their portraits and logos from absolute URLs"""
    path = route.request.url[len(LIVE):].split('?')[0].split('#')[0] or 'index.html'
    f = os.path.join(DIST, *path.split('/'))
    if os.path.isfile(f):
        route.fulfill(path=f)
    else:
        route.fulfill(status=404, body='')


def open_page(b, url, width, height, dpr, mobile):
    ctx = b.new_context(viewport={'width': width, 'height': height}, device_scale_factor=dpr, is_mobile=mobile,
                        has_touch=mobile, timezone_id=TZ, color_scheme='light', reduced_motion='reduce')
    page = ctx.new_page()
    page.clock.set_fixed_time(NOW)
    page.add_init_script(SEEDED_RANDOM)
    page.route(LIVE + '**', local)
    page.goto(url)
    page.evaluate('document.fonts.ready')
    page.add_style_tag(content=HIDE)
    return ctx, page


def widget(b, base, **kw):
    ctx, page = open_page(b, base + '/', 440, 3600, 3, True, **kw)
    page.wait_for_selector('.entry__link')
    page.evaluate('document.fonts.ready')
    page.wait_for_timeout(400)
    return ctx, page


def rect(page, sel, i=0):
    return page.evaluate("""([sel, i]) => { const r = document.querySelectorAll(sel)[i].getBoundingClientRect();
      return { x: r.left, y: r.top, w: r.width, h: r.height }; }""", [sel, i])


def shot(page, name, clip):
    """a clipped screenshot inside the (tall) viewport, never a full-page one: resizing the page shifts its layout"""
    clip = {k: round(v, 2) for k, v in clip.items()}
    vw, vh, sy = page.evaluate('[innerWidth, innerHeight, scrollY]')
    assert sy == 0 and clip['y'] >= 0 and clip['y'] + clip['h'] <= vh and clip['x'] + clip['w'] <= vw, (name, clip, vw, vh, sy)
    page.screenshot(path=os.path.join(SHOTS, name), clip={'x': clip['x'], 'y': clip['y'], 'width': clip['w'], 'height': clip['h']})
    return clip


def rel(r, crop):
    return {'x': round(r['x'] - crop['x'], 1), 'y': round(r['y'] - crop['y'], 1), 'w': round(r['w'], 1), 'h': round(r['h'], 1)}


def caret(page, crop):
    """where the text caret would sit after the typed value, measured with the field's own font"""
    return page.evaluate("""(crop) => { const i = document.getElementById('obit-search'), cs = getComputedStyle(i), r = i.getBoundingClientRect();
      const c = document.createElement('canvas').getContext('2d'); c.font = cs.font;
      const x = r.left + parseFloat(cs.borderLeftWidth) + parseFloat(cs.paddingLeft) + c.measureText(i.value).width;
      const h = parseFloat(cs.fontSize) * 1.25;
      return { x: Math.round((x - crop.x) * 10) / 10, y: Math.round((r.top + r.height / 2 - h / 2 - crop.y) * 10) / 10, h: Math.round(h * 10) / 10 }; }""", crop)


if __name__ == '__main__':
    assert os.path.isfile(os.path.join(DIST, 'o', PERSON + '.html')), 'build the widget and render the pages first'
    os.makedirs(SHOTS, exist_ok=True)
    for f in ('wpr-seal.png', 'wpr-logo.png', 'helke.png', 'brainard.png'):
        shutil.copy(os.path.join(ROOT, 'web', 'public', 'assets', f), os.path.join(SHOTS, f))
    L = {'phone': 440}
    httpd, base = serve()
    with sync_playwright() as p:
        b = p.chromium.launch()

        # Cover + O1: the search block, and the register from its first date heading down
        ctx, page = widget(b, base)
        s = rect(page, '.search')
        crop = shot(page, 'search-cover.png', {'x': s['x'] - 10, 'y': s['y'] - 10, 'w': s['w'] + 20, 'h': s['h'] + 20})
        L['searchCover'] = {'w': crop['w'], 'h': crop['h'], 'caret': caret(page, crop)}
        L['featured'] = page.evaluate("document.querySelector('.featured__name')?.textContent || null")
        head = rect(page, '.register__date')
        rows = page.evaluate("[...document.querySelectorAll('.register__group')].slice(0, 3).map(g => { const r = g.getBoundingClientRect(); return [r.top, r.bottom]; })")
        top = head['y'] - 14
        crop = shot(page, 'register.png', {'x': 0, 'y': top, 'w': 440, 'h': min(rows[-1][1] + 10 - top, 3600 - top)})
        L['register'] = {'w': crop['w'], 'h': crop['h'], 'groups': [round(r[0] - top, 1) for r in rows]}
        L['names'] = page.evaluate("[...document.querySelectorAll('.entry__name')].slice(0, 12).map(n => n.textContent)")
        # the same default view whole, from the masthead down, for the phone on page 1
        crop = shot(page, 'phone-register.png', {'x': 0, 'y': 0, 'w': 440, 'h': round(rows[1][1] + 10, 1)})
        L['phoneRegister'] = {'w': crop['w'], 'h': crop['h'], 'register': round(head['y'], 1),
                              'services': round(rect(page, '.services')['y'], 1)}
        ctx.close()

        # O2: Browse opened, then the letter K
        ctx, page = widget(b, base)
        page.click('.browse__toggle')
        page.wait_for_timeout(300)
        br = rect(page, '.browse')
        crop = {'x': 0, 'y': br['y'] - 14, 'w': 440, 'h': 1040}
        crop = shot(page, 'browse-open.png', crop)
        letters = page.evaluate("[...document.querySelectorAll('.browse__letter')].map(l => l.textContent)")
        k = letters.index('K')
        L['browse'] = {'w': crop['w'], 'h': crop['h'], 'k': rel(rect(page, '.browse__letter', k), crop)}
        page.click('.browse__letter >> nth=%d' % k)
        page.wait_for_timeout(400)
        shot(page, 'browse-k.png', crop)
        ctx.close()

        # O3: the search, typed one letter at a time (the empty field first), every state cropped to one window
        ctx, page = widget(b, base)
        s = rect(page, '.search')
        page.fill('#obit-search', QUERY)
        page.wait_for_timeout(400)
        last = rect(page, '.register__group--mentions')
        crop = {'x': 0, 'y': s['y'] - 14, 'w': 440, 'h': round(last['y'] + last['h'] + 10 - (s['y'] - 14), 1)}
        typed = []
        page.fill('#obit-search', '')
        page.evaluate('document.activeElement.blur()')
        page.wait_for_timeout(300)
        shot(page, 'search-rest.png', crop)
        L['field'] = rel(rect(page, '#obit-search'), crop)
        for n in range(len(TYPED) + 1):
            page.fill('#obit-search', TYPED[:n])
            page.wait_for_timeout(300)
            shot(page, 'search-%d.png' % n, crop)
            typed.append({'count': page.evaluate("document.querySelector('.search__count').textContent"), 'caret': caret(page, crop)})
        L['search'] = {'w': crop['w'], 'h': crop['h'], 'states': typed, 'field': L.pop('field')}

        # O4: the mentions tier of the name spelled right, and every matched word in it
        page.fill('#obit-search', QUERY)
        page.wait_for_timeout(400)
        m = rect(page, '.register__group--mentions')
        crop = shot(page, 'mentions.png', {'x': 0, 'y': m['y'] - 10, 'w': 440, 'h': m['h'] + 20})
        marks = page.evaluate("document.querySelectorAll('.register__group--mentions .entry__mark').length")
        L['mentions'] = {'w': crop['w'], 'h': crop['h'], 'top': round(m['y'] - 10 - (s['y'] - 14), 1),
                         'marks': [rel(rect(page, '.register__group--mentions .entry__mark', i), crop) for i in range(marks)]}
        ctx.close()

        # O5 + O6: her page, its share row, and the printed keepsake
        ctx, page = open_page(b, base + '/o/%s.html' % PERSON, 600, 4200, 2.5, False)
        page.wait_for_timeout(300)
        sh = rect(page, '.share')
        crop = shot(page, 'person.png', {'x': 0, 'y': 0, 'w': 600, 'h': sh['y'] + sh['h'] + 34})
        L['person'] = {'w': crop['w'], 'h': crop['h'], 'portrait': rel(rect(page, '.portrait'), crop),
                       'text': rel(rect(page, '.body'), crop)}
        bottom = sh['y'] + sh['h'] + 30
        crop = shot(page, 'person-foot.png', {'x': 0, 'y': bottom - 540, 'w': 600, 'h': 540})
        btns = page.evaluate("[...document.querySelectorAll('.share__btn')].map(b => b.textContent.trim())")
        L['share'] = {'w': crop['w'], 'h': crop['h'], 'buttons': {t: rel(rect(page, '.share__btn', i), crop) for i, t in enumerate(btns)}}
        page.evaluate("document.querySelector('[data-copy]').textContent = 'Link copied'")   # what a tap shows
        shot(page, 'person-foot-copied.png', crop)
        ctx.close()

        ctx, page = open_page(b, base + '/o/%s.html' % PERSON, 816, 2400, 2, False)
        page.emulate_media(media='print')
        page.add_style_tag(content='body{margin:0;padding:64px 72px !important}')
        page.wait_for_timeout(300)
        shot(page, 'print.png', {'x': 0, 'y': 0, 'w': 816, 'h': 1056})
        L['print'] = {'w': 816, 'h': 1056}
        ctx.close()
        b.close()
    httpd.shutdown()
    json.dump(L, open(os.path.join(SHOTS, 'layout.json'), 'w', encoding='utf-8'), indent=1)
    print(json.dumps(L, indent=1)[:2500])

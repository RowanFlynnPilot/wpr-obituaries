"""Render a single crawlable, rankable obituary page per person.

This is the SEO layer. Each page is a real URL Google can index, with a
person's name in the title and H1, schema.org Obituary structured data, and
the full text. The React widget is only the browse surface; these pages are
what win the "<name> obituary Wausau" searches.

Visual system mirrors the WPR newsroom: Oswald (the condensed nameplate face),
Merriweather (the reading serif) and Courier Prime as the typewriter accent for
datelines and labels — so a shared page reads as Wausau Pilot & Review.
"""

from __future__ import annotations

import html
import json
from urllib.parse import quote

from models import Obituary

WPR_LOGO = (
    "https://wausaupilotandreview.com/wp-content/uploads/2024/04/"
    "WausauPilotandReviewLogo.png"
)
FONTS = (
    "https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;"
    "0,400;0,700;1,300;1,400&family=Oswald:wght@400;500;600;700&"
    "family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap"
)


def render_sitemap(obituaries: list[Obituary], base_url: str) -> str:
    """Build a sitemap.xml of the register plus every per-person page.

    Speeds indexing and tells search engines these URLs are canonical. Driven by
    the full master, so every published page is always listed.
    """
    urls = [f"  <url><loc>{html.escape(base_url)}/</loc></url>"]
    for ob in obituaries:
        loc = html.escape(f"{base_url}/o/{ob.slug}.html")
        urls.append(
            f"  <url><loc>{loc}</loc><lastmod>{ob.source_date}</lastmod></url>"
        )
    body = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


def _structured_data(
    ob: Obituary, page_url: str, sponsor: dict, base_url: str, photo_url: str | None = None
) -> str:
    image = photo_url or ob.photo_url
    data = {
        "@context": "https://schema.org",
        "@type": "Obituary",
        "headline": f"{ob.name} obituary",
        "url": page_url,
        "datePublished": ob.source_date,
        "publisher": {"@type": "NewsMediaOrganization", "name": "Wausau Pilot & Review"},
        "about": {
            "@type": "Person",
            "name": ob.name,
            **({"birthDate": ob.birth_date} if ob.birth_date else {}),
            **({"deathDate": ob.death_date} if ob.death_date else {}),
            **({"image": image} if image else {}),
        },
    }
    orgs = []
    for s in sponsor.get("sponsors") or []:
        if not s.get("name"):
            continue
        org = {"@type": "Organization", "name": s["name"]}
        if s.get("url"):
            org["url"] = s["url"]
        if s.get("logo"):
            org["logo"] = f"{base_url}/{s['logo']}"
        orgs.append(org)
    if orgs:
        data["sponsor"] = orgs if len(orgs) > 1 else orgs[0]
    return json.dumps(data, indent=2)


def _lifespan(ob: Obituary) -> str:
    birth = ob.birth_date[:4] if ob.birth_date else ""
    death = ob.death_date[:4] if ob.death_date else (str(ob.death_year) if ob.death_year else "")
    if birth and death:
        return f"{birth} – {death}"
    if death:
        return death
    return ""


def _sponsor_lockup(s: dict, base_url: str) -> str:
    """A single sponsor's logo (or name), linked to its site when present."""
    name = html.escape(s["name"])
    if s.get("logo"):
        inner = f'<img src="{base_url}/{html.escape(s["logo"])}" alt="{name}" />'
    else:
        inner = f'<span class="sponsor-card__name">{name}</span>'
    if s.get("url"):
        return (
            f'<a class="sponsor-card__logo" href="{html.escape(s["url"])}" '
            f'target="_blank" rel="noopener">{inner}</a>'
        )
    return f'<span class="sponsor-card__logo">{inner}</span>'


def _sponsor_section(sponsor: dict, base_url: str) -> str:
    """Showcase the anchor sponsors: one logo lockup per sponsor."""
    lockups = [
        _sponsor_lockup(s, base_url)
        for s in (sponsor.get("sponsors") or [])
        if s.get("name")
    ]
    if not lockups:
        return ""
    label = html.escape(sponsor.get("label") or "Obituaries made possible by")
    logos = "\n        ".join(lockups)
    return f"""<section class="sponsor-card">
      <p class="sponsor-card__label">{label}</p>
      <div class="sponsor-card__logos">
        {logos}
      </div>
    </section>"""


def _share_section(name: str, page_url: str) -> str:
    """Facebook / email / print — families share obituaries widely."""
    fb = f"https://www.facebook.com/sharer/sharer.php?u={quote(page_url, safe='')}"
    subject = quote(f"{name} Obituary")
    body = quote(f"{name} — obituary on Wausau Pilot & Review:\n{page_url}")
    return f"""<div class="share">
      <span class="share__label">Share</span>
      <a class="share__btn" href="{fb}" target="_blank" rel="noopener">Facebook</a>
      <a class="share__btn" href="mailto:?subject={subject}&amp;body={body}">Email</a>
      <button class="share__btn" type="button" onclick="window.print();return false;">Print</button>
    </div>"""


def _related_section(related: list[Obituary], base_url: str) -> str:
    """Internal links to recent obituaries — recirculation and crawl depth."""
    if not related:
        return ""
    items = []
    for r in related:
        span = _lifespan(r)
        meta = f' <span class="more__span">{span}</span>' if span else ""
        items.append(
            f'<li><a href="{base_url}/o/{r.slug}.html">{html.escape(r.name)}</a>{meta}</li>'
        )
    links = "\n        ".join(items)
    return f"""<section class="more">
      <p class="more__label">More recent obituaries</p>
      <ul class="more__list">
        {links}
      </ul>
    </section>"""


def render_person_page(
    ob: Obituary,
    sponsor: dict,
    base_url: str,
    related: list[Obituary] | None = None,
    photo_url: str | None = None,
) -> str:
    page_url = f"{base_url}/o/{ob.slug}.html"
    pic = photo_url or ob.photo_url  # vendored local copy when available, else remote
    body_paragraphs = "\n".join(
        f"      <p>{html.escape(p)}</p>" for p in ob.body.split("\n\n") if p.strip()
    )
    lifespan = _lifespan(ob)
    photo = (
        f'<img class="portrait" src="{html.escape(pic)}" '
        f'alt="{html.escape(ob.name)}" />'
        if pic
        else ""
    )
    funeral_line = (
        f'<p class="arrangements">Arrangements by {html.escape(ob.funeral_home)}.</p>'
        if ob.funeral_home
        else ""
    )
    sponsor_section = _sponsor_section(sponsor, base_url)
    share_section = _share_section(ob.name, page_url)
    related_section = _related_section(related or [], base_url)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(ob.name)} Obituary — Wausau Pilot &amp; Review</title>
  <meta name="description" content="{html.escape(ob.summary)}" />
  <meta name="theme-color" content="#f6f2ea" />
  <link rel="canonical" href="{page_url}" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Wausau Pilot &amp; Review" />
  <meta property="og:title" content="{html.escape(ob.name)} Obituary" />
  <meta property="og:description" content="{html.escape(ob.summary)}" />
  <meta property="og:url" content="{page_url}" />
  {f'<meta property="og:image" content="{html.escape(pic)}" />' if pic else ''}
  <script type="application/ld+json">
{_structured_data(ob, page_url, sponsor, base_url, pic)}
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="{FONTS}" rel="stylesheet" />
  <style>
    :root {{
      --ink: #1b1a18; --paper: #f6f2ea; --paper-2: #fffdf7;
      --muted: #6f6a61; --faint: #9b958a; --rule: #d9d3c6;
      --hairline: #e7e1d5; --accent: #7c2e36;
      --serif: "Merriweather", Georgia, serif;
      --nameplate: "Oswald", "Arial Narrow", sans-serif;
      --mono: "Courier Prime", "Courier New", monospace;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; background: var(--paper); color: var(--ink);
      font-family: var(--serif); font-weight: 400; line-height: 1.75;
      -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
    }}
    .wrap {{ max-width: 680px; margin: 0 auto; padding: 44px 24px 80px; }}
    .masthead {{ text-align: center; margin-bottom: 30px; }}
    .masthead__logo img {{ height: 30px; width: auto; mix-blend-mode: multiply; }}
    .kicker {{
      margin: 16px 0 0; font-family: var(--mono); font-size: 11.5px;
      letter-spacing: 0.26em; text-transform: uppercase; color: var(--accent);
    }}
    .masthead__rule {{
      height: 0; border: 0; border-top: 3px double var(--rule);
      margin: 22px auto 0;
    }}
    h1 {{
      font-family: var(--serif); font-weight: 700;
      font-size: clamp(2.1rem, 6vw, 3rem); line-height: 1.08;
      letter-spacing: -0.01em; margin: 0;
    }}
    .lifespan {{
      font-family: var(--mono); font-size: 1.05rem; letter-spacing: 0.04em;
      color: var(--muted); margin: 10px 0 0;
    }}
    .rule {{ height: 3px; background: var(--accent); width: 54px; margin: 26px 0; }}
    .portrait {{
      float: right; width: 184px; max-width: 42%; margin: 4px 0 18px 26px;
      border: 1px solid var(--rule); filter: grayscale(0.15);
    }}
    .body {{ font-weight: 300; font-size: 1.06rem; }}
    .body p {{ margin: 0 0 1.2em; }}
    .arrangements {{
      clear: both; color: var(--muted); font-style: italic; font-weight: 300;
    }}
    .sponsor-card {{
      clear: both; text-align: center; background: var(--paper-2);
      border: 1px solid var(--rule); border-top: 3px solid var(--accent);
      border-radius: 2px; padding: 30px 28px 32px; margin: 44px 0 0;
    }}
    .sponsor-card__label {{
      margin: 0 0 18px; font-family: var(--mono); font-size: 11px;
      letter-spacing: 0.24em; text-transform: uppercase; color: var(--muted);
    }}
    .sponsor-card__logos {{
      display: flex; flex-wrap: wrap; align-items: center;
      justify-content: center; gap: 22px 40px;
    }}
    .sponsor-card__logo img {{ height: 80px; width: auto; max-width: 100%; }}
    .sponsor-card__name {{
      font-family: var(--nameplate); font-size: 1.3rem; font-weight: 600;
      margin: 0;
    }}
    .sponsor-card__name a {{ color: var(--ink); text-decoration: none; }}
    .share {{
      clear: both; display: flex; flex-wrap: wrap; align-items: center;
      gap: 10px; margin: 30px 0 0;
    }}
    .share__label {{
      font-family: var(--mono); font-size: 11px; letter-spacing: 0.18em;
      text-transform: uppercase; color: var(--muted);
    }}
    .share__btn {{
      font-family: var(--mono); font-size: 12px; letter-spacing: 0.03em;
      color: var(--accent); background: var(--paper-2); border: 1px solid var(--rule);
      border-radius: 2px; padding: 6px 12px; text-decoration: none; cursor: pointer;
    }}
    .share__btn:hover {{ background: var(--hover); }}
    .more {{ margin: 40px 0 0; padding-top: 22px; border-top: 1px solid var(--rule); }}
    .more__label {{
      margin: 0 0 12px; font-family: var(--mono); font-size: 11px;
      letter-spacing: 0.2em; text-transform: uppercase; color: var(--muted);
    }}
    .more__list {{ list-style: none; margin: 0; padding: 0; }}
    .more__list li {{ margin: 0 0 8px; }}
    .more__list a {{
      font-family: var(--serif); font-weight: 700; color: var(--ink);
      text-decoration: none;
    }}
    .more__list a:hover {{ color: var(--accent); text-decoration: underline; }}
    .more__span {{
      font-family: var(--mono); font-size: 12px; color: var(--muted); margin-left: 6px;
    }}
    .back {{
      display: inline-block; margin-top: 36px; font-family: var(--mono);
      font-size: 12.5px; letter-spacing: 0.04em; color: var(--accent);
      text-decoration: none;
    }}
    .back:hover {{ text-decoration: underline; }}
    @media (max-width: 480px) {{
      .wrap {{ padding: 32px 18px 64px; }}
      .portrait {{ float: none; width: 100%; max-width: 100%; margin: 0 0 18px; }}
      .sponsor-card__logo img {{ height: 72px; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <header class="masthead">
      <a class="masthead__logo" href="https://wausaupilotandreview.com"
         target="_blank" rel="noopener">
        <img src="{WPR_LOGO}" alt="Wausau Pilot &amp; Review" />
      </a>
      <p class="kicker">In Memoriam</p>
      <hr class="masthead__rule" />
    </header>
    <h1>{html.escape(ob.name)}</h1>
    {f'<p class="lifespan">{lifespan}</p>' if lifespan else ''}
    <div class="rule"></div>
    <article class="body">
      {photo}
{body_paragraphs}
    </article>
    {funeral_line}
    {share_section}
    {sponsor_section}
    {related_section}
    <a class="back" href="{base_url}/">&larr; All obituaries</a>
  </main>
</body>
</html>
"""

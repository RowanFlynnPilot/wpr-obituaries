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


def _structured_data(ob: Obituary, page_url: str, sponsor: dict, base_url: str) -> str:
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
            **({"image": ob.photo_url} if ob.photo_url else {}),
        },
    }
    if sponsor.get("name"):
        org = {"@type": "Organization", "name": sponsor["name"]}
        if sponsor.get("url"):
            org["url"] = sponsor["url"]
        if sponsor.get("logo"):
            org["logo"] = f"{base_url}/{sponsor['logo']}"
        data["sponsor"] = org
    return json.dumps(data, indent=2)


def _lifespan(ob: Obituary) -> str:
    birth = ob.birth_date[:4] if ob.birth_date else ""
    death = ob.death_date[:4] if ob.death_date else (str(ob.death_year) if ob.death_year else "")
    if birth and death:
        return f"{birth} – {death}"
    if death:
        return death
    return ""


def _sponsor_section(sponsor: dict, base_url: str) -> str:
    """Showcase the anchor sponsor: logo lockup, link and tagline when present."""
    if not sponsor.get("name"):
        return ""
    name = html.escape(sponsor["name"])
    url = html.escape(sponsor["url"]) if sponsor.get("url") else ""
    tagline = (
        f'<p class="sponsor-card__tagline">{html.escape(sponsor["tagline"])}</p>'
        if sponsor.get("tagline")
        else ""
    )
    if sponsor.get("logo"):
        img = (
            f'<img src="{base_url}/{html.escape(sponsor["logo"])}" alt="{name}" />'
        )
        lockup = (
            f'<a class="sponsor-card__logo" href="{url}" target="_blank" '
            f'rel="noopener">{img}</a>'
            if url
            else f'<span class="sponsor-card__logo">{img}</span>'
        )
    else:
        linked = f'<a href="{url}">{name}</a>' if url else name
        lockup = f'<p class="sponsor-card__name">{linked}</p>'
    return f"""<section class="sponsor-card">
      <p class="sponsor-card__label">Obituaries made possible by</p>
      {lockup}
      {tagline}
    </section>"""


def render_person_page(ob: Obituary, sponsor: dict, base_url: str) -> str:
    page_url = f"{base_url}/o/{ob.slug}.html"
    body_paragraphs = "\n".join(
        f"      <p>{html.escape(p)}</p>" for p in ob.body.split("\n\n") if p.strip()
    )
    lifespan = _lifespan(ob)
    photo = (
        f'<img class="portrait" src="{html.escape(ob.photo_url)}" '
        f'alt="{html.escape(ob.name)}" />'
        if ob.photo_url
        else ""
    )
    funeral_line = (
        f'<p class="arrangements">Arrangements by {html.escape(ob.funeral_home)}.</p>'
        if ob.funeral_home
        else ""
    )
    sponsor_section = _sponsor_section(sponsor, base_url)

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
  {f'<meta property="og:image" content="{html.escape(ob.photo_url)}" />' if ob.photo_url else ''}
  <script type="application/ld+json">
{_structured_data(ob, page_url, sponsor, base_url)}
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
    .sponsor-card__logo img {{ height: 88px; width: auto; max-width: 100%; }}
    .sponsor-card__name {{
      font-family: var(--nameplate); font-size: 1.3rem; font-weight: 600;
      margin: 0;
    }}
    .sponsor-card__name a {{ color: var(--ink); text-decoration: none; }}
    .sponsor-card__tagline {{
      max-width: 38ch; margin: 18px auto 0; font-style: italic;
      font-weight: 300; font-size: 0.96rem; color: var(--muted);
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
    {sponsor_section}
    <a class="back" href="{base_url}/">&larr; All obituaries</a>
  </main>
</body>
</html>
"""

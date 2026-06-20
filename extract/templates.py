"""Render a single crawlable, rankable obituary page per person.

This is the SEO layer. Each page is a real URL Google can index, with a
person's name in the title and H1, schema.org Obituary structured data, and
the full text. The React widget is only the browse surface; these pages are
what win the "<name> obituary Wausau" searches.
"""

from __future__ import annotations

import html
import json

from models import Obituary


def _structured_data(ob: Obituary, page_url: str, sponsor: dict) -> str:
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
        data["sponsor"] = {"@type": "Organization", "name": sponsor["name"]}
    return json.dumps(data, indent=2)


def _lifespan(ob: Obituary) -> str:
    birth = ob.birth_date[:4] if ob.birth_date else ""
    death = ob.death_date[:4] if ob.death_date else (str(ob.death_year) if ob.death_year else "")
    if birth and death:
        return f"{birth} – {death}"
    if death:
        return death
    return ""


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
    sponsor_line = (
        f'<p class="sponsor">Obituaries on Wausau Pilot &amp; Review are made '
        f'possible by {html.escape(sponsor["name"])}.</p>'
        if sponsor.get("name")
        else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(ob.name)} Obituary — Wausau Pilot &amp; Review</title>
  <meta name="description" content="{html.escape(ob.summary)}" />
  <link rel="canonical" href="{page_url}" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{html.escape(ob.name)} Obituary" />
  <meta property="og:description" content="{html.escape(ob.summary)}" />
  <meta property="og:url" content="{page_url}" />
  {f'<meta property="og:image" content="{html.escape(ob.photo_url)}" />' if ob.photo_url else ''}
  <script type="application/ld+json">
{_structured_data(ob, page_url, sponsor)}
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --ink: #1c1b19; --paper: #f7f4ee; --muted: #6b665e;
      --teal: #3a867c; --rule: #d8d2c6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; background: var(--paper); color: var(--ink);
      font-family: "Source Sans 3", system-ui, sans-serif;
      line-height: 1.65; -webkit-font-smoothing: antialiased;
    }}
    .wrap {{ max-width: 680px; margin: 0 auto; padding: 48px 24px 80px; }}
    .eyebrow {{
      font-family: "JetBrains Mono", monospace; font-size: 12px;
      letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted);
    }}
    h1 {{
      font-family: "Fraunces", serif; font-weight: 600;
      font-size: clamp(2rem, 6vw, 3rem); line-height: 1.05;
      margin: 8px 0 4px;
    }}
    .lifespan {{
      font-family: "JetBrains Mono", monospace; font-size: 1.1rem;
      color: var(--muted); margin-bottom: 24px;
    }}
    .rule {{ height: 2px; background: var(--teal); width: 56px; margin: 24px 0; }}
    .portrait {{
      float: right; width: 180px; max-width: 40%; margin: 0 0 16px 24px;
      border: 1px solid var(--rule);
    }}
    .body p {{ margin: 0 0 1.1em; }}
    .arrangements {{ color: var(--muted); font-style: italic; }}
    .sponsor {{
      margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--rule);
      font-family: "JetBrains Mono", monospace; font-size: 13px;
      color: var(--muted);
    }}
    .back {{
      display: inline-block; margin-top: 32px;
      font-family: "JetBrains Mono", monospace; font-size: 13px;
      color: var(--teal); text-decoration: none;
    }}
    .back:hover {{ text-decoration: underline; }}
    @media (max-width: 480px) {{ .portrait {{ float: none; width: 100%; max-width: 100%; margin: 0 0 16px; }} }}
  </style>
</head>
<body>
  <main class="wrap">
    <p class="eyebrow">In Memoriam · Wausau Pilot &amp; Review</p>
    <h1>{html.escape(ob.name)}</h1>
    {f'<p class="lifespan">{lifespan}</p>' if lifespan else ''}
    <div class="rule"></div>
    <div class="body">
      {photo}
{body_paragraphs}
    </div>
    {funeral_line}
    {sponsor_line}
    <a class="back" href="{base_url}/">← All obituaries</a>
  </main>
</body>
</html>
"""

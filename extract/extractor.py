"""Turn one daily batch post into individual, structured obituaries.

Obituary formatting varies wildly post to post, so a regex parser would be
brittle. Claude Haiku reads each batch and returns one structured record per
person. The model only extracts what is present; it never invents detail.
"""

from __future__ import annotations

import json

from anthropic import Anthropic
from bs4 import BeautifulSoup

from models import Obituary

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 16000

PROMPT = """You are extracting individual obituaries from a single \
newspaper batch post. The post below contains one or more obituaries \
concatenated together. Each [IMAGE: url] marker is a photo that appears \
immediately before the person it belongs to.

Return ONLY a JSON array — no prose, no markdown fences. One object per \
person, in the order they appear:

[{{
  "name": "Full name as written",
  "birth_date": "YYYY-MM-DD or null",
  "death_date": "YYYY-MM-DD or null",
  "death_year": 2026 or null,
  "age": 87 or null,
  "funeral_home": "Name of funeral home handling arrangements, or null",
  "photo_url": "URL of this person's photo from the nearest preceding \
[IMAGE] marker, or null",
  "summary": "One respectful sentence naming the person and, if present, \
their age and town. No flourishes.",
  "body": "This person's full obituary text. Preserve paragraphs as \\n\\n. \
Do not include other people's obituaries, sponsor lines, or funeral home \
logos."
}}]

Rules:
- Extract only what the text states. Use null for anything absent.
- Never fabricate dates, ages, or biographical detail.
- If no obituary for a real person is present, return [].

Batch post text:
---
{text}
---"""


def _to_markered_text(content_html: str) -> str:
    """Flatten post HTML to text, inlining image URLs as [IMAGE: url]."""
    soup = BeautifulSoup(content_html, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src", "")
        img.replace_with(f"\n[IMAGE: {src}]\n")
    text = soup.get_text("\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _parse_response(raw: str) -> list[dict]:
    """Parse the model's JSON array, raising loudly on malformed output."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].removeprefix("json").strip()
    return json.loads(raw)


def extract_obituaries(post: dict, client: Anthropic) -> list[Obituary]:
    """Extract every person from one batch post."""
    source_id = int(post["id"])
    source_url = post["link"]
    source_date = post["date"][:10]
    content_html = post["content"]["rendered"]
    text = _to_markered_text(content_html)

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": PROMPT.format(text=text)}],
    )
    if response.stop_reason == "max_tokens":
        raise ValueError(
            f"Output truncated for {source_url} (hit max_tokens={MAX_TOKENS}); "
            "raise MAX_TOKENS."
        )
    records = _parse_response(response.content[0].text)

    obituaries: list[Obituary] = []
    for r in records:
        name = (r.get("name") or "").strip()
        if not name:
            raise ValueError(f"Record with no name in post {source_url}: {r}")
        obituaries.append(
            Obituary(
                name=name,
                source_id=source_id,
                source_url=source_url,
                source_date=source_date,
                death_year=r.get("death_year"),
                birth_date=r.get("birth_date"),
                death_date=r.get("death_date"),
                age=r.get("age"),
                funeral_home=r.get("funeral_home"),
                photo_url=r.get("photo_url"),
                summary=(r.get("summary") or "").strip(),
                body=(r.get("body") or "").strip(),
            )
        )
    return obituaries
"""Turn one daily batch post into individual, structured obituaries.

Obituary formatting varies wildly post to post, so a regex parser would be
brittle. Claude Haiku reads each batch and returns one structured record per
person. The model only extracts what is present; it never invents detail.
"""

from __future__ import annotations

import re
import sys
from datetime import date

from anthropic import Anthropic
from bs4 import BeautifulSoup

from models import Obituary


def sanity_warnings(ob: Obituary) -> list[str]:
    """Flag implausible extracted data — logged loudly, never fatal."""
    warnings = []
    if ob.birth_date and ob.death_date and ob.birth_date > ob.death_date:
        warnings.append(f"birth {ob.birth_date} after death {ob.death_date}")
    if ob.death_year and not (1900 <= ob.death_year <= date.today().year + 1):
        warnings.append(f"implausible death year {ob.death_year}")
    if ob.age is not None and not (0 <= ob.age <= 120):
        warnings.append(f"implausible age {ob.age}")
    if ob.birth_date and ob.death_date and ob.age is not None:
        years = int(ob.death_date[:4]) - int(ob.birth_date[:4])
        if abs(years - ob.age) > 1:
            warnings.append(f"age {ob.age} inconsistent with dates (~{years})")
    return warnings

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 16000

_NULLABLE_TEXT = {"type": ["string", "null"]}
_NULLABLE_INT = {"type": ["integer", "null"]}

# The records come back as a tool call, so the API hands over parsed data. Asked
# to write the JSON out as text, the model eventually leaves one quotation mark
# unescaped inside a long obituary body, and the whole post fails to parse.
RECORD_TOOL = {
    "name": "record_obituaries",
    "description": "Record every obituary found in the batch post.",
    "input_schema": {
        "type": "object",
        "properties": {
            "obituaries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Full name as written"},
                        "birth_date": {**_NULLABLE_TEXT, "description": "YYYY-MM-DD, or null"},
                        "death_date": {**_NULLABLE_TEXT, "description": "YYYY-MM-DD, or null"},
                        "death_year": _NULLABLE_INT,
                        "age": _NULLABLE_INT,
                        "funeral_home": {
                            **_NULLABLE_TEXT,
                            "description": "Funeral home handling arrangements, or null",
                        },
                        "photo_url": {
                            **_NULLABLE_TEXT,
                            "description": "URL from the nearest preceding [IMAGE] marker, or null",
                        },
                        "summary": {
                            "type": "string",
                            "description": (
                                "One respectful sentence naming the person and, if present, "
                                "their age and town. If the town is not stated, leave it out "
                                "entirely; never write 'unspecified' or 'unknown'. No flourishes."
                            ),
                        },
                        "body": {
                            "type": "string",
                            "description": (
                                "This person's full obituary text, paragraphs separated by a "
                                "blank line. No other people's obituaries, sponsor lines, or "
                                "funeral home logos."
                            ),
                        },
                    },
                    "required": ["name", "summary", "body"],
                },
            }
        },
        "required": ["obituaries"],
    },
}

PROMPT = """You are extracting individual obituaries from a single \
newspaper batch post. The post below contains one or more obituaries \
concatenated together. Each [IMAGE: url] marker is a photo that appears \
immediately before the person it belongs to.

Record every person with the record_obituaries tool, one entry per person, in the order they appear.

Rules:
- Extract only what the text states. Use null for anything absent.
- Never fabricate dates, ages, or biographical detail.
- If no obituary for a real person is present, record an empty list.

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


# The model occasionally narrates an absence ("Jane Doe, 84, of an unspecified
# town, passed away…"). That is a placeholder, not a fact, and it would be
# published verbatim in the register — strip the clause.
_ABSENT_TOWN = re.compile(
    r",?\s*of (?:an? )?(?:unspecified|unknown|unnamed|undisclosed) (?:town|city|"
    r"village|location|residence|hometown)\b",
    re.IGNORECASE,
)


def clean_summary(summary: str) -> str:
    """The model's one-line summary with any 'of an unspecified town' clause removed."""
    return _ABSENT_TOWN.sub("", summary).strip()


def _records(response, source_url: str) -> list[dict]:
    """The people the model recorded, raising loudly if it recorded none properly."""
    calls = [b for b in response.content if b.type == "tool_use"]
    if len(calls) != 1 or not isinstance(calls[0].input.get("obituaries"), list):
        got = [(b.type, repr(getattr(b, "input", getattr(b, "text", "")))[:700]) for b in response.content]
        raise ValueError(
            f"No usable record_obituaries call for {source_url} "
            f"(stop_reason={response.stop_reason}): {got}"
        )
    return calls[0].input["obituaries"]


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
        tools=[RECORD_TOOL],
        tool_choice={"type": "tool", "name": RECORD_TOOL["name"]},
        messages=[{"role": "user", "content": PROMPT.format(text=text)}],
    )
    if response.stop_reason == "max_tokens":
        raise ValueError(
            f"Output truncated for {source_url} (hit max_tokens={MAX_TOKENS}); "
            "raise MAX_TOKENS."
        )
    records = _records(response, source_url)

    obituaries: list[Obituary] = []
    for r in records:
        name = (r.get("name") or "").strip()
        if not name:
            raise ValueError(f"Record with no name in post {source_url}: {r}")
        ob = Obituary(
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
            summary=clean_summary(r.get("summary") or ""),
            body=(r.get("body") or "").strip(),
        )
        for warning in sanity_warnings(ob):
            print(f"  WARN {ob.name} ({source_url}): {warning}", file=sys.stderr)
        obituaries.append(ob)
    return obituaries
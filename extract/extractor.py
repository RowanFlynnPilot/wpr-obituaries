"""Turn one daily batch post into individual, structured obituaries.

Obituary formatting varies wildly post to post, so a regex parser would be
brittle. Claude Haiku reads each batch and returns one structured record per
person. The model only extracts what is present; it never invents detail.
"""

from __future__ import annotations

import json
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

_INLINE = ["a", "strong", "em", "b", "i", "u", "span", "mark", "small", "sup", "sub"]

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 16000

_NULLABLE_TEXT = {"type": ["string", "null"]}
# "September of 2026" used to come back as 2026-09-01 and a bare birth year as
# January 1: a day nobody stated, published as a fact.
# A birth is often given loosely ("born in 1930", "in September, 1954"). The
# year is worth keeping (it is half the lifespan line), so a birth date carries
# exactly the precision the text has; a death without a day keeps death_year.
_AS_STATED = (
    "The date exactly as precise as the text states it: YYYY-MM-DD when day, month and "
    "year are given, YYYY-MM for a month and year, YYYY for a year alone, else null. "
    "Never fill in a day or month the text does not state."
)
_FULL_DATE_ONLY = (
    "YYYY-MM-DD, only when the text states the day, month and year. If any part is "
    "missing (a month and year, a year alone), use null: never fill in a day or month."
)
_NULLABLE_INT = {"type": ["integer", "null"]}

# The model returns facts and a paragraph range per person, never the obituary
# text itself: the body is lifted from the post by _body. Asked to retype a
# long body inside JSON, the model eventually mis-escapes a quotation mark and
# the whole post fails to parse (Nov. 18, 2026, three runs in a row); and a
# retyped body is the model's copy, where a lifted one is the source's words.
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
                        "birth_date": {**_NULLABLE_TEXT, "description": _AS_STATED},
                        "death_date": {**_NULLABLE_TEXT, "description": _FULL_DATE_ONLY},
                        "death_year": _NULLABLE_INT,
                        "age": _NULLABLE_INT,
                        "veteran": {
                            "type": "boolean",
                            "description": (
                                "true only if the text states that this person served in the armed "
                                "forces (a branch, a war, 'veteran', military honors). A relative's "
                                "service does not count. Otherwise false."
                            ),
                        },
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
                        "body_first": {
                            "type": "integer",
                            "description": "Number of the first paragraph of this person's obituary text",
                        },
                        "body_last": {
                            "type": "integer",
                            "description": (
                                "Number of its last paragraph. The range must not take in another "
                                "person's obituary, a sponsor line, or a funeral home logo."
                            ),
                        },
                    },
                    # every field required (null where the text is silent): left optional,
                    # the model skips them, and a named funeral home goes unrecorded
                    "required": [
                        "name", "birth_date", "death_date", "death_year", "age", "veteran", "funeral_home",
                        "photo_url", "summary", "body_first", "body_last",
                    ],
                },
            }
        },
        "required": ["obituaries"],
    },
}

PROMPT = """You are extracting individual obituaries from a single \
newspaper batch post. The post below contains one or more obituaries \
concatenated together, one numbered paragraph per line ("12| ..."). Each \
[IMAGE: url] marker is a photo that appears immediately before the person it \
belongs to.

Record every person with the record_obituaries tool, one entry per person, in the order they appear.

Rules:
- Extract only what the text states. Use null for anything absent.
- Never fabricate dates, ages, or biographical detail. A date with no stated day is null.
- If no obituary for a real person is present, record an empty list.

Batch post text:
---
{text}
---"""


def _to_markered_text(content_html: str) -> str:
    """Flatten post HTML to one line per paragraph, inlining image URLs as [IMAGE: url]."""
    soup = BeautifulSoup(content_html, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src", "")
        img.replace_with(f"\n[IMAGE: {src}]\n")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    # Inline markup must not split a paragraph: a bolded name or a link is part
    # of its sentence, and a paragraph is the unit a body is lifted by.
    for tag in soup.find_all(_INLINE):
        tag.unwrap()
    soup.smooth()
    text = soup.get_text("\n")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _body(lines: list[str], first, last, name: str, source_url: str) -> str:
    """One person's obituary text: paragraphs first..last (1-based) of the post, photos left out."""
    if not (isinstance(first, int) and isinstance(last, int) and 1 <= first <= last <= len(lines)):
        raise ValueError(
            f"Bad paragraph range {first!r}..{last!r} for {name} in {source_url} "
            f"({len(lines)} paragraphs)"
        )
    return "\n\n".join(l for l in lines[first - 1 : last] if not l.startswith("[IMAGE:"))


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
    if len(calls) == 1 and isinstance(calls[0].input.get("obituaries"), str):
        # Haiku sometimes sends the array as one JSON string; with no bodies in
        # it, that string is short facts and parses (and raises here if not).
        return json.loads(calls[0].input["obituaries"])
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
    lines = _to_markered_text(content_html).split("\n")
    text = "\n".join(f"{n}| {line}" for n, line in enumerate(lines, 1))

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
            body=_body(lines, r.get("body_first"), r.get("body_last"), name, source_url),
            veteran=r.get("veteran") is True,
        )
        for warning in sanity_warnings(ob):
            print(f"  WARN {ob.name} ({source_url}): {warning}", file=sys.stderr)
        obituaries.append(ob)
    return obituaries
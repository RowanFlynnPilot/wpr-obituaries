"""Append one hand-entered obituary to data/manual.json (the render-time hatch).

Used by the **Add obituary** staff workflow (.github/workflows/add-obituary.yml),
which is triggered from web/public/submit-obituary.html. The record is a loose
dict of obituary fields read from stdin (or --record); only `name` and
`source_date` are required — everything else is optional and absent data stays
null. A one-line summary is composed when none is supplied so the town facet and
the card teaser read well.

manual.json is merged at *render*, so an added obituary publishes on the next
render/deploy without a scrape or any API call — the right home for the occasional
out-of-area notice an editor is handed directly. Contrast data/intake/, which
flows through sync.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUAL_FILE = ROOT / "data" / "manual.json"


def _iso_or_die(value: str, field: str) -> str:
    """Return value if it's a valid YYYY-MM-DD date, else exit with a clear error."""
    try:
        date.fromisoformat(value)
    except ValueError:
        raise SystemExit(f"error: {field} must be a date as YYYY-MM-DD (got {value!r})")
    return value


def _format_dod(iso: str) -> str | None:
    """"2026-07-01" -> "July 1, 2026" for the summary line."""
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return None
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def _summary(name: str, age: int | None, town: str | None, death_date: str | None) -> str:
    """One respectful line, shaped so the town facet can read "of <Town>"."""
    parts = [name]
    if age is not None:
        parts.append(f", age {age}")
    if town:
        parts.append(f", of {town}")
    dod = _format_dod(death_date) if death_date else None
    if dod:
        parts.append(f" passed away on {dod}")
    return "".join(parts) + "."


def _opt(raw: dict, key: str) -> str | None:
    """A trimmed string field, or None when blank/absent."""
    v = raw.get(key)
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def build_record(raw: dict) -> dict:
    """Validate + normalise a loose submission into a manual.json entry.

    Mirrors the manual.json schema (data/README.md). Raises SystemExit with a
    plain message on any bad input so the workflow log says exactly what to fix.
    """
    name = (raw.get("name") or "").strip()
    if not name:
        raise SystemExit("error: name is required")
    source_date = (raw.get("source_date") or "").strip()
    if not source_date:
        raise SystemExit("error: source_date (YYYY-MM-DD) is required")
    _iso_or_die(source_date, "source_date")

    death_date = _opt(raw, "death_date")
    birth_date = _opt(raw, "birth_date")
    if death_date:
        _iso_or_die(death_date, "death_date")
    if birth_date:
        _iso_or_die(birth_date, "birth_date")

    age_raw = raw.get("age")
    if age_raw is None or (isinstance(age_raw, str) and not age_raw.strip()):
        age: int | None = None
    else:
        try:
            age = int(age_raw)
        except (TypeError, ValueError):
            raise SystemExit(f"error: age must be a whole number (got {age_raw!r})")

    town = _opt(raw, "town")
    death_year = int((death_date or source_date)[:4])
    summary = _opt(raw, "summary") or _summary(name, age, town, death_date)

    return {
        "name": name,
        "source_date": source_date,
        "death_year": death_year,
        "birth_date": birth_date,
        "death_date": death_date,
        "age": age,
        "funeral_home": _opt(raw, "funeral_home"),
        "photo_url": _opt(raw, "photo_url"),
        "summary": summary,
        "body": _opt(raw, "body"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Append an obituary to data/manual.json.")
    ap.add_argument("--record", help="JSON record; if omitted, read it from stdin.")
    args = ap.parse_args()

    payload = args.record if args.record else sys.stdin.read()
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as e:
        raise SystemExit(f"error: record is not valid JSON ({e})")
    if not isinstance(raw, dict):
        raise SystemExit("error: record must be a JSON object")

    record = build_record(raw)

    existing = json.loads(MANUAL_FILE.read_text(encoding="utf-8")) if MANUAL_FILE.exists() else []
    # A manual record's identity is name + source_date (its slug seed), so a
    # repeated submission of the same person on the same date is a no-op, not a
    # duplicate page.
    if any(
        e.get("name") == record["name"] and e.get("source_date") == record["source_date"]
        for e in existing
    ):
        print(f"note: '{record['name']}' on {record['source_date']} already in manual.json — skipping.")
        return

    existing.append(record)
    MANUAL_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Added manual obituary: {record['name']} ({record['source_date']}).")


if __name__ == "__main__":
    main()

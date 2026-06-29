# `data/intake/` — submitted obituaries (the reviewed product path)

One JSON file per submission, `<id>.json`. The **intake** write-source reads
every file here and emits the **approved** ones into the master on the next sync
(`python extract/main.py`), so they're deduped, photo-vendored, and permanent
exactly like scraped obituaries. Pending and rejected submissions never reach the
site.

This is the universal path (it works for any newsroom, not just WPR's batch
posts). For a quick one-off the editor can still use `manual.json` instead — that
one renders directly without going through review.

## How a submission gets here (lightweight backend)

1. A family submits via the widget's **"Submit an obituary"** form, which opens a
   prefilled email to the submissions address (matching the existing
   "email obituaries to…" workflow).
2. An editor reviews it, then saves it as `data/intake/<id>.json` with
   `"status": "approved"` and commits. (Set `"status": "pending"` to stage one
   without publishing.)

Step 5 swaps this manual file step for a Supabase review queue, without changing
the adapter — flip `adapters.intake.backend` in `newsroom.config.json`.

## Schema

```json
{
  "id": 1001,
  "status": "approved",
  "name": "Jane Q. Doe",
  "source_date": "2026-06-28",
  "birth_date": "1940-03-02",
  "death_date": "2026-06-20",
  "death_year": 2026,
  "age": 86,
  "funeral_home": "Helke Funeral Home",
  "photo_url": "https://…/jane.jpg",
  "summary": "Jane Q. Doe, 86, of Wausau, passed away June 20, 2026.",
  "body": "Full obituary text.\n\nParagraphs separated by a blank line."
}
```

| field | required | notes |
| --- | --- | --- |
| `id` | yes | integer, unique within intake; the page slug + dedupe key derive from it |
| `status` | yes | `pending` \| `approved` \| `rejected` — only `approved` publishes |
| `name` | yes | full name as it should appear |
| `source_date` | yes | `YYYY-MM-DD`, used for ordering (usually the submission/publish date) |
| `birth_date`, `death_date` | no | `YYYY-MM-DD` |
| `death_year`, `age` | no | integers |
| `funeral_home` | no | matched to a funeral-home page if known |
| `photo_url` | no | vendored locally on the next sync |
| `summary` | no | one line for cards/meta; defaults to the name |
| `body` | no | full text; defaults to the summary |

Any edit to an approved file re-publishes it on the next sync (the adapter keys
off a content hash, so there's nothing to bump by hand).

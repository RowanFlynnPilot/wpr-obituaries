import { useState } from "react";
import ObituaryRow from "./ObituaryRow.jsx";
import { dateLabel, eventDate, hasDeathDate } from "../lib/format.js";

// Rows shown before "Show earlier obituaries" — bounds the embed's initial
// height and how many portraits load at once (inside the auto-height iframe
// every mounted row counts as "in viewport", so lazy loading can't help).
const PAGE_SIZE = 60;

export default function Register({
  obituaries,
  mentions = [],
  query,
  letter = null,
  onClear,
  onBrowseLetters,
  onSubmit,
}) {
  // App keys this component on the search/filter identity, so a new result set
  // mounts fresh at the first page — no frame of the old page size, no stale
  // height posted to the embedding page.
  const [limit, setLimit] = useState(PAGE_SIZE);

  if (obituaries.length === 0 && mentions.length === 0) {
    return (
      <div className="register__empty">
        <p className="register__empty-text">
          {query
            ? `No one named “${query}” is listed yet.`
            : "No obituaries to show here yet."}
        </p>
        {/* A dead end on a memorial page must offer a way forward — never end
            on the sponsor card. */}
        <div className="register__empty-actions">
          {query && (
            <button type="button" className="register__action" onClick={onClear}>
              Clear the search
            </button>
          )}
          <button type="button" className="register__action" onClick={onBrowseLetters}>
            Browse by last name
          </button>
          <button type="button" className="register__action" onClick={onSubmit}>
            Not listed? Submit an obituary
          </button>
        </div>
        {query && (
          <p className="register__empty-hint">
            Try just the last name — spellings vary, and a notice may not have reached us yet.
          </p>
        )}
      </div>
    );
  }

  const visible = obituaries.slice(0, limit);
  const remaining = obituaries.length - visible.length;

  // Grouped by date of death (98% of records), labelled honestly; the few with
  // only a publication date say so. A letter browse is one alphabetical index.
  let groups;
  if (letter) {
    groups = [{ key: letter, label: `Last names beginning with ${letter}`, items: visible }];
  } else {
    groups = [];
    for (const ob of visible) {
      const key = eventDate(ob);
      const last = groups[groups.length - 1];
      if (last && last.key === key) last.items.push(ob);
      else {
        groups.push({
          key,
          label: `${hasDeathDate(ob) ? "Died" : "Published"} ${dateLabel(key)}`,
          items: [ob],
        });
      }
    }
  }

  return (
    <div className="register">
      {groups.map((g) => (
        <section className="register__group" key={g.key}>
          <h2 className="register__date">{g.label}</h2>
          <ol className="register__list">
            {g.items.map((ob) => (
              <ObituaryRow key={ob.slug} ob={ob} />
            ))}
          </ol>
        </section>
      ))}
      {/* No live region here: the search bar's count line is the one announcer
          for a new result set, so a keystroke never triggers two readouts. */}
      {remaining > 0 && (
        <button
          type="button"
          className="register__more"
          onClick={() => setLimit(limit + PAGE_SIZE)}
        >
          Show earlier obituaries
          <span className="register__more-count">{remaining} more</span>
        </button>
      )}
      {remaining === 0 && mentions.length > 0 && (
        <section className="register__group register__group--mentions">
          <h2 className="register__date">
            Mentioned in {mentions.length === 1 ? "another notice" : `${mentions.length} other notices`}
          </h2>
          <ol className="register__list">
            {mentions.slice(0, PAGE_SIZE).map((ob) => (
              <ObituaryRow key={ob.slug} ob={ob} />
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}

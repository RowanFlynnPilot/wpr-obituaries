import { useState } from "react";
import ObituaryRow from "./ObituaryRow.jsx";
import { dateLabel, eventDate, hasDeathDate } from "../lib/format.js";

// Rows shown before "Show earlier obituaries" — bounds the embed's initial
// height and how many portraits load at once (inside the auto-height iframe
// every mounted row counts as "in viewport", so lazy loading can't help).
const PAGE_SIZE = 60;
// The second tier is evidence, not a result set: a handful, then the rest on
// request.
const MENTION_PAGE = 10;

export default function Register({
  obituaries,
  mentions = [],
  homes = [],
  query,
  letter = null,
  featured = null,
  onClear,
  onBrowseLetters,
  onSubmit,
  onHome,
}) {
  // App keys this component on the search/filter identity, so a new result set
  // mounts fresh at the first page — no frame of the old page size, no stale
  // height posted to the embedding page.
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [allMentions, setAllMentions] = useState(false);

  if (obituaries.length === 0 && mentions.length === 0 && homes.length === 0) {
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

  const shownMentions = allMentions ? mentions : mentions.slice(0, MENTION_PAGE);
  const restMentions = mentions.length - shownMentions.length;

  return (
    <div className="register">
      {groups.map((g, n) => (
        <div key={g.key}>
          <section className="register__group">
            <h2 className="register__date">{g.label}</h2>
            <ol className="register__list">
              {g.items.map((ob) => (
                <ObituaryRow key={ob.slug} ob={ob} />
              ))}
            </ol>
          </section>
          {/* The featured strip follows the newest day's names rather than
              standing between the search and its results. */}
          {n === 0 && featured}
        </div>
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
      {remaining === 0 && homes.length > 0 && (
        <div className="register__elsewhere">
          {homes.map((h) => (
            <button
              key={h.name}
              type="button"
              className="register__elsewhere-link"
              onClick={() => onHome(h.name)}
            >
              {h.count} {h.count === 1 ? "notice" : "notices"} arranged by {h.name} →
            </button>
          ))}
        </div>
      )}
      {remaining === 0 && mentions.length > 0 && (
        <section className="register__group register__group--mentions">
          <h2 className="register__date">
            {/* "Also" only when there were names to be also to. */}
            {obituaries.length > 0 ? "Also named in " : "Named in "}
            {mentions.length === 1
              ? `one ${obituaries.length > 0 ? "other " : ""}notice`
              : `${mentions.length} ${obituaries.length > 0 ? "other " : ""}notices`}
          </h2>
          <ol className="register__list">
            {shownMentions.map((m) => (
              <ObituaryRow key={m.ob.slug} ob={m.ob} match={m.match} />
            ))}
          </ol>
          {restMentions > 0 && (
            <button
              type="button"
              className="register__more"
              onClick={() => setAllMentions(true)}
            >
              Show the rest
              <span className="register__more-count">{restMentions} more</span>
            </button>
          )}
        </section>
      )}
    </div>
  );
}

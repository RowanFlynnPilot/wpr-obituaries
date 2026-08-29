import { useEffect, useState } from "react";
import ObituaryRow from "./ObituaryRow.jsx";
import { dateLabel } from "../lib/format.js";

// Rows shown before "Show earlier obituaries" — bounds the embed's initial
// height and how many portraits load at once (inside the auto-height iframe
// every mounted row counts as "in viewport", so lazy loading can't help).
const PAGE_SIZE = 60;

export default function Register({ obituaries, query }) {
  const [limit, setLimit] = useState(PAGE_SIZE);

  // A new search/filter result starts back at the first page.
  useEffect(() => setLimit(PAGE_SIZE), [obituaries]);

  if (obituaries.length === 0) {
    return (
      <p className="register__empty">
        {query
          ? `No obituaries match “${query}”. Try a last name, or clear the search to browse.`
          : "No obituaries to show here yet."}
      </p>
    );
  }

  const visible = obituaries.slice(0, limit);
  const remaining = obituaries.length - visible.length;

  // obituaries arrive newest-first, so consecutive same-date entries group up.
  const groups = [];
  for (const ob of visible) {
    const last = groups[groups.length - 1];
    if (last && last.date === ob.sourceDate) last.items.push(ob);
    else groups.push({ date: ob.sourceDate, items: [ob] });
  }

  return (
    <div className="register">
      {groups.map((g) => (
        <section className="register__group" key={g.date}>
          <h2 className="register__date">{dateLabel(g.date)}</h2>
          <ol className="register__list">
            {g.items.map((ob) => (
              <ObituaryRow key={ob.slug} ob={ob} />
            ))}
          </ol>
        </section>
      ))}
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
    </div>
  );
}

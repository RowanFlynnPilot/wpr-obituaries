import ObituaryRow from "./ObituaryRow.jsx";
import { dateLabel } from "../lib/format.js";

export default function Register({ obituaries, query }) {
  if (obituaries.length === 0) {
    return (
      <p className="register__empty">
        No obituaries match “{query}”. Try a last name, or browse the full
        list by clearing the search.
      </p>
    );
  }

  // obituaries arrive newest-first, so consecutive same-date entries group up.
  const groups = [];
  for (const ob of obituaries) {
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
    </div>
  );
}

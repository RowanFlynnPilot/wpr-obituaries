import { useMemo } from "react";
import { monthKey, monthLabel, lastNameInitial } from "../lib/format.js";

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export default function BrowseBar({ obituaries, filter, onFilter }) {
  const months = useMemo(() => {
    const counts = new Map();
    for (const o of obituaries) {
      const k = monthKey(o.sourceDate);
      counts.set(k, (counts.get(k) || 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => (a[0] < b[0] ? 1 : -1))
      .map(([key, count]) => ({ key, count }));
  }, [obituaries]);

  const present = useMemo(() => {
    const s = new Set();
    for (const o of obituaries) s.add(lastNameInitial(o.name));
    return s;
  }, [obituaries]);

  const isMonth = (k) => filter.kind === "month" && filter.value === k;
  const isLetter = (l) => filter.kind === "letter" && filter.value === l;

  return (
    <div className="browse">
      <div className="browse__row">
        <span className="browse__label">Month</span>
        <button
          type="button"
          className={`browse__chip${filter.kind === "none" ? " is-active" : ""}`}
          onClick={() => onFilter({ kind: "none" })}
        >
          All
        </button>
        {months.map((m) => (
          <button
            key={m.key}
            type="button"
            className={`browse__chip${isMonth(m.key) ? " is-active" : ""}`}
            onClick={() => onFilter({ kind: "month", value: m.key })}
          >
            {monthLabel(m.key)} <span className="browse__count">{m.count}</span>
          </button>
        ))}
      </div>

      <div className="browse__row browse__row--az">
        <span className="browse__label">A–Z</span>
        {LETTERS.map((l) =>
          present.has(l) ? (
            <button
              key={l}
              type="button"
              className={`browse__letter${isLetter(l) ? " is-active" : ""}`}
              onClick={() => onFilter({ kind: "letter", value: l })}
            >
              {l}
            </button>
          ) : (
            <span key={l} className="browse__letter is-disabled" aria-hidden="true">
              {l}
            </span>
          )
        )}
      </div>
    </div>
  );
}

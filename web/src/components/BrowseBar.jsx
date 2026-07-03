import { useMemo } from "react";
import { monthKey, monthLabel, lastNameInitial } from "../lib/format.js";

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export default function BrowseBar({ obituaries, filter, onFilter, recentMonths = 3 }) {
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

  // Town is derived best-effort from the summary, so the long count-1 tail holds
  // the occasional non-town ("of Jesus", a hospice). Requiring 2+ keeps the facet
  // to real places people actually browse; rare towns stay reachable via search.
  const towns = useMemo(
    () => countBy(obituaries, (o) => o.town).filter((t) => t.count >= 2),
    [obituaries]
  );
  const homes = useMemo(() => countBy(obituaries, (o) => o.homeName), [obituaries]);

  const isMonth = (k) => filter.kind === "month" && filter.value === k;
  const isLetter = (l) => filter.kind === "letter" && filter.value === l;
  const onSelect = (kind) => (e) =>
    onFilter(e.target.value ? { kind, value: e.target.value } : { kind: "none" });

  return (
    <div className="browse">
      <div className="browse__row">
        <span className="browse__label">Month</span>
        <button
          type="button"
          className={`browse__chip${filter.kind === "recent" ? " is-active" : ""}`}
          onClick={() => onFilter({ kind: "recent", value: recentMonths })}
          title={`The last ${recentMonths} months`}
        >
          Recent
        </button>
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

      <div className="browse__row browse__row--selects">
        {towns.length > 0 && (
          <label className="browse__select">
            <span className="browse__label">Town</span>
            <select
              value={filter.kind === "town" ? filter.value : ""}
              onChange={onSelect("town")}
            >
              <option value="">All towns</option>
              {towns.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.value} ({t.count})
                </option>
              ))}
            </select>
          </label>
        )}
        {homes.length > 0 && (
          <label className="browse__select">
            <span className="browse__label browse__label--inline">Funeral home</span>
            <select
              value={filter.kind === "home" ? filter.value : ""}
              onChange={onSelect("home")}
            >
              <option value="">All funeral homes</option>
              {homes.map((h) => (
                <option key={h.value} value={h.value}>
                  {h.value} ({h.count})
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
    </div>
  );
}

// Distinct non-empty values of `key`, alphabetical, with counts — for the facets.
function countBy(obituaries, key) {
  const counts = new Map();
  for (const o of obituaries) {
    const v = key(o);
    if (v) counts.set(v, (counts.get(v) || 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([value, count]) => ({ value, count }));
}

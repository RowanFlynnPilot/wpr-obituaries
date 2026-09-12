import { forwardRef, useEffect, useMemo, useState } from "react";
import { eventDate, monthKey, monthLabel, lastNameInitial } from "../lib/format.js";

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
// The chip row is half a year; everything older lives in the "Earlier…"
// select. A month with only a stray record or two (a late notice, a
// correction) reads as a broken catalogue if it gets a chip of its own, so it
// goes to the select as well — nothing is unreachable, just not headlined.
const MONTH_CHIPS = 6;
const MIN_CHIP_COUNT = 3;

// Browse is a secondary path (the reader's first move is to type a name), so
// it stays behind one disclosure until asked for — or until a filter is active,
// when the panel must be visible to show what is selected. Inside, month and
// last name are the first tier; town and funeral home sit behind a second
// "More ways to browse" line, so the open panel is two rows, not a control deck.
const BrowseBar = forwardRef(function BrowseBar(
  { obituaries, filter, onFilter, open, onOpenChange, recentMonths = 3 },
  ref
) {
  const filtered = filter.kind !== "recent" && filter.kind !== "none";
  const facetActive = filter.kind === "town" || filter.kind === "home";
  const [moreOpen, setMoreOpen] = useState(facetActive);
  useEffect(() => {
    if (filtered) onOpenChange(true);
  }, [filtered, onOpenChange]);
  useEffect(() => {
    if (facetActive) setMoreOpen(true);
  }, [facetActive]);

  const months = useMemo(() => {
    const counts = new Map();
    for (const o of obituaries) {
      const k = monthKey(eventDate(o));
      counts.set(k, (counts.get(k) || 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => (a[0] < b[0] ? 1 : -1))
      .map(([key, count]) => ({ key, count }));
  }, [obituaries]);

  // Only the letters that begin a surname: an A–Z row with invisible gaps
  // reads as broken, a shorter row reads as the index it is.
  const letters = useMemo(() => {
    const s = new Set();
    for (const o of obituaries) s.add(lastNameInitial(o.name));
    return LETTERS.filter((l) => s.has(l));
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
  // Clearing a select lands on the Recent default, matching what clearing the
  // search does — never a surprise dump into the entire catalogue.
  const onSelect = (kind) => (e) =>
    onFilter(
      e.target.value
        ? { kind, value: e.target.value }
        : { kind: "recent", value: recentMonths }
    );

  const chipMonths = months.slice(0, MONTH_CHIPS).filter((m) => m.count >= MIN_CHIP_COUNT);
  const olderMonths = months.filter((m) => !chipMonths.includes(m));
  const olderActive =
    filter.kind === "month" && olderMonths.some((m) => m.key === filter.value);

  return (
    <div className="browse" ref={ref}>
      <button
        type="button"
        className={`browse__toggle${open ? " is-open" : ""}`}
        aria-expanded={open}
        aria-controls="browse-panel"
        onClick={() => onOpenChange(!open)}
      >
        <span className="browse__toggle-mark" aria-hidden="true">
          {open ? "–" : "+"}
        </span>
        Browse by month or last name
      </button>

      {open && (
        <div className="browse__panel" id="browse-panel">
          <div className="browse__row" role="group" aria-label="Month">
            <span className="browse__label">Month</span>
            <button
              type="button"
              className={`browse__chip${filter.kind === "recent" ? " is-active" : ""}`}
              aria-pressed={filter.kind === "recent"}
              onClick={() => onFilter({ kind: "recent", value: recentMonths })}
            >
              Last {recentMonths} months
            </button>
            <button
              type="button"
              className={`browse__chip${filter.kind === "none" ? " is-active" : ""}`}
              aria-pressed={filter.kind === "none"}
              onClick={() => onFilter({ kind: "none" })}
            >
              All
            </button>
            {chipMonths.map((m) => (
              <button
                key={m.key}
                type="button"
                className={`browse__chip${isMonth(m.key) ? " is-active" : ""}`}
                aria-pressed={isMonth(m.key)}
                onClick={() => onFilter({ kind: "month", value: m.key })}
              >
                {monthLabel(m.key)} <span className="browse__count">{m.count}</span>
              </button>
            ))}
            {olderMonths.length > 0 && (
              <label className="browse__select">
                <select
                  aria-label="Earlier months"
                  className={olderActive ? "is-active" : ""}
                  value={olderActive ? filter.value : ""}
                  onChange={onSelect("month")}
                >
                  <option value="">Earlier…</option>
                  {olderMonths.map((m) => (
                    <option key={m.key} value={m.key}>
                      {monthLabel(m.key)} ({m.count})
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>

          <div className="browse__row browse__row--az" role="group" aria-label="Last name begins with">
            <span className="browse__label">Last name</span>
            {letters.map((l) => (
              <button
                key={l}
                type="button"
                className={`browse__letter${isLetter(l) ? " is-active" : ""}`}
                aria-pressed={isLetter(l)}
                onClick={() => onFilter({ kind: "letter", value: l })}
              >
                {l}
              </button>
            ))}
          </div>

          {(towns.length > 0 || homes.length > 0) && (
            <div className="browse__row browse__row--more">
              <button
                type="button"
                className="browse__more"
                aria-expanded={moreOpen}
                aria-controls="browse-more"
                onClick={() => setMoreOpen((v) => !v)}
              >
                {moreOpen ? "Fewer ways to browse" : "More ways to browse: town, funeral home"}
              </button>
              {moreOpen && (
                <div className="browse__row browse__row--selects" id="browse-more">
                  {towns.length > 0 && (
                    <label className="browse__select">
                      <span className="browse__label">Town</span>
                      <select
                        className={filter.kind === "town" ? "is-active" : ""}
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
                      <span className="browse__label">Funeral home</span>
                      <select
                        className={filter.kind === "home" ? "is-active" : ""}
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
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
});

export default BrowseBar;

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

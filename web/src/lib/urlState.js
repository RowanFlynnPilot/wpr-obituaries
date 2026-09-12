// Search and browse state mirrored into the URL — ?q=, ?month=, ?letter=,
// ?town=, ?home= — so Back from a person page lands on the same list and a
// filtered view can be shared or bookmarked. Values are validated on the way
// in: the URL is untrusted input, and a bad value falls back to the default
// view rather than a broken one. Embedded, the widget also posts the same
// search string to the parent (lib/frame.js) so the WordPress page can carry it.

const LETTER = /^[A-Z]$/;
const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/;
const MAX_VALUE = 80;
const FACETS = ["town", "home"];

// The state named by a search string, or null when it names none.
export function readState(search = window.location.search) {
  const p = new URLSearchParams(search);
  const q = (p.get("q") || "").slice(0, MAX_VALUE);
  if (q.trim()) return { query: q, filter: { kind: "none" } };
  const month = p.get("month") || "";
  if (MONTH.test(month)) return { query: "", filter: { kind: "month", value: month } };
  const letter = (p.get("letter") || "").toUpperCase();
  if (LETTER.test(letter)) return { query: "", filter: { kind: "letter", value: letter } };
  for (const kind of FACETS) {
    const value = (p.get(kind) || "").trim().slice(0, MAX_VALUE);
    if (value) return { query: "", filter: { kind, value } };
  }
  return null;
}

// The search string for a state: "" for the default view.
export function stateSearch(query, filter) {
  const p = new URLSearchParams();
  if (query.trim()) p.set("q", query.trim());
  else if (["month", "letter", ...FACETS].includes(filter.kind)) p.set(filter.kind, filter.value);
  const s = p.toString();
  return s ? `?${s}` : "";
}

// Replace (never push) so the reader's Back button still leaves the page.
export function writeState(query, filter) {
  const search = stateSearch(query, filter);
  if (search === window.location.search) return search;
  const { pathname, hash } = window.location;
  window.history.replaceState(null, "", `${pathname}${search}${hash}`);
  return search;
}

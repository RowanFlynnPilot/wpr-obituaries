// Name search that matches the way people say names.
//
// "Allan Jensen" must find "Allan Guy Jensen"; "Rosy Schmitt" must find
// `Rosemary "Rosy" M. Schmitt`; "munoz" must find "Muñoz". A record is a
// *name match* when every query token is a prefix of one of the name's own
// tokens (middle names, initials, nicknames and suffixes in between don't
// matter). Records that only mention the query elsewhere — the funeral home,
// the town, a maiden name inside the summary — are a second tier, listed after
// the names so a search for "Jensen" leads with the Jensens, not a community
// center.

const SUFFIXES = new Set(["jr", "sr", "ii", "iii", "iv", "v"]);

export function normalize(text) {
  return (text || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // fold diacritics: Muñoz -> Munoz
    .toLowerCase()
    .replace(/[“”"'’‘.,()]/g, " ") // quotes, dots, commas, parens are not letters
    .replace(/\s+/g, " ")
    .trim();
}

export function nameTokens(name) {
  return normalize(name)
    .split(" ")
    .filter((t) => t && !SUFFIXES.has(t));
}

export function queryTokens(query) {
  return normalize(query).split(" ").filter(Boolean);
}

function isNameMatch(tokens, ob) {
  const name = nameTokens(ob.name);
  return tokens.every((t) => name.some((n) => n.startsWith(t)));
}

function isMention(tokens, ob) {
  const haystack = normalize(
    [ob.homeName, ob.funeralHome, ob.town, ob.summary, ob.excerpt].filter(Boolean).join(" ")
  );
  return tokens.every((t) => haystack.includes(t));
}

// Returns { names, mentions } — both preserve the index's newest-first order.
export function searchObituaries(obituaries, query) {
  const tokens = queryTokens(query);
  if (tokens.length === 0) return { names: obituaries, mentions: [] };
  const names = [];
  const mentions = [];
  for (const ob of obituaries) {
    if (isNameMatch(tokens, ob)) names.push(ob);
    else if (isMention(tokens, ob)) mentions.push(ob);
  }
  return { names, mentions };
}

// Surname-first sort for the A–Z browse: "Jensen, Allan Guy" before
// "Johnson, Ryan".
export function bySurname(a, b) {
  const ta = nameTokens(a.name);
  const tb = nameTokens(b.name);
  const la = ta[ta.length - 1] || "";
  const lb = tb[tb.length - 1] || "";
  return la.localeCompare(lb) || (ta[0] || "").localeCompare(tb[0] || "");
}

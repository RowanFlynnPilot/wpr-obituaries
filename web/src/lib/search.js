// Name search that matches the way people say names.
//
// "Allan Jensen" must find "Allan Guy Jensen"; "Rosy Schmitt" must find
// `Rosemary "Rosy" M. Schmitt`; "munoz" must find "Muñoz"; "Tugnoli" must find
// "Latzig-Tugnoli". A record is a *name match* when every query token is a
// prefix of one of the name's own tokens (middle names, initials, nicknames
// and suffixes in between don't matter).
//
// Everything else the query can hit is not a person of that name, and the
// register says so rather than listing look-alike rows:
//   - the **funeral home's own name** ("Schmidt" is also Schmidt & Schulta) —
//     counted per home, offered as one line into that home's notices;
//   - a **mention** in the text (a maiden name, a surviving relative) — listed
//     after the names, each with the phrase that matched.

const SUFFIXES = new Set(["jr", "sr", "ii", "iii", "iv", "v"]);
const CONTEXT_WORDS = 6; // either side of the hit in a mention's evidence line

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

// A hyphenated surname is two names to the person searching: "Tugnoli" has to
// reach "Latzig-Tugnoli". The token stays whole for sorting and the A–Z index.
function startsToken(word, token) {
  return word.startsWith(token) || word.split("-").some((part) => part.startsWith(token));
}

function isNameMatch(tokens, ob) {
  const name = nameTokens(ob.name);
  return tokens.every((t) => name.some((n) => startsToken(n, t)));
}

function homeOf(ob) {
  return ob.homeName || ob.funeralHome || "";
}

function matchesAll(tokens, text) {
  const haystack = normalize(text);
  return tokens.every((t) => haystack.includes(t));
}

function isMention(tokens, ob) {
  return matchesAll(tokens, [ob.town, ob.summary, ob.excerpt].filter(Boolean).join(" "));
}

// The evidence a mention row owes the reader: the phrase around the hit, with
// the matched word marked. Split on words, not characters, so the highlight
// never lands mid-syllable and a folded index never has to map back.
export function matchSnippet(ob, tokens) {
  for (const text of [ob.summary, ob.excerpt]) {
    const words = (text || "").match(/\S+/g) || [];
    const hit = words.findIndex((w) => tokens.some((t) => normalize(w).includes(t)));
    if (hit === -1) continue;
    const from = Math.max(0, hit - CONTEXT_WORDS);
    const to = Math.min(words.length, hit + CONTEXT_WORDS + 1);
    const before = words.slice(from, hit).join(" ");
    const after = words.slice(hit + 1, to).join(" ");
    return {
      before: (from > 0 ? "…" : "") + before + (before ? " " : ""),
      hit: words[hit],
      after: (after ? " " : "") + after + (to < words.length ? "…" : ""),
    };
  }
  return null;
}

// Returns { names, mentions, homes }. `names` and `mentions` preserve the
// index's newest-first order; `mentions` entries carry their evidence
// ({ ob, match }); `homes` are the funeral homes whose own name matched,
// largest first.
export function searchObituaries(obituaries, query) {
  const tokens = queryTokens(query);
  if (tokens.length === 0) return { names: obituaries, mentions: [], homes: [] };
  const names = [];
  const mentions = [];
  const homeCounts = new Map();
  for (const ob of obituaries) {
    if (isNameMatch(tokens, ob)) {
      names.push(ob);
      continue;
    }
    const home = homeOf(ob);
    if (home && matchesAll(tokens, home)) {
      homeCounts.set(home, (homeCounts.get(home) || 0) + 1);
      continue;
    }
    if (isMention(tokens, ob)) mentions.push({ ob, match: matchSnippet(ob, tokens) });
  }
  const homes = [...homeCounts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
  return { names, mentions, homes };
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

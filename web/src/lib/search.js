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
//
// And when no name matches at all, the nearest spellings are offered, labelled
// as such: "Kruger" has to reach Krueger, "Shultz" has to reach Schultz. Names
// here are German and Polish and people spell them by ear.

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

// Edit distance with adjacent swaps ("Shcultz"), stopping early past `max`.
function distance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let prev2 = null;
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const row = [i];
    let best = i;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      let d = Math.min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + cost);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
        d = Math.min(d, prev2[j - 2] + 1);
      }
      row.push(d);
      if (d < best) best = d;
    }
    if (best > max) return max + 1;
    prev2 = prev;
    prev = row;
  }
  return prev[b.length];
}

// How far a spelling may stray: one slip in a name of ordinary length, two in a
// long one. A three-letter word is too short to guess at on its own ("Jon"
// would reach Joan, Ron and Don), so it may stray only beside another word.
function allowance(token, alone) {
  if (token.length >= 8) return 2;
  if (token.length >= 4) return 1;
  return token.length === 3 && !alone ? 1 : 0;
}

// The total slips needed for every query word to land on one of the name's
// words, or null when a word lands nowhere. Zero never happens here: that is a
// name match, and it is found first.
function closeness(tokens, ob) {
  const parts = nameTokens(ob.name).flatMap((n) => (n.includes("-") ? [n, ...n.split("-")] : [n]));
  let total = 0;
  for (const t of tokens) {
    if (parts.some((n) => n.startsWith(t))) continue;
    const max = allowance(t, tokens.length === 1);
    let best = max + 1;
    for (const n of parts) best = Math.min(best, distance(t, n, max));
    if (best > max) return null;
    total += best;
  }
  return total;
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

// Returns { names, close, mentions, homes }. `names` and `mentions` preserve
// the index's newest-first order; `mentions` entries carry their evidence
// ({ ob, match }); `homes` are the funeral homes whose own name matched,
// largest first; `close` is the nearest spellings, nearest first, and is only
// ever filled when no name matched.
export function searchObituaries(obituaries, query) {
  const tokens = queryTokens(query);
  if (tokens.length === 0) return { names: obituaries, close: [], mentions: [], homes: [] };
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
  const close = [];
  if (names.length === 0) {
    for (const ob of obituaries) {
      const slips = closeness(tokens, ob);
      if (slips !== null) close.push({ ob, slips });
    }
    close.sort((a, b) => a.slips - b.slips); // stable: newest first within a distance
  }
  return { names, close: close.map((c) => c.ob), mentions, homes };
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

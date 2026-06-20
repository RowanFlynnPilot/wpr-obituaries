// Display helpers. Each does exactly one thing.

export function lifespan(ob) {
  const birth = ob.birthDate ? ob.birthDate.slice(0, 4) : "";
  const death = ob.deathDate
    ? ob.deathDate.slice(0, 4)
    : ob.deathYear
    ? String(ob.deathYear)
    : "";
  if (birth && death) return `${birth} – ${death}`;
  return death || "";
}

export function publishedOn(ob) {
  // ob.sourceDate is an ISO date like "2026-06-19".
  return dateLabel(ob.sourceDate);
}

export function dateLabel(sourceDate) {
  const [y, m, d] = sourceDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function monthKey(sourceDate) {
  return sourceDate.slice(0, 7); // "2026-06"
}

export function monthLabel(monthKey) {
  const [y, m] = monthKey.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}

const SUFFIXES = new Set(["jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"]);

export function lastNameInitial(name) {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter((p) => !SUFFIXES.has(p.toLowerCase()));
  const last = parts[parts.length - 1] || name;
  const ch = (last[0] || "").toUpperCase();
  return /[A-Z]/.test(ch) ? ch : "#";
}

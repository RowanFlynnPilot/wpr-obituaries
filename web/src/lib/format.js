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
  const [y, m, d] = ob.sourceDate.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

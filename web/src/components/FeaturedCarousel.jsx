import { useEffect, useMemo, useRef, useState } from "react";
import { lifespan, photoSrc } from "../lib/format.js";

const BASE = import.meta.env.BASE_URL;
const DAYS = 7; // draw from the past week
const MAX = 5; // this week's faces, newest first — a handful, not a gallery
const INTERVAL = 6500; // gentle, dignified cadence
const REDUCED = "(prefers-reduced-motion: reduce)";

function useMediaQuery(query) {
  const [matches, setMatches] = useState(
    () => typeof window !== "undefined" && window.matchMedia(query).matches
  );
  useEffect(() => {
    const mq = window.matchMedia(query);
    const onChange = (e) => setMatches(e.matches);
    setMatches(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [query]);
  return matches;
}

function withinDays(sourceDate, days) {
  const [y, m, d] = sourceDate.split("-").map(Number);
  const when = new Date(y, m - 1, d);
  const cutoff = new Date();
  cutoff.setHours(0, 0, 0, 0);
  cutoff.setDate(cutoff.getDate() - days);
  return when >= cutoff;
}

// `obituaries` arrives newest death first (App sorts once), so the pool reads
// as "this week" and a returning visitor sees the same set — not a shuffle.
// On a quiet stretch (nothing photographed in the window) it falls back to the
// most recent portraits so the strip never vanishes. It sits at the top of the
// default view, under the search, and stands down the moment the reader
// searches or browses: then the list itself is the answer.
export default function FeaturedCarousel({ obituaries }) {
  const reduced = useMediaQuery(REDUCED);
  const featured = useMemo(() => {
    const photographed = obituaries.filter((o) => o.photoUrl);
    const recent = photographed.filter((o) => withinDays(o.sourceDate, DAYS));
    return (recent.length ? recent : photographed).slice(0, MAX);
  }, [obituaries]);

  const [index, setIndex] = useState(0);
  const [hovered, setHovered] = useState(false);
  // Auto-advance stops for good after any manual choice (arrow, dot, or the
  // Pause control) — hover/focus pause never fires on touch, so an explicit,
  // visible control is the pause a phone reader has (WCAG 2.2.2).
  const [stopped, setStopped] = useState(false);
  const dotsRef = useRef(null);

  // Reset if the underlying set changes (e.g. fresh data load).
  useEffect(() => setIndex(0), [featured.length]);

  const playing = featured.length > 1 && !hovered && !stopped && !reduced;
  useEffect(() => {
    if (!playing) return;
    const t = setInterval(
      () => setIndex((i) => (i + 1) % featured.length),
      INTERVAL
    );
    return () => clearInterval(t);
  }, [playing, featured.length]);

  if (featured.length === 0) return null;

  const i = index % featured.length;
  const ob = featured[i];
  const span = lifespan(ob);
  const href = `${BASE}o/${ob.slug}.html`;
  const go = (n) => {
    setStopped(true);
    setIndex((n + featured.length) % featured.length);
  };

  // The dots are ONE tab stop with a roving tabindex: arrow keys move between
  // them, so the strip costs a keyboard reader four stops (prev, card, next,
  // dots) plus Pause — not one per portrait.
  const onDotsKey = (e) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    let n;
    if (step) n = i + step;
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = featured.length - 1;
    else return;
    e.preventDefault();
    n = (n + featured.length) % featured.length;
    go(n);
    // Every dot is already in the DOM; only its tabindex changes on render,
    // so the new one can take focus synchronously.
    dotsRef.current?.children[n]?.focus();
  };

  return (
    <section
      className="featured"
      aria-label="Recently remembered"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocusCapture={() => setHovered(true)}
      onBlurCapture={() => setHovered(false)}
    >
      <h2 className="featured__kicker">Recently Remembered</h2>

      <div className="featured__stage">
        {featured.length > 1 && (
          <button
            type="button"
            className="featured__arrow featured__arrow--prev"
            aria-label="Previous"
            onClick={() => go(i - 1)}
          >
            ‹
          </button>
        )}

        <a className="featured__card" href={href} target="_top" key={ob.slug}>
          <img
            className="featured__photo"
            src={photoSrc(ob.photoUrl)}
            alt=""
            loading="lazy"
            width="132"
            height="168"
          />
          <div className="featured__text">
            <span className="featured__name">{ob.name}</span>
            {span && <span className="featured__span">{span}</span>}
            <span className="featured__excerpt">
              {ob.excerpt || ob.summary}
            </span>
            <span className="featured__more">Read the full obituary →</span>
          </div>
        </a>

        {featured.length > 1 && (
          <button
            type="button"
            className="featured__arrow featured__arrow--next"
            aria-label="Next"
            onClick={() => go(i + 1)}
          >
            ›
          </button>
        )}
      </div>

      {/* Screen readers hear a change the reader asked for. While the strip is
          advancing on its own the region stays empty: someone reading the
          register must not be interrupted by a new name every 6.5 seconds. */}
      <p className="sr-only" aria-live="polite" aria-atomic="true">
        {playing ? "" : `Now showing ${ob.name}, ${i + 1} of ${featured.length}`}
      </p>

      {featured.length > 1 && (
        <div className="featured__nav">
          <div
            className="featured__dots"
            role="group"
            aria-label="Choose a featured obituary (arrow keys)"
            ref={dotsRef}
            onKeyDown={onDotsKey}
          >
            {featured.map((f, n) => (
              <button
                key={f.slug}
                type="button"
                className={`featured__dot${n === i ? " is-active" : ""}`}
                aria-label={`Show ${f.name}`}
                aria-current={n === i}
                tabIndex={n === i ? 0 : -1}
                onClick={() => go(n)}
              />
            ))}
          </div>
          {!reduced && (
            <button
              type="button"
              className="featured__pause"
              aria-label={stopped ? "Resume auto-advance" : "Pause auto-advance"}
              onClick={() => setStopped((s) => !s)}
            >
              {/* The visible word has to appear in the accessible name, or
                  voice control can't activate the button by what it reads
                  (WCAG 2.5.3): "Resume", not "Play". */}
              {stopped ? "Resume" : "Pause"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}

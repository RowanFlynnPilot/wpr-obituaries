import { useEffect, useMemo, useState } from "react";
import { lifespan, photoSrc } from "../lib/format.js";

const BASE = import.meta.env.BASE_URL;
const DAYS = 7; // draw from the past week
const MAX = 10; // a random handful, fresh on each load
const INTERVAL = 6500; // gentle, dignified cadence

function withinDays(sourceDate, days) {
  const [y, m, d] = sourceDate.split("-").map(Number);
  const when = new Date(y, m - 1, d);
  const cutoff = new Date();
  cutoff.setHours(0, 0, 0, 0);
  cutoff.setDate(cutoff.getDate() - days);
  return when >= cutoff;
}

export default function FeaturedCarousel({ obituaries }) {
  const featured = useMemo(() => {
    // filter()/slice() return fresh arrays, so shuffling in place is safe.
    const photographed = obituaries.filter((o) => o.photoUrl);
    const recent = photographed.filter((o) => withinDays(o.sourceDate, DAYS));
    // Prefer the past week; but on a quiet stretch (nothing photographed in the
    // window) fall back to the most recent portraits so the hero never vanishes.
    const pool = recent.length ? recent : photographed.slice(0, MAX * 2);
    // Fisher–Yates shuffle, then take MAX — a unique selection each page load.
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [pool[i], pool[j]] = [pool[j], pool[i]];
    }
    return pool.slice(0, MAX);
  }, [obituaries]);

  const [index, setIndex] = useState(0);
  const [hovered, setHovered] = useState(false);
  // Auto-advance stops for good after any manual choice (arrow, dot, or the
  // Pause control) — hover/focus pause never fires on touch, so an explicit,
  // visible control is the pause a phone reader has (WCAG 2.2.2).
  const [stopped, setStopped] = useState(false);
  const reduced =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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

  return (
    <section
      className="featured"
      aria-label="Recently remembered"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocusCapture={() => setHovered(true)}
      onBlurCapture={() => setHovered(false)}
    >
      <p className="featured__kicker">Recently Remembered</p>

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

      {/* Screen readers hear the change without the card itself being live. */}
      <p className="sr-only" aria-live="polite" aria-atomic="true">
        Now showing {ob.name}, {i + 1} of {featured.length}
      </p>

      {featured.length > 1 && (
        <div className="featured__nav">
          <div className="featured__dots" role="group" aria-label="Choose a featured obituary">
            {featured.map((f, n) => (
              <button
                key={f.slug}
                type="button"
                className={`featured__dot${n === i ? " is-active" : ""}`}
                aria-label={`Show ${f.name}`}
                aria-current={n === i}
                onClick={() => go(n)}
              />
            ))}
          </div>
          {!reduced && (
            <button
              type="button"
              className="featured__pause"
              aria-pressed={stopped}
              onClick={() => setStopped((s) => !s)}
            >
              {stopped ? "Play" : "Pause"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}

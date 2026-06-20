import { useEffect, useMemo, useState } from "react";
import { lifespan, photoSrc } from "../lib/format.js";

const BASE = import.meta.env.BASE_URL;
const DAYS = 7; // feature the past week
const MAX = 10; // a highlight, not the whole list
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
  const featured = useMemo(
    () =>
      obituaries
        .filter((o) => o.photoUrl && withinDays(o.sourceDate, DAYS))
        .slice(0, MAX),
    [obituaries]
  );

  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  // Reset if the underlying set changes (e.g. fresh data load).
  useEffect(() => setIndex(0), [featured.length]);

  useEffect(() => {
    if (featured.length <= 1 || paused) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setInterval(
      () => setIndex((i) => (i + 1) % featured.length),
      INTERVAL
    );
    return () => clearInterval(t);
  }, [featured.length, paused]);

  if (featured.length === 0) return null;

  const i = index % featured.length;
  const ob = featured[i];
  const span = lifespan(ob);
  const href = `${BASE}o/${ob.slug}.html`;
  const go = (n) => setIndex((n + featured.length) % featured.length);

  return (
    <section
      className="featured"
      aria-label="Recently remembered"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={() => setPaused(false)}
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

        <a className="featured__card" href={href} key={ob.slug}>
          <img
            className="featured__photo"
            src={photoSrc(ob.photoUrl)}
            alt={ob.name}
            loading="lazy"
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

      {featured.length > 1 && (
        <div className="featured__dots" role="tablist">
          {featured.map((f, n) => (
            <button
              key={f.slug}
              type="button"
              className={`featured__dot${n === i ? " is-active" : ""}`}
              aria-label={`Show ${f.name}`}
              aria-selected={n === i}
              onClick={() => go(n)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

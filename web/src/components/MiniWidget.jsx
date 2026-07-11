import { useEffect, useMemo, useRef, useState } from "react";
import config from "../config.js";
import { trackEvent } from "../lib/analytics.js";
import { lifespan, photoSrc } from "../lib/format.js";

const BASE = import.meta.env.BASE_URL;
const { identity } = config;
const POOL = 20; // draw from the N most recent…
const SHOW = 10; // …and flip through this many
const ADVANCE_MS = 6000;

// Where "View all obituaries" points: the WordPress page hosting the full tool,
// passed by the embed snippet as ?link= (URL-encoded). Falls back to this
// deployment's own register until that page exists.
function registerUrl() {
  const link = new URLSearchParams(window.location.search).get("link");
  return link || BASE;
}

function shuffle(list) {
  const a = [...list];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

export default function MiniWidget() {
  const [data, setData] = useState(null);
  const [sponsor, setSponsor] = useState(null);
  const [error, setError] = useState(null);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const timer = useRef(null);

  useEffect(() => {
    Promise.all([
      fetch(`${BASE}data/obituaries.json`).then(ok),
      fetch(`${BASE}data/sponsor.json`).then(ok),
    ])
      .then(([idx, sp]) => {
        setData(idx);
        setSponsor(sp);
      })
      .catch((e) => setError(e.message));
  }, []);

  // Random order each load: shuffle the freshest POOL, keep SHOW.
  const picks = useMemo(() => {
    if (!data) return [];
    return shuffle(data.obituaries.slice(0, POOL)).slice(0, SHOW);
  }, [data]);

  useEffect(() => {
    if (paused || picks.length < 2) return undefined;
    // Honour reduced-motion: no auto-advance (the dots still let you step through).
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return undefined;
    timer.current = setInterval(
      () => setIndex((i) => (i + 1) % picks.length),
      ADVANCE_MS
    );
    return () => clearInterval(timer.current);
  }, [paused, picks.length]);

  if (error) {
    return (
      <aside className="mini mini--message" aria-label={`Recent obituaries from ${identity.name}`}>
        <p className="mini__kicker">In Memoriam · {identity.shortName}</p>
        <p className="mini__error">Obituaries are unavailable right now.</p>
      </aside>
    );
  }
  if (!picks.length) {
    return (
      <aside className="mini mini--loading" aria-busy="true" aria-label="Loading obituaries">
        <p className="mini__kicker">In Memoriam · {identity.shortName}</p>
      </aside>
    );
  }

  const ob = picks[index];
  const span = lifespan(ob);
  const sponsors = sponsor?.sponsors || [];
  const allUrl = registerUrl();
  const go = (delta) => setIndex((i) => (i + delta + picks.length) % picks.length);

  return (
    <aside
      className="mini"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={() => setPaused(false)}
      aria-label={`Recent obituaries from ${identity.name}`}
    >
      <p className="mini__kicker">In Memoriam · {identity.shortName}</p>

      <a
        className="mini__card"
        href={`${BASE}o/${ob.slug}.html`}
        target="_top"
        key={ob.slug}
      >
        {ob.photoUrl ? (
          <img className="mini__photo" src={photoSrc(ob.photoUrl)} alt="" loading="lazy" />
        ) : (
          <span className="mini__photo mini__photo--blank" aria-hidden="true">
            {initials(ob.name)}
          </span>
        )}
        <span className="mini__text">
          <span className="mini__name">{ob.name}</span>
          {span && <span className="mini__span">{span}</span>}
          {ob.summary && <span className="mini__summary">{ob.summary}</span>}
        </span>
      </a>

      {picks.length > 1 && (
        <div className="mini__nav">
          <button
            className="mini__arrow"
            type="button"
            aria-label="Previous obituary"
            onClick={() => go(-1)}
          >
            ‹
          </button>
          <div className="mini__dots" role="group" aria-label="More obituaries">
            {picks.map((p, i) => (
              <button
                key={p.slug}
                type="button"
                className={`mini__dot${i === index ? " is-active" : ""}`}
                aria-label={p.name}
                aria-current={i === index}
                onClick={() => setIndex(i)}
              />
            ))}
          </div>
          <button
            className="mini__arrow"
            type="button"
            aria-label="Next obituary"
            onClick={() => go(1)}
          >
            ›
          </button>
        </div>
      )}

      <a className="mini__all" href={allUrl} target="_top">
        View all obituaries →
      </a>

      {sponsors.length > 0 && (
        <div className="mini__sponsors">
          <span className="mini__sponsor-label">
            {sponsor.label || "Made possible by"}
          </span>
          <span className="mini__sponsor-logos">
            {sponsors.map((s) => (
              <SponsorLogo key={s.name} s={s} />
            ))}
          </span>
        </div>
      )}
    </aside>
  );
}

function SponsorLogo({ s }) {
  const img = <img src={`${BASE}${s.logo}`} alt={s.name} loading="lazy" />;
  return s.url ? (
    <a
      href={s.url}
      target="_blank"
      rel="noopener"
      onClick={() => trackEvent("Sponsor click", { label: s.name })}
    >
      {img}
    </a>
  ) : (
    <span>{img}</span>
  );
}

function ok(response) {
  if (!response.ok) {
    throw new Error(`${response.url} returned ${response.status}`);
  }
  return response.json();
}

import { useEffect, useId, useMemo, useRef, useState } from "react";
import config from "../config.js";
import { trackEvent } from "../lib/analytics.js";
import { initials, lifespan, photoSrc } from "../lib/format.js";
import { sponsorHref } from "../lib/sponsor.js";

const BASE = import.meta.env.BASE_URL;
const { identity } = config;
const POOL = 20; // draw from the N most recent…
const SHOW = 10; // …and flip through this many
const ADVANCE_MS = 6000;

// Where "View all obituaries" points: the WordPress page hosting the full tool,
// passed by the embed snippet as ?link= (URL-encoded). Only http(s) URLs are
// accepted — the value is attacker-reachable and lands in a target="_top" href.
// Falls back to this deployment's own register until that page exists.
function registerUrl() {
  const link = new URLSearchParams(window.location.search).get("link");
  return link && /^https?:\/\//i.test(link) ? link : BASE;
}

function shuffle(list) {
  const a = [...list];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export default function MiniWidget() {
  const id = useId();
  const [data, setData] = useState(null);
  const [sponsor, setSponsor] = useState(null);
  const [error, setError] = useState(null);
  const [index, setIndex] = useState(0);
  // Hover or focus inside the card holds it still while someone is reading.
  const [held, setHeld] = useState(false);
  // Stopped for good by the Pause control or any manual choice. The widget sits
  // beside article text and moves on its own, so a visible way to stop it is
  // required (WCAG 2.2.2) — hover never fires on a phone.
  const [stopped, setStopped] = useState(false);
  const dotsRef = useRef(null);
  const reduced =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    // recent.json is the small feed of the freshest few records — the mini
    // widget never needs the full (forever-growing) index.
    Promise.all([
      fetch(`${BASE}data/recent.json`).then(ok),
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

  // Under reduced motion it never advances on its own (the dots still step).
  const playing = picks.length > 1 && !held && !stopped && !reduced;
  useEffect(() => {
    if (!playing) return undefined;
    const t = setInterval(() => setIndex((i) => (i + 1) % picks.length), ADVANCE_MS);
    return () => clearInterval(t);
  }, [playing, picks.length]);

  if (error) {
    return (
      <aside className="mini mini--message" aria-label={`Recent obituaries from ${identity.name}`}>
        <p className="mini__kicker">In Memoriam · {identity.shortName}</p>
        <p className="mini__error">Obituaries are unavailable right now.</p>
      </aside>
    );
  }
  if (!data) {
    return (
      <aside className="mini mini--loading" aria-busy="true" aria-label="Loading obituaries">
        <p className="mini__kicker">In Memoriam · {identity.shortName}</p>
      </aside>
    );
  }
  if (!picks.length) {
    // Loaded but empty — show the quiet message, not a permanent skeleton.
    return (
      <aside className="mini mini--message" aria-label={`Recent obituaries from ${identity.name}`}>
        <p className="mini__kicker">In Memoriam · {identity.shortName}</p>
        <p className="mini__error">No recent obituaries to show.</p>
      </aside>
    );
  }

  const ob = picks[index];
  const span = lifespan(ob);
  const sponsors = sponsor?.sponsors || [];
  const allUrl = registerUrl();
  const go = (n) => {
    setStopped(true);
    setIndex((n + picks.length) % picks.length);
  };

  // The dots are one Tab stop with a roving tabindex: arrow keys, Home and End
  // move between them, so ten people cost a keyboard reader one stop, not ten.
  const onDotsKey = (e) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    let n;
    if (step) n = index + step;
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = picks.length - 1;
    else return;
    e.preventDefault();
    n = (n + picks.length) % picks.length;
    go(n);
    // Every dot is already rendered; only its tabindex moves, so focus can too.
    dotsRef.current?.children[n]?.focus();
  };

  return (
    <aside
      className="mini"
      onMouseEnter={() => setHeld(true)}
      onMouseLeave={() => setHeld(false)}
      onFocusCapture={() => setHeld(true)}
      onBlurCapture={() => setHeld(false)}
      aria-label={`Recent obituaries from ${identity.name}`}
    >
      <p className="mini__kicker">In Memoriam · {identity.shortName}</p>

      {/* Named by the person and described by their years; the summary stays
          out of the link's name. */}
      <a
        className="mini__card"
        href={`${BASE}o/${ob.slug}.html`}
        target="_top"
        key={ob.slug}
        aria-labelledby={`${id}-name`}
        aria-describedby={span ? `${id}-span` : undefined}
      >
        {ob.photoUrl ? (
          <img className="mini__photo" src={photoSrc(ob.photoUrl)} alt="" loading="lazy" />
        ) : (
          <span className="mini__photo mini__photo--blank" aria-hidden="true">
            {initials(ob.name)}
          </span>
        )}
        <span className="mini__text">
          <span className="mini__name" id={`${id}-name`}>
            {ob.name}
          </span>
          {span && (
            <span className="mini__span" id={`${id}-span`}>
              {span}
            </span>
          )}
          {ob.summary && <span className="mini__summary">{ob.summary}</span>}
        </span>
      </a>

      {/* A stable region that speaks only for a change the reader made: while
          the card advances on its own it stays empty, so article text is never
          interrupted every six seconds. */}
      <p className="sr-only" aria-live="polite" aria-atomic="true">
        {playing ? "" : `Now showing ${ob.name}, ${index + 1} of ${picks.length}`}
      </p>

      {picks.length > 1 && (
        <div className="mini__nav">
          <button
            className="mini__arrow"
            type="button"
            aria-label="Previous obituary"
            onClick={() => go(index - 1)}
          >
            ‹
          </button>
          <div
            className="mini__dots"
            role="group"
            aria-label="Choose an obituary (arrow keys)"
            ref={dotsRef}
            onKeyDown={onDotsKey}
          >
            {picks.map((p, i) => (
              <button
                key={p.slug}
                type="button"
                className={`mini__dot${i === index ? " is-active" : ""}`}
                aria-label={`Show ${p.name}`}
                aria-current={i === index}
                tabIndex={i === index ? 0 : -1}
                onClick={() => go(i)}
              />
            ))}
          </div>
          <button
            className="mini__arrow"
            type="button"
            aria-label="Next obituary"
            onClick={() => go(index + 1)}
          >
            ›
          </button>
        </div>
      )}

      <div className={`mini__foot${picks.length > 1 && !reduced ? " mini__foot--pause" : ""}`}>
        {picks.length > 1 && !reduced && (
          <button
            type="button"
            className="mini__pause"
            aria-label={stopped ? "Resume auto-advance" : "Pause auto-advance"}
            onClick={() => setStopped((s) => !s)}
          >
            {/* The visible word sits inside the accessible name, so voice
                control can press it by what it reads (WCAG 2.5.3). */}
            {stopped ? "Resume" : "Pause"}
          </button>
        )}
        <a className="mini__all" href={allUrl} target="_top">
          View all obituaries →
        </a>
      </div>

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
      href={sponsorHref(s.url)}
      target="_blank"
      rel="noopener sponsored"
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

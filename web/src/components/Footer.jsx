import config from "../config.js";
import { trackEvent } from "../lib/analytics.js";
import { sponsorHref } from "../lib/sponsor.js";

const BASE = import.meta.env.BASE_URL;
const { identity, branding, copy } = config;

export default function Footer({ sponsor }) {
  const sponsors = sponsor?.sponsors || [];
  return (
    <footer className="footer">
      {sponsors.length > 0 && (
        <section className="sponsor-card">
          <p className="sponsor-card__label">
            {sponsor.label || "Obituaries made possible by"}
          </p>
          <div className="sponsor-card__logos">
            {sponsors.map((s) => {
              const img = <img src={`${BASE}${s.logo}`} alt={s.name} />;
              return s.url ? (
                <a
                  key={s.name}
                  className="sponsor-card__logo"
                  href={sponsorHref(s.url)}
                  target="_blank"
                  rel="noopener sponsored"
                  onClick={() => trackEvent("Sponsor click", { label: s.name })}
                >
                  {img}
                </a>
              ) : (
                <span key={s.name} className="sponsor-card__logo">
                  {img}
                </span>
              );
            })}
          </div>
        </section>
      )}

      <hr className="footer__rule" />
      <p className="footer__index">
        <a href={`${BASE}archive.html`} target="_top">
          Browse the full obituary index →
        </a>
      </p>
      {/* Colophon: where a reader checks whether to trust the page — provenance,
          then the newsroom's name and phone. */}
      <div className="footer__colophon">
        <img
          className="footer__seal"
          src={`${BASE}${branding.sealPath}`}
          alt=""
          width="44"
          height="44"
          loading="lazy"
        />
        <div className="footer__lines">
          {copy.provenance && <p>{copy.provenance}</p>}
          <p>
            {identity.name}
            {identity.phone ? ` · ${identity.phone}` : ""} — {copy.footerTagline}
          </p>
        </div>
      </div>
    </footer>
  );
}

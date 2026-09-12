import config from "../config.js";
import { trackEvent } from "../lib/analytics.js";
import { sponsorHref } from "../lib/sponsor.js";

const BASE = import.meta.env.BASE_URL;
const { identity, branding, copy } = config;

// Order matters at the end of a memorial page: the reader's next steps (the
// full index, submitting a notice) come first, the sponsor card after them,
// and the colophon — provenance and the newsroom's phone — closes the page.
// The sponsor card is never the last thing.
export default function Footer({ sponsor, children }) {
  const sponsors = sponsor?.sponsors || [];
  return (
    <footer className="footer">
      <hr className="footer__rule" />
      <div className="footer__next">
        <p className="footer__index">
          <a href={`${BASE}archive.html`} target="_top">
            Browse the full obituary index →
          </a>
        </p>
        {children}
      </div>

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

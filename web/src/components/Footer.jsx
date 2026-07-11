import config from "../config.js";
import { trackEvent } from "../lib/analytics.js";

const BASE = import.meta.env.BASE_URL;
const { identity, copy } = config;

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
                  href={s.url}
                  target="_blank"
                  rel="noopener"
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
      <p className="footer__fineprint">
        {identity.name} — {copy.footerTagline}
      </p>
    </footer>
  );
}

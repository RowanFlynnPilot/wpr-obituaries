const BASE = import.meta.env.BASE_URL;

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
      <p className="footer__fineprint">
        Wausau Pilot &amp; Review — nonprofit local journalism for north central
        Wisconsin.
      </p>
    </footer>
  );
}

const BASE = import.meta.env.BASE_URL;

export default function Footer({ sponsor }) {
  return (
    <footer className="footer">
      {sponsor?.logo && (
        <section className="sponsor-card">
          <p className="sponsor-card__label">Obituaries made possible by</p>
          {sponsor.url ? (
            <a
              className="sponsor-card__logo"
              href={sponsor.url}
              target="_blank"
              rel="noopener"
            >
              <img src={`${BASE}${sponsor.logo}`} alt={sponsor.name} />
            </a>
          ) : (
            <span className="sponsor-card__logo">
              <img src={`${BASE}${sponsor.logo}`} alt={sponsor.name} />
            </span>
          )}
          {sponsor.tagline && (
            <p className="sponsor-card__tagline">{sponsor.tagline}</p>
          )}
        </section>
      )}

      <hr className="footer__rule" />
      <p className="footer__submit">
        To submit an obituary, email it with a photo to{" "}
        <a href="mailto:editor@wausaupilotandreview.com">
          editor@wausaupilotandreview.com
        </a>
        , or ask your funeral home for assistance. There is no charge.
      </p>
      <p className="footer__fineprint">
        Wausau Pilot &amp; Review — nonprofit local journalism for north central
        Wisconsin.
      </p>
    </footer>
  );
}

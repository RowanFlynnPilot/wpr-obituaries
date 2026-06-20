const LOGO =
  "https://wausaupilotandreview.com/wp-content/uploads/2024/04/WausauPilotandReviewLogo.png";

const BASE = import.meta.env.BASE_URL;

export default function Masthead({ sponsor }) {
  const sponsors = sponsor?.sponsors || [];
  return (
    <header className="masthead">
      <a
        className="masthead__logo"
        href="https://wausaupilotandreview.com"
        target="_blank"
        rel="noopener"
      >
        <img src={LOGO} alt="Wausau Pilot & Review" />
      </a>
      <p className="masthead__eyebrow">In Memoriam</p>
      <h1 className="masthead__title">Obituaries</h1>
      <p className="masthead__lede">
        Remembering the lives of Wausau and Marathon County, published free of
        charge each Monday, Wednesday and Friday.
      </p>
      <p className="masthead__submit">
        Email obituaries with photos to{" "}
        <a href="mailto:darren@wausaupilotandreview.com">
          darren@wausaupilotandreview.com
        </a>
        , or ask your funeral director for assistance.
      </p>

      {sponsors.length > 0 && (
        <div className="masthead__sponsors">
          <span className="masthead__sponsor-label">
            {sponsor.label || "Made possible by"}
          </span>
          <div className="masthead__sponsor-logos">
            {sponsors.map((s) => (
              <SponsorLogo key={s.name} s={s} />
            ))}
          </div>
        </div>
      )}

      <hr className="masthead__rule" />
    </header>
  );
}

function SponsorLogo({ s }) {
  const img = <img src={`${BASE}${s.logo}`} alt={s.name} loading="lazy" />;
  return s.url ? (
    <a
      className="masthead__sponsor-logo"
      href={s.url}
      target="_blank"
      rel="noopener"
    >
      {img}
    </a>
  ) : (
    <span className="masthead__sponsor-logo">{img}</span>
  );
}

const LOGO =
  "https://wausaupilotandreview.com/wp-content/uploads/2024/04/WausauPilotandReviewLogo.png";

const BASE = import.meta.env.BASE_URL;

export default function Masthead({ sponsor }) {
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
        Remembering the lives of Wausau and Marathon County. Published free of
        charge each Monday, Wednesday and Friday.
      </p>

      {sponsor?.logo && (
        <p className="masthead__sponsor">
          <span className="masthead__sponsor-label">Made possible by</span>
          <SponsorLogo sponsor={sponsor} className="masthead__sponsor-logo" />
        </p>
      )}

      <hr className="masthead__rule" />
    </header>
  );
}

function SponsorLogo({ sponsor, className }) {
  const img = (
    <img src={`${BASE}${sponsor.logo}`} alt={sponsor.name} loading="lazy" />
  );
  return sponsor.url ? (
    <a className={className} href={sponsor.url} target="_blank" rel="noopener">
      {img}
    </a>
  ) : (
    <span className={className}>{img}</span>
  );
}

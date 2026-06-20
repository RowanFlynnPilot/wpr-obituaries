const LOGO =
  "https://wausaupilotandreview.com/wp-content/uploads/2024/04/WausauPilotandReviewLogo.png";

export default function Masthead({ sponsor }) {
  return (
    <header className="masthead">
      <a className="masthead__logo" href="https://wausaupilotandreview.com">
        <img src={LOGO} alt="Wausau Pilot & Review" />
      </a>
      <p className="masthead__eyebrow">In Memoriam</p>
      <h1 className="masthead__title">Obituaries</h1>
      <p className="masthead__lede">
        Remembering the lives of Wausau and Marathon County. Published free of
        charge each Monday, Wednesday and Friday.
      </p>
      {sponsor?.name && (
        <p className="masthead__sponsor">
          Made possible by{" "}
          {sponsor.url ? (
            <a href={sponsor.url}>{sponsor.name}</a>
          ) : (
            sponsor.name
          )}
        </p>
      )}
    </header>
  );
}

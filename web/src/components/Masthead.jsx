import config from "../config.js";
import { trackEvent } from "../lib/analytics.js";
import { sponsorHref } from "../lib/sponsor.js";

const BASE = import.meta.env.BASE_URL;
const { identity, branding, copy } = config;

// The order is the argument: the newsroom's flag, the title, one line of
// context, then the search — the reader's task — before anything the newsroom
// wants (sponsors). Submissions live in the footer.
export default function Masthead({ sponsor, search = null }) {
  const sponsors = sponsor?.sponsors || [];
  return (
    <header className="masthead">
      <a
        className="masthead__flag"
        href={identity.url}
        target="_blank"
        rel="noopener"
        aria-label={identity.name}
      >
        <img
          className="masthead__seal"
          src={`${BASE}${branding.sealPath}`}
          alt=""
          width="52"
          height="52"
        />
        <img
          className="masthead__wordmark"
          src={branding.logoPath ? `${BASE}${branding.logoPath}` : branding.logoUrl}
          alt={identity.name}
        />
      </a>
      {identity.tagline && <p className="masthead__tagline">{identity.tagline}</p>}
      <div className="masthead__flag-rule" aria-hidden="true" />
      <p className="masthead__eyebrow">In Memoriam</p>
      <h1 className="masthead__title">Obituaries</h1>
      <p className="masthead__lede">{copy.lede}</p>

      {search}

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
      href={sponsorHref(s.url)}
      target="_blank"
      rel="noopener sponsored"
      onClick={() => trackEvent("Sponsor click", { label: s.name })}
    >
      {img}
    </a>
  ) : (
    <span className="masthead__sponsor-logo">{img}</span>
  );
}

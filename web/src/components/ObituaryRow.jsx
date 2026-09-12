import { initials, lifespan, photoSrc } from "../lib/format.js";

export default function ObituaryRow({ ob }) {
  const span = lifespan(ob);
  const href = `${import.meta.env.BASE_URL}o/${ob.slug}.html`;
  // The scannable facts — lifespan and town — sit outside the sentence, on
  // the typewriter line, so "is this my Frank?" is answered without reading.
  const facts = [span, ob.town].filter(Boolean).join(" · ");

  return (
    <li className="entry">
      <a className="entry__link" href={href} target="_top">
        {ob.photoUrl ? (
          <img
            className="entry__photo"
            src={photoSrc(ob.photoUrl)}
            alt=""
            loading="lazy"
            width="66"
            height="66"
          />
        ) : (
          <span className="entry__photo entry__photo--blank" aria-hidden="true">
            {initials(ob.name)}
          </span>
        )}
        <span className="entry__text">
          <span className="entry__name">{ob.name}</span>
          {facts && <span className="entry__span">{facts}</span>}
          {ob.summary && <span className="entry__summary">{ob.summary}</span>}
          {(ob.homeName || ob.funeralHome) && (
            <span className="entry__home">{ob.homeName || ob.funeralHome}</span>
          )}
        </span>
      </a>
    </li>
  );
}

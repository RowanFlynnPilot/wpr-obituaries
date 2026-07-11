import { lifespan, photoSrc } from "../lib/format.js";

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

export default function ObituaryRow({ ob }) {
  const span = lifespan(ob);
  const href = `${import.meta.env.BASE_URL}o/${ob.slug}.html`;

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
          {span && <span className="entry__span">{span}</span>}
          {ob.summary && <span className="entry__summary">{ob.summary}</span>}
          {(ob.homeName || ob.funeralHome) && (
            <span className="entry__home">{ob.homeName || ob.funeralHome}</span>
          )}
        </span>
      </a>
    </li>
  );
}

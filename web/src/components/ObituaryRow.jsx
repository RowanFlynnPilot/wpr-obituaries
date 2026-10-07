import { useId } from "react";
import { initials, lifespan, photoSrc } from "../lib/format.js";

// Age earns its place on the fact line only when the years don't already carry
// it — 93% of records have a full lifespan, where "age 81" restates "1944 –
// 2026". The bound rejects the handful of records that came through as age 0.
function ageFact(ob, span) {
  if (span.includes("–")) return null;
  return ob.age > 0 && ob.age <= 115 ? `age ${ob.age}` : null;
}

export default function ObituaryRow({ ob, match = null }) {
  const id = useId();
  const span = lifespan(ob);
  const href = `${import.meta.env.BASE_URL}o/${ob.slug}.html`;
  // The scannable facts on the typewriter line, so "is this my Frank?" is
  // answered without reading. There is no summary line: the extractor writes
  // one respectful sentence naming the person, their age and their town, and
  // every one of those facts is already above it — the name in title weight,
  // the town here, the date in the group heading. An echo is not information.
  // The full notice is one click away; the register's job is to get you there.
  const facts = [span, ageFact(ob, span), ob.town].filter(Boolean).join(" · ");
  const home = ob.homeName || ob.funeralHome;
  // The link's name is the person; the facts, the matched phrase and the home
  // describe it. Left to the browser, the name would be every line run
  // together, and a screen reader's list of sixty links could not be scanned
  // by name.
  const described = [facts && `${id}-facts`, match && `${id}-match`, home && `${id}-home`]
    .filter(Boolean)
    .join(" ");

  return (
    <li className="entry">
      <a
        className="entry__link"
        href={href}
        target="_top"
        aria-labelledby={`${id}-name`}
        aria-describedby={described || undefined}
      >
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
          <span className="entry__name" id={`${id}-name`}>
            {ob.name}
          </span>
          {facts && (
            <span className="entry__span" id={`${id}-facts`}>
              {facts}
            </span>
          )}
          {/* A row in the mentions tier is the exception: it shows the phrase
              that matched, because a row with no visible reason reads as a
              wrong answer on a memorial page. */}
          {match && (
            <span className="entry__match" id={`${id}-match`}>
              {match.before}
              <mark className="entry__mark">{match.hit}</mark>
              {match.after}
            </span>
          )}
          {home && (
            <span className="entry__home" id={`${id}-home`}>
              {home}
            </span>
          )}
        </span>
      </a>
    </li>
  );
}

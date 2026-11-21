import { useState } from "react";

const BASE = import.meta.env.BASE_URL;
const DAYS = 10; // how far ahead "upcoming" reaches
const FIRST = 6; // lines shown before "Show all"

const pad = (n) => String(n).padStart(2, "0");
const isoDay = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

function dayLabel(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

// The question most visitors arrive with is "when is the service?". Where a
// funeral home's feed states the next service date, the register lists it:
// today through the coming days, soonest first. The window is cut against the
// reader's own clock, so a date that has passed is gone even though the site
// is rebuilt only three times a week. Times and places stay in the notice.
export default function UpcomingServices({ obituaries }) {
  const [all, setAll] = useState(false);
  const today = new Date();
  const until = new Date(today);
  until.setDate(until.getDate() + DAYS);
  const from = isoDay(today);
  const to = isoDay(until);
  const upcoming = obituaries
    .filter((o) => o.serviceDate && o.serviceDate >= from && o.serviceDate <= to)
    .sort((a, b) => a.serviceDate.localeCompare(b.serviceDate) || a.name.localeCompare(b.name));
  if (upcoming.length === 0) return null;

  const shown = all ? upcoming : upcoming.slice(0, FIRST);
  const days = [];
  for (const ob of shown) {
    const last = days[days.length - 1];
    if (last && last.day === ob.serviceDate) last.people.push(ob);
    else days.push({ day: ob.serviceDate, people: [ob] });
  }

  return (
    <section className="services" aria-labelledby="services-title">
      <h2 className="services__kicker" id="services-title">
        Upcoming services
      </h2>
      <dl className="services__list">
        {days.map((g) => (
          <div className="services__day" key={g.day}>
            <dt className="services__date">{g.day === from ? "Today" : dayLabel(g.day)}</dt>
            {g.people.map((ob) => (
              <dd className="services__person" key={ob.slug}>
                <a className="services__link" href={`${BASE}o/${ob.slug}.html`} target="_top">
                  {ob.name}
                </a>
                {(ob.homeName || ob.funeralHome) && (
                  <span className="services__home">{ob.homeName || ob.funeralHome}</span>
                )}
              </dd>
            ))}
          </div>
        ))}
      </dl>
      {upcoming.length > FIRST && !all && (
        <button type="button" className="services__all" onClick={() => setAll(true)}>
          Show all {upcoming.length}
        </button>
      )}
      <p className="services__note">
        Dates as posted by the funeral homes. Times and places are in each notice.
      </p>
    </section>
  );
}

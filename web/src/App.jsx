import { useEffect, useMemo, useRef, useState } from "react";
import Masthead from "./components/Masthead.jsx";
import SubmitForm from "./components/SubmitForm.jsx";
import SearchBar from "./components/SearchBar.jsx";
import BrowseBar from "./components/BrowseBar.jsx";
import Register from "./components/Register.jsx";
import Footer from "./components/Footer.jsx";
import { eventDate, monthKey, monthLabel, lastNameInitial } from "./lib/format.js";
import { bySurname, searchObituaries } from "./lib/search.js";
import { readState, writeState } from "./lib/urlState.js";
import { reportStateToParent } from "./lib/frame.js";

const BASE = import.meta.env.BASE_URL;
const RECENT_MONTHS = 3; // default view: the current month plus the prior two
const RECENT = { kind: "recent", value: RECENT_MONTHS };
const NO_FILTER = { kind: "none" };
const EMPTY = { names: [], mentions: [], homes: [] };

// Newest date of death first (falling back to the publication date for the few
// records without one), so the register reads as a calendar of deaths.
function byEventDate(a, b) {
  const da = eventDate(a);
  const db = eventDate(b);
  return da < db ? 1 : da > db ? -1 : 0;
}

// The N most recent distinct months present, newest first.
function recentMonthKeys(obituaries, n) {
  const keys = [];
  for (const o of obituaries) {
    const k = monthKey(eventDate(o));
    if (!keys.includes(k)) {
      keys.push(k);
      if (keys.length >= n) break;
    }
  }
  return keys;
}

// What the count line says the number is *of* — always, not only by default,
// so "36 names" never floats free of the filter that produced it.
function scopeLabel(filter) {
  switch (filter.kind) {
    case "recent":
      return `the last ${filter.value} months`;
    case "month":
      return monthLabel(filter.value);
    case "letter":
      return `last names beginning with ${filter.value}`;
    case "town":
    case "home":
      return filter.value;
    default:
      return "every year";
  }
}

// Focus after a state change that unmounts the control the reader just used —
// run on the next task, once React has committed the new DOM.
function focusSoon(find) {
  setTimeout(() => find()?.focus(), 0);
}

export default function App() {
  // A shared or bookmarked URL (?q=, ?month=, ?letter=, ?town=, ?home=) reopens
  // the same list; otherwise the register opens on the recent months.
  const [seeded] = useState(() => readState());
  const [data, setData] = useState(null);
  const [sponsor, setSponsor] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const [query, setQuery] = useState(seeded?.query ?? "");
  const [filter, setFilter] = useState(seeded?.filter ?? NO_FILTER);
  const [browseOpen, setBrowseOpen] = useState(false);
  const [submitOpen, setSubmitOpen] = useState(false);
  const browseRef = useRef(null);
  const submitRef = useRef(null);

  useEffect(() => {
    let live = true;
    Promise.all([
      fetch(`${BASE}data/obituaries.json`).then(ok),
      fetch(`${BASE}data/sponsor.json`).then(ok),
    ])
      .then(([index, sponsorConfig]) => {
        if (!live) return;
        // One sort, once: everything downstream reads newest death first.
        setData({ ...index, obituaries: [...index.obituaries].sort(byEventDate) });
        setSponsor(sponsorConfig);
        // Default the register to the most recent few months so the embed opens
        // at a readable height instead of listing the whole catalogue.
        if (index.obituaries.length && !seeded) setFilter(RECENT);
      })
      .catch((e) => {
        if (!live) return;
        console.error("Obituary index failed to load:", e);
        setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [seeded, attempt]);

  // Mirror the state into the URL (and to the embedding page) once the data is
  // in, so Back from a person page lands here, not on an empty default.
  useEffect(() => {
    if (data) reportStateToParent(writeState(query, filter));
  }, [data, query, filter]);

  // Search and browse are independent narrowings; activating one clears the other.
  // Clearing the search returns to the default view — carousel and all.
  const onSearch = (v) => {
    setQuery(v);
    setFilter(v ? NO_FILTER : RECENT);
  };
  const onFilter = (f) => {
    setFilter(f);
    setQuery("");
  };
  // Clearing from the empty state unmounts the button that was clicked, so
  // hand focus back to the field the reader will type in next.
  const clearSearch = () => {
    onSearch("");
    focusSoon(() => document.getElementById("obit-search"));
  };
  const openBrowse = () => {
    setBrowseOpen(true);
    onFilter(RECENT);
    // Focus the first letter: it both reveals the panel and lands the reader
    // on the control they asked for.
    focusSoon(() => browseRef.current?.querySelector(".browse__letter"));
  };
  const openSubmit = () => {
    setSubmitOpen(true);
    focusSoon(() => submitRef.current?.querySelector("input, textarea"));
  };

  const results = useMemo(() => {
    if (!data) return EMPTY;
    if (query.trim()) return searchObituaries(data.obituaries, query);
    const all = data.obituaries;
    const of = (names) => ({ ...EMPTY, names });
    if (filter.kind === "recent") {
      const set = new Set(recentMonthKeys(all, filter.value));
      return of(all.filter((o) => set.has(monthKey(eventDate(o)))));
    }
    if (filter.kind === "month") {
      return of(all.filter((o) => monthKey(eventDate(o)) === filter.value));
    }
    if (filter.kind === "letter") {
      // A letter browse reads like an index: alphabetical by surname.
      return of(all.filter((o) => lastNameInitial(o.name) === filter.value).sort(bySurname));
    }
    if (filter.kind === "town") {
      return of(all.filter((o) => o.town === filter.value));
    }
    if (filter.kind === "home") {
      return of(all.filter((o) => (o.homeName || o.funeralHome) === filter.value));
    }
    return of(all);
  }, [data, query, filter]);

  if (error) {
    return (
      <main className="page">
        <Masthead sponsor={sponsor} />
        <div className="page__error" role="alert">
          <p className="page__error-text">
            Obituaries are unavailable right now. This is usually temporary.
          </p>
          <button
            type="button"
            className="register__action"
            onClick={() => {
              setError(null);
              setAttempt((n) => n + 1);
            }}
          >
            Try again
          </button>
        </div>
        <Footer sponsor={sponsor} />
      </main>
    );
  }

  return (
    <main className="page">
      <Masthead
        sponsor={sponsor}
        search={
          data ? (
            <SearchBar
              value={query}
              onChange={onSearch}
              count={results.names.length}
              mentions={results.mentions.length}
              scope={query ? "" : scopeLabel(filter)}
            />
          ) : null
        }
      />
      {data ? (
        <>
          {!query && (
            <BrowseBar
              ref={browseRef}
              obituaries={data.obituaries}
              filter={filter}
              onFilter={onFilter}
              open={browseOpen}
              onOpenChange={setBrowseOpen}
              recentMonths={RECENT_MONTHS}
            />
          )}
          <Register
            key={`${query}|${filter.kind}|${filter.value ?? ""}`}
            obituaries={results.names}
            mentions={results.mentions}
            homes={results.homes}
            query={query}
            letter={filter.kind === "letter" ? filter.value : null}
            onClear={clearSearch}
            onBrowseLetters={openBrowse}
            onSubmit={openSubmit}
            onHome={(name) => onFilter({ kind: "home", value: name })}
          />
        </>
      ) : (
        <LoadingSkeleton />
      )}
      <Footer sponsor={sponsor}>
        <SubmitForm ref={submitRef} open={submitOpen} onOpenChange={setSubmitOpen} />
      </Footer>
    </main>
  );
}

function LoadingSkeleton() {
  return (
    <>
      <p className="sr-only" role="status">
        Loading obituaries…
      </p>
      <SkeletonRows />
    </>
  );
}

function SkeletonRows() {
  return (
    <div className="skeleton" aria-hidden="true">
      {Array.from({ length: 6 }).map((_, i) => (
        <div className="skeleton__row" key={i}>
          <div className="skeleton__photo" />
          <div className="skeleton__text">
            <div className="skeleton__line skeleton__line--name" />
            <div className="skeleton__line skeleton__line--meta" />
            <div className="skeleton__line skeleton__line--summary" />
          </div>
        </div>
      ))}
    </div>
  );
}

function ok(response) {
  if (!response.ok) {
    throw new Error(`${response.url} returned ${response.status}`);
  }
  return response.json();
}

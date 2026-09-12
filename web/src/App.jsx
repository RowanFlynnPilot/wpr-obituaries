import { useEffect, useMemo, useRef, useState } from "react";
import Masthead from "./components/Masthead.jsx";
import SubmitForm from "./components/SubmitForm.jsx";
import FeaturedCarousel from "./components/FeaturedCarousel.jsx";
import SearchBar from "./components/SearchBar.jsx";
import BrowseBar from "./components/BrowseBar.jsx";
import Register from "./components/Register.jsx";
import Footer from "./components/Footer.jsx";
import { eventDate, monthKey, lastNameInitial } from "./lib/format.js";
import { bySurname, searchObituaries } from "./lib/search.js";

const BASE = import.meta.env.BASE_URL;
const RECENT_MONTHS = 3; // default view: the current month plus the prior two
const RECENT = { kind: "recent", value: RECENT_MONTHS };
const NO_FILTER = { kind: "none" };

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

export default function App() {
  const [data, setData] = useState(null);
  const [sponsor, setSponsor] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState(NO_FILTER);
  const [browseOpen, setBrowseOpen] = useState(false);
  const [submitOpen, setSubmitOpen] = useState(false);
  const browseRef = useRef(null);
  const submitRef = useRef(null);

  useEffect(() => {
    Promise.all([
      fetch(`${BASE}data/obituaries.json`).then(ok),
      fetch(`${BASE}data/sponsor.json`).then(ok),
    ])
      .then(([index, sponsorConfig]) => {
        // One sort, once: everything downstream reads newest death first.
        setData({ ...index, obituaries: [...index.obituaries].sort(byEventDate) });
        setSponsor(sponsorConfig);
        // Default the register to the most recent few months so the embed opens
        // at a readable height instead of listing the whole catalogue.
        if (index.obituaries.length) setFilter(RECENT);
      })
      .catch((e) => {
        console.error("Obituary index failed to load:", e);
        setError(e.message);
      });
  }, []);

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
  const openBrowse = () => {
    setBrowseOpen(true);
    onFilter(RECENT);
    requestAnimationFrame(() => browseRef.current?.scrollIntoView({ block: "start" }));
  };
  const openSubmit = () => {
    setSubmitOpen(true);
    requestAnimationFrame(() => submitRef.current?.scrollIntoView({ block: "start" }));
  };

  const results = useMemo(() => {
    if (!data) return { names: [], mentions: [] };
    if (query.trim()) return searchObituaries(data.obituaries, query);
    const all = data.obituaries;
    if (filter.kind === "recent") {
      const set = new Set(recentMonthKeys(all, filter.value));
      return { names: all.filter((o) => set.has(monthKey(eventDate(o)))), mentions: [] };
    }
    if (filter.kind === "month") {
      return { names: all.filter((o) => monthKey(eventDate(o)) === filter.value), mentions: [] };
    }
    if (filter.kind === "letter") {
      // A letter browse reads like an index: alphabetical by surname.
      const hits = all.filter((o) => lastNameInitial(o.name) === filter.value);
      return { names: hits.sort(bySurname), mentions: [] };
    }
    if (filter.kind === "town") {
      return { names: all.filter((o) => o.town === filter.value), mentions: [] };
    }
    if (filter.kind === "home") {
      return { names: all.filter((o) => o.homeName === filter.value), mentions: [] };
    }
    return { names: all, mentions: [] };
  }, [data, query, filter]);

  if (error) {
    return (
      <main className="page">
        <Masthead sponsor={sponsor} />
        <p className="page__error" role="alert">
          Obituaries are unavailable right now. Please check back in a little while.
        </p>
      </main>
    );
  }

  const isDefault = !query && filter.kind === "recent" && !browseOpen;
  const scope =
    !query && filter.kind === "recent" ? `the last ${filter.value} months` : "";

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
              scope={scope}
            />
          ) : null
        }
      />
      {data ? (
        <>
          {isDefault && <FeaturedCarousel obituaries={data.obituaries} />}
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
            query={query}
            letter={filter.kind === "letter" ? filter.value : null}
            onClear={() => onSearch("")}
            onBrowseLetters={openBrowse}
            onSubmit={openSubmit}
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

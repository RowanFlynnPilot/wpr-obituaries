import { useEffect, useMemo, useState } from "react";
import Masthead from "./components/Masthead.jsx";
import SubmitForm from "./components/SubmitForm.jsx";
import FeaturedCarousel from "./components/FeaturedCarousel.jsx";
import SearchBar from "./components/SearchBar.jsx";
import BrowseBar from "./components/BrowseBar.jsx";
import Register from "./components/Register.jsx";
import Footer from "./components/Footer.jsx";
import { monthKey, lastNameInitial } from "./lib/format.js";

const BASE = import.meta.env.BASE_URL;
const NO_FILTER = { kind: "none" };
const RECENT_MONTHS = 3; // default view: the current month plus the prior two

// The N most recent distinct months present, newest first (the index is sorted
// newest-first, so distinct months appear in descending order).
function recentMonthKeys(obituaries, n) {
  const keys = [];
  for (const o of obituaries) {
    const k = monthKey(o.sourceDate);
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
  // Has the reader touched search/browse yet? Until they do, we show the
  // featured carousel even though the register defaults to the latest month.
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${BASE}data/obituaries.json`).then(ok),
      fetch(`${BASE}data/sponsor.json`).then(ok),
    ])
      .then(([index, sponsorConfig]) => {
        setData(index);
        setSponsor(sponsorConfig);
        // Default the register to the most recent few months so the embed opens
        // at a readable height instead of listing the whole catalogue, while still
        // showing more than a sparse just-started month.
        if (index.obituaries.length) setFilter({ kind: "recent", value: RECENT_MONTHS });
      })
      .catch((e) => {
        console.error("Obituary index failed to load:", e);
        setError(e.message);
      });
  }, []);

  // Search and browse are independent narrowings; activating one clears the other.
  const onSearch = (v) => {
    setTouched(true);
    setQuery(v);
    // A query supersedes the browse filter; clearing it returns to the default
    // recent view instead of dumping the reader into the whole catalogue.
    setFilter(v ? NO_FILTER : { kind: "recent", value: RECENT_MONTHS });
  };
  const onFilter = (f) => {
    setTouched(true);
    setFilter(f);
    setQuery("");
  };

  const displayed = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    if (q) {
      // Match across name, funeral home, and the summary/excerpt — the latter
      // carries the town ("of Wausau") and other searchable detail.
      return data.obituaries.filter((ob) =>
        [ob.name, ob.funeralHome, ob.summary, ob.excerpt]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(q)
      );
    }
    if (filter.kind === "recent") {
      const set = new Set(recentMonthKeys(data.obituaries, filter.value));
      return data.obituaries.filter((o) => set.has(monthKey(o.sourceDate)));
    }
    if (filter.kind === "month") {
      return data.obituaries.filter((o) => monthKey(o.sourceDate) === filter.value);
    }
    if (filter.kind === "letter") {
      return data.obituaries.filter((o) => lastNameInitial(o.name) === filter.value);
    }
    if (filter.kind === "town") {
      return data.obituaries.filter((o) => o.town === filter.value);
    }
    if (filter.kind === "home") {
      return data.obituaries.filter((o) => o.homeName === filter.value);
    }
    return data.obituaries;
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

  const isDefault = !query && !touched;

  return (
    <main className="page">
      <Masthead sponsor={sponsor} />
      <SubmitForm />
      {data ? (
        <>
          {isDefault && <FeaturedCarousel obituaries={data.obituaries} />}
          <SearchBar value={query} onChange={onSearch} count={displayed.length} />
          {!query && (
            <BrowseBar
              obituaries={data.obituaries}
              filter={filter}
              onFilter={onFilter}
              recentMonths={RECENT_MONTHS}
            />
          )}
          <Register obituaries={displayed} query={query} />
        </>
      ) : (
        <LoadingSkeleton />
      )}
      <Footer sponsor={sponsor} />
    </main>
  );
}

function LoadingSkeleton() {
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

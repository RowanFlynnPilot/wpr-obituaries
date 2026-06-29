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

export default function App() {
  const [data, setData] = useState(null);
  const [sponsor, setSponsor] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState(NO_FILTER);

  useEffect(() => {
    Promise.all([
      fetch(`${BASE}data/obituaries.json`).then(ok),
      fetch(`${BASE}data/sponsor.json`).then(ok),
    ])
      .then(([index, sponsorConfig]) => {
        setData(index);
        setSponsor(sponsorConfig);
      })
      .catch((e) => setError(e.message));
  }, []);

  // Search and browse are independent narrowings; activating one clears the other.
  const onSearch = (v) => {
    setQuery(v);
    if (v) setFilter(NO_FILTER);
  };
  const onFilter = (f) => {
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
        <p className="page__error">
          The obituary index could not be loaded. {error}
        </p>
      </main>
    );
  }

  const isDefault = !query && filter.kind === "none";

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

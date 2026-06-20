import { useEffect, useMemo, useState } from "react";
import Masthead from "./components/Masthead.jsx";
import FeaturedCarousel from "./components/FeaturedCarousel.jsx";
import SearchBar from "./components/SearchBar.jsx";
import Register from "./components/Register.jsx";
import Footer from "./components/Footer.jsx";

const BASE = import.meta.env.BASE_URL;

export default function App() {
  const [data, setData] = useState(null);
  const [sponsor, setSponsor] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");

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

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    if (!q) return data.obituaries;
    return data.obituaries.filter(
      (ob) =>
        ob.name.toLowerCase().includes(q) ||
        (ob.funeralHome || "").toLowerCase().includes(q)
    );
  }, [data, query]);

  if (error) {
    return (
      <main className="page">
        <p className="page__error">
          The obituary index could not be loaded. {error}
        </p>
      </main>
    );
  }

  return (
    <main className="page">
      <Masthead sponsor={sponsor} />
      {data ? (
        <>
          {!query && <FeaturedCarousel obituaries={data.obituaries} />}
          <SearchBar value={query} onChange={setQuery} count={filtered.length} />
          <Register obituaries={filtered} query={query} />
        </>
      ) : (
        <p className="page__loading">Loading…</p>
      )}
      <Footer sponsor={sponsor} />
    </main>
  );
}

function ok(response) {
  if (!response.ok) {
    throw new Error(`${response.url} returned ${response.status}`);
  }
  return response.json();
}

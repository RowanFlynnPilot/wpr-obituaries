export default function SearchBar({ value, onChange, count }) {
  return (
    <div className="search">
      <label className="search__label" htmlFor="obit-search">
        Find a name
      </label>
      <input
        id="obit-search"
        className="search__input"
        type="search"
        placeholder="Search by name, town, or funeral home"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete="off"
      />
      <p className="search__count" role="status" aria-live="polite" aria-atomic="true">
        {count} {count === 1 ? "name" : "names"}
      </p>
    </div>
  );
}

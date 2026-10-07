import { useEffect, useState } from "react";

// A value that only changes once it has held still for `ms` — so a reader who
// types "jensen" hears one count, not six.
function useSettled(value, ms) {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setSettled(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return settled;
}

// The name search is the product (PRODUCT.md, principle 1): it sits directly
// under the lede, reads at body size, and has a boundary a low-vision reader
// can see. Nothing above it but the newsroom's flag and the title; nothing
// between it and its results.
export default function SearchBar({ value, onChange, count, mentions = 0, scope = "" }) {
  const names = `${count} ${count === 1 ? "name" : "names"}`;
  const extra = mentions ? ` · ${mentions} more mention${mentions === 1 ? "" : "s"}` : "";
  const scoped = scope ? ` · ${scope}` : "";
  const line = `${names}${extra}${scoped}`;
  // Sighted readers watch the count change as they type. Screen-reader users
  // get the same text from a stable status region once typing pauses; the
  // visible line is hidden from them so it is not read twice.
  const announced = useSettled(line, 700);
  // Results are live as you type, so Enter's one job is to dismiss the phone
  // keyboard and show the list — what enterKeyHint="search" promises.
  const onKeyDown = (e) => {
    if (e.key === "Enter") e.currentTarget.blur();
  };
  return (
    <div className="search">
      <label className="search__label" htmlFor="obit-search">
        Find a name
      </label>
      <div className="search__field">
        <svg
          className="search__glyph"
          viewBox="0 0 20 20"
          width="20"
          height="20"
          aria-hidden="true"
          focusable="false"
        >
          <circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
          <path d="M12.8 12.8 17 17" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
        <input
          id="obit-search"
          className="search__input"
          type="search"
          placeholder="Name, town or funeral home"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          autoComplete="off"
          autoCapitalize="words"
          enterKeyHint="search"
        />
      </div>
      <p className="search__count" aria-hidden="true">
        {line}
      </p>
      {/* role="status" is a polite, atomic live region. It is rendered from the
          start with the initial count, so only a change is announced. */}
      <p className="sr-only" role="status">
        {announced}
      </p>
    </div>
  );
}

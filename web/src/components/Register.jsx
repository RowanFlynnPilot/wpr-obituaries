import ObituaryRow from "./ObituaryRow.jsx";

export default function Register({ obituaries, query }) {
  if (obituaries.length === 0) {
    return (
      <p className="register__empty">
        No obituaries match “{query}”. Try a last name, or browse the full
        list by clearing the search.
      </p>
    );
  }

  return (
    <ol className="register">
      {obituaries.map((ob) => (
        <ObituaryRow key={ob.slug} ob={ob} />
      ))}
    </ol>
  );
}

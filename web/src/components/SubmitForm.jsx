import { useState } from "react";
import config from "../config.js";

const { identity } = config;

// The lightweight, no-infrastructure submit path: collect structured fields and
// hand the family a prefilled email to the newsroom (matching the existing
// "email obituaries to…" workflow). An editor turns the email into an approved
// data/intake/<id>.json. Step 5 swaps this for a Supabase POST — same form.
const FIELDS = [
  { name: "name", label: "Full name", required: true },
  { name: "source_date", label: "Date of publication", type: "date", required: true },
  { name: "birth_date", label: "Date of birth", type: "date" },
  { name: "death_date", label: "Date of death", type: "date" },
  { name: "age", label: "Age", type: "number" },
  { name: "funeral_home", label: "Funeral home" },
];

export default function SubmitForm() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({});
  const [body, setBody] = useState("");

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    const lines = FIELDS.filter((f) => form[f.name]).map(
      (f) => `${f.label}: ${form[f.name]}`
    );
    const emailBody =
      lines.join("\n") +
      "\n\nObituary text:\n" +
      (body.trim() || "(none provided)") +
      "\n\nIf you have a photo, please attach it to this email.";
    window.location.href =
      `mailto:${identity.submissionsEmail}` +
      `?subject=${encodeURIComponent("Obituary submission: " + (form.name || ""))}` +
      `&body=${encodeURIComponent(emailBody)}`;
  };

  if (!open) {
    return (
      <div className="submit">
        <button
          className="submit__open"
          type="button"
          onClick={() => setOpen(true)}
        >
          Submit an obituary
        </button>
      </div>
    );
  }

  return (
    <form className="submit submit--open" onSubmit={submit}>
      <p className="submit__intro">
        Fill in what you can. Your email program opens with a message ready to
        send to our newsroom — attach a photo there if you have one.
      </p>
      <div className="submit__grid">
        {FIELDS.map((f) => (
          <label className="submit__field" key={f.name}>
            <span className="submit__label">
              {f.label}
              {f.required ? " *" : ""}
            </span>
            <input
              className="submit__input"
              type={f.type || "text"}
              required={f.required}
              value={form[f.name] || ""}
              onChange={set(f.name)}
            />
          </label>
        ))}
      </div>
      <label className="submit__field">
        <span className="submit__label">Obituary text</span>
        <textarea
          className="submit__input submit__textarea"
          rows="6"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
      </label>
      <div className="submit__actions">
        <button className="submit__send" type="submit">
          Open email to send
        </button>
        <button
          className="submit__cancel"
          type="button"
          onClick={() => setOpen(false)}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

import { useEffect, useRef, useState } from "react";
import config from "../config.js";

const { identity } = config;

// The lightweight, no-infrastructure submit path: collect structured fields and
// hand the family a prefilled email to the newsroom (matching the existing
// "email obituaries to…" workflow). An editor turns the email into an approved
// data/intake/<id>.json. Step 5 swaps this for a Supabase POST — same form.
const FIELDS = [
  { name: "name", label: "Full name", required: true },
  // Publication date is a newsroom concept a family can't know — the editor
  // sets it during intake review, so it's optional here.
  { name: "source_date", label: "Date of publication (if known)", type: "date" },
  { name: "birth_date", label: "Date of birth", type: "date" },
  { name: "death_date", label: "Date of death", type: "date" },
  { name: "age", label: "Age", type: "number" },
  { name: "funeral_home", label: "Funeral home" },
];

export default function SubmitForm() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({});
  const [body, setBody] = useState("");
  const formRef = useRef(null);
  const openBtnRef = useRef(null);
  const wasOpen = useRef(false);

  // Keyboard/screen-reader flow: opening moves focus into the form, closing
  // returns it to the trigger (never on initial mount — the embed must not
  // steal focus from the page hosting it).
  useEffect(() => {
    if (open) {
      formRef.current?.querySelector("input")?.focus();
      wasOpen.current = true;
    } else if (wasOpen.current) {
      openBtnRef.current?.focus();
      wasOpen.current = false;
    }
  }, [open]);

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
          ref={openBtnRef}
          onClick={() => setOpen(true)}
        >
          Submit an obituary
        </button>
      </div>
    );
  }

  return (
    <form
      className="submit submit--open"
      ref={formRef}
      onSubmit={submit}
      onKeyDown={(e) => {
        if (e.key === "Escape") setOpen(false);
      }}
    >
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
      {body.length > 1500 && (
        <p className="submit__intro" role="status">
          Some email programs cut off long prefilled messages. If the email that
          opens looks incomplete, paste the obituary text into it yourself.
        </p>
      )}
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

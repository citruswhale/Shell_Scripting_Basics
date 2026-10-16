import { useState } from "react";
import { api } from "../api.js";
import Field from "./Field.jsx";
import Modal from "./Modal.jsx";

function isoDate(daysFromToday) {
  const d = new Date();
  d.setDate(d.getDate() + daysFromToday);
  // Local date in YYYY-MM-DD, without timezone shifting
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

export default function LendForm({ item, onClose, onSaved }) {
  const [form, setForm] = useState({ borrower_name: "", borrower_email: "", due_date: isoDate(7) });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setErrors({});
    setMessage("");
    try {
      await api.createLoan({ ...form, item_id: item.id });
      onSaved();
    } catch (err) {
      setErrors(err.fieldErrors || {});
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={`Lend “${item.name}”`} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        {message && <div className="banner error">{message}</div>}
        <Field label="Borrower name" error={errors.borrower_name}>
          <input value={form.borrower_name} onChange={set("borrower_name")} autoFocus />
        </Field>
        <Field label="Borrower email" error={errors.borrower_email}>
          <input type="email" value={form.borrower_email} onChange={set("borrower_email")} />
        </Field>
        <Field label="Due date" error={errors.due_date} hint="Up to 30 days from today">
          <input
            type="date"
            value={form.due_date}
            min={isoDate(0)}
            max={isoDate(30)}
            onChange={set("due_date")}
          />
        </Field>
        <div className="actions">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn primary" disabled={saving}>
            {saving ? "Saving…" : "Lend item"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

import { useState } from "react";
import { api, CATEGORIES, CONDITIONS, label } from "../api.js";
import Field from "./Field.jsx";
import Modal from "./Modal.jsx";

// Add or edit an item. Validation messages come straight from the API.
export default function ItemForm({ item, onClose, onSaved }) {
  const editing = Boolean(item);
  const [form, setForm] = useState({
    name: item?.name ?? "",
    category: item?.category ?? "camera",
    serial_number: item?.serial_number ?? "",
    condition: item?.condition ?? "good",
    status: item?.status ?? "available",
    notes: item?.notes ?? "",
  });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setErrors({});
    setMessage("");
    const body = { ...form };
    // An item on loan keeps its status; it changes when the loan is returned.
    if (form.status === "on_loan") delete body.status;
    try {
      const saved = editing ? await api.updateItem(item.id, body) : await api.createItem(body);
      onSaved(saved);
    } catch (err) {
      setErrors(err.fieldErrors || {});
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={editing ? "Edit item" : "Add item"} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        {message && <div className="banner error">{message}</div>}
        <Field label="Name" error={errors.name}>
          <input value={form.name} onChange={set("name")} maxLength={100} autoFocus required />
        </Field>
        <div className="row">
          <Field label="Category" error={errors.category}>
            <select value={form.category} onChange={set("category")}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{label(c)}</option>
              ))}
            </select>
          </Field>
          <Field label="Condition" error={errors.condition}>
            <select value={form.condition} onChange={set("condition")}>
              {CONDITIONS.map((c) => (
                <option key={c} value={c}>{label(c)}</option>
              ))}
            </select>
          </Field>
        </div>
        <div className="row">
          <Field label="Serial number" error={errors.serial_number} hint="Optional, must be unique">
            <input value={form.serial_number} onChange={set("serial_number")} maxLength={64} />
          </Field>
          <Field label="Status" error={errors.status}>
            {form.status === "on_loan" ? (
              <input value="on loan" disabled />
            ) : (
              <select value={form.status} onChange={set("status")}>
                <option value="available">available</option>
                <option value="maintenance">maintenance</option>
              </select>
            )}
          </Field>
        </div>
        <Field label="Notes" error={errors.notes}>
          <textarea rows={3} value={form.notes} onChange={set("notes")} maxLength={1000} />
        </Field>
        <div className="actions">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn primary" disabled={saving}>
            {saving ? "Saving…" : editing ? "Save changes" : "Add item"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

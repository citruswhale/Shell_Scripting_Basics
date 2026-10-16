import { useState } from "react";
import { api, CONDITIONS, label } from "../api.js";
import Modal from "./Modal.jsx";

export default function ReturnDialog({ loan, onClose, onSaved }) {
  const [condition, setCondition] = useState("good");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.returnLoan(loan.id, condition);
      onSaved();
    } catch (err) {
      setMessage(err.message);
      setSaving(false);
    }
  }

  return (
    <Modal title="Return item" onClose={onClose}>
      <form onSubmit={submit}>
        {message && <div className="banner error">{message}</div>}
        <p className="muted">
          <strong>{loan.item_name}</strong> borrowed by {loan.borrower_name}
        </p>
        <fieldset className="choices">
          <legend>Condition on return</legend>
          {CONDITIONS.map((c) => (
            <label key={c} className={condition === c ? "choice selected" : "choice"}>
              <input
                type="radio"
                name="condition"
                value={c}
                checked={condition === c}
                onChange={() => setCondition(c)}
              />
              {label(c)}
            </label>
          ))}
        </fieldset>
        {condition === "damaged" && (
          <div className="banner warn">Damaged items go to maintenance and can't be lent until fixed.</div>
        )}
        <div className="actions">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn primary" disabled={saving}>
            {saving ? "Saving…" : "Confirm return"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

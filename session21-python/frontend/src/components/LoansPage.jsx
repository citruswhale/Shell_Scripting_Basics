import { useEffect, useState } from "react";
import { api } from "../api.js";
import Badge from "./Badge.jsx";
import ReturnDialog from "./ReturnDialog.jsx";

const FILTERS = [
  { value: "", label: "All" },
  { value: "active", label: "Active" },
  { value: "overdue", label: "Overdue" },
  { value: "returned", label: "Returned" },
];

const fmtDate = (value) =>
  value ? new Date(value).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "—";

export default function LoansPage({ version, onChange }) {
  const [status, setStatus] = useState("");
  const [email, setEmail] = useState("");
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [returning, setReturning] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const t = setTimeout(() => {
      api
        .listLoans({ status, borrower_email: email.trim() })
        .then((data) => !cancelled && (setLoans(data), setError("")))
        .catch((err) => !cancelled && setError(err.message))
        .finally(() => !cancelled && setLoading(false));
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [status, email, version]);

  async function remove(loan) {
    if (!window.confirm("Remove this returned loan from the history?")) return;
    try {
      await api.deleteLoan(loan.id);
      onChange();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <div className="toolbar">
        <div className="segmented" role="group" aria-label="Filter loans">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              className={status === f.value ? "seg active" : "seg"}
              onClick={() => setStatus(f.value)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <input
          className="search"
          type="search"
          placeholder="Borrower email…"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-label="Filter by borrower email"
        />
      </div>

      {error && <div className="banner error">{error}</div>}

      {loading && loans.length === 0 ? (
        <div className="empty">Loading loans…</div>
      ) : loans.length === 0 ? (
        <div className="empty">No loans to show. Lend an item from the Equipment tab.</div>
      ) : (
        <div className={loading ? "table-wrap loading" : "table-wrap"}>
          <table className="table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Borrower</th>
                <th>Loaned</th>
                <th>Due</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {loans.map((loan) => (
                <tr key={loan.id} className={loan.status === "overdue" ? "overdue-row" : ""}>
                  <td data-label="Item"><strong>{loan.item_name}</strong></td>
                  <td data-label="Borrower">
                    <div>
                      {loan.borrower_name}
                      <div className="muted small">{loan.borrower_email}</div>
                    </div>
                  </td>
                  <td data-label="Loaned">{fmtDate(loan.loaned_at)}</td>
                  <td data-label="Due">{fmtDate(loan.due_date + "T00:00:00")}</td>
                  <td data-label="Status">
                    <div>
                      <Badge value={loan.status} />
                      {loan.returned_at && (
                        <div className="muted small">
                          {fmtDate(loan.returned_at)} · {loan.return_condition}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="row-actions">
                    {loan.status === "returned" ? (
                      <button className="btn small ghost" onClick={() => remove(loan)}>Remove</button>
                    ) : (
                      <button className="btn small primary" onClick={() => setReturning(loan)}>Return</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {returning && (
        <ReturnDialog
          loan={returning}
          onClose={() => setReturning(null)}
          onSaved={() => {
            setReturning(null);
            onChange();
          }}
        />
      )}
    </section>
  );
}

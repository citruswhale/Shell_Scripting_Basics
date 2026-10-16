import { useEffect, useState } from "react";
import { api, CATEGORIES, ITEM_STATUSES, label } from "../api.js";
import Badge from "./Badge.jsx";
import ItemForm from "./ItemForm.jsx";
import LendForm from "./LendForm.jsx";

export default function ItemsPage({ version, onChange }) {
  const [filters, setFilters] = useState({ search: "", category: "", status: "" });
  const [search, setSearch] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null); // null, "new" or an item
  const [lending, setLending] = useState(null);

  // Wait a moment after typing before searching, so we don't call the API on every key.
  useEffect(() => {
    const t = setTimeout(() => setFilters((f) => ({ ...f, search })), 300);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .listItems(filters)
      .then((data) => !cancelled && (setItems(data), setError("")))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [filters, version]);

  async function remove(item) {
    if (!window.confirm(`Delete "${item.name}"? This cannot be undone.`)) return;
    try {
      await api.deleteItem(item.id);
      onChange();
    } catch (err) {
      setError(err.message);
    }
  }

  const filtered = filters.search || filters.category || filters.status;

  return (
    <section>
      <div className="toolbar">
        <input
          className="search"
          type="search"
          placeholder="Search name, serial or notes…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search items"
        />
        <select
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          aria-label="Filter by category"
        >
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{label(c)}</option>
          ))}
        </select>
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          {ITEM_STATUSES.map((s) => (
            <option key={s} value={s}>{label(s)}</option>
          ))}
        </select>
        <button className="btn primary" onClick={() => setEditing("new")}>+ Add item</button>
      </div>

      {error && <div className="banner error">{error}</div>}

      {loading && items.length === 0 ? (
        <div className="empty">Loading equipment…</div>
      ) : items.length === 0 ? (
        <div className="empty">
          {filtered ? "No items match these filters." : "No equipment yet. Add the first item to get started."}
        </div>
      ) : (
        <div className={loading ? "table-wrap loading" : "table-wrap"}>
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Serial</th>
                <th>Condition</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td data-label="Name">
                    <div>
                      <strong>{item.name}</strong>
                      {item.notes && <div className="muted small">{item.notes}</div>}
                    </div>
                  </td>
                  <td data-label="Category">{label(item.category)}</td>
                  <td data-label="Serial" className="mono">{item.serial_number || "—"}</td>
                  <td data-label="Condition"><Badge value={item.condition} /></td>
                  <td data-label="Status"><Badge value={item.status} /></td>
                  <td className="row-actions">
                    {item.status === "available" && (
                      <button className="btn small primary" onClick={() => setLending(item)}>Lend</button>
                    )}
                    <button className="btn small ghost" onClick={() => setEditing(item)}>Edit</button>
                    <button className="btn small danger" onClick={() => remove(item)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <ItemForm
          item={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            onChange();
          }}
        />
      )}
      {lending && (
        <LendForm
          item={lending}
          onClose={() => setLending(null)}
          onSaved={() => {
            setLending(null);
            onChange();
          }}
        />
      )}
    </section>
  );
}

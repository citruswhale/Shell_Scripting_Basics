// Small wrapper around fetch. All calls go to the relative /api path, which
// nginx (docker compose) or the ingress (k8s) sends to the backend.
const BASE = "/api";

export class ApiError extends Error {
  constructor(message, status, fieldErrors = {}) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

// FastAPI sends either {"detail": "text"} or, for 422, a list of field errors.
function parseError(status, body) {
  const detail = body && body.detail;
  if (Array.isArray(detail)) {
    const fieldErrors = {};
    for (const err of detail) {
      const field = err.loc ? err.loc[err.loc.length - 1] : "form";
      fieldErrors[field] = err.msg.replace(/^Value error, /, "");
    }
    return new ApiError("Please fix the highlighted fields.", status, fieldErrors);
  }
  if (typeof detail === "string") return new ApiError(detail, status);
  return new ApiError(`Request failed (${status})`, status);
}

async function request(path, { method = "GET", body, params } = {}) {
  let url = BASE + path;
  if (params) {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== "" && v != null)
    ).toString();
    if (query) url += `?${query}`;
  }

  let resp;
  try {
    resp = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Is the backend running?", 0);
  }

  if (resp.status === 204) return null;
  const data = await resp.json().catch(() => null);
  if (!resp.ok) throw parseError(resp.status, data);
  return data;
}

export const api = {
  info: () => request("/info"),
  stats: () => request("/stats"),
  listItems: (params) => request("/items", { params }),
  createItem: (item) => request("/items", { method: "POST", body: item }),
  updateItem: (id, item) => request(`/items/${id}`, { method: "PUT", body: item }),
  deleteItem: (id) => request(`/items/${id}`, { method: "DELETE" }),
  listLoans: (params) => request("/loans", { params }),
  createLoan: (loan) => request("/loans", { method: "POST", body: loan }),
  returnLoan: (id, condition) =>
    request(`/loans/${id}/return`, { method: "POST", body: { condition } }),
  deleteLoan: (id) => request(`/loans/${id}`, { method: "DELETE" }),
};

export const CATEGORIES = ["camera", "laptop", "audio", "lighting", "tripod", "other"];
export const CONDITIONS = ["good", "fair", "damaged"];
export const ITEM_STATUSES = ["available", "on_loan", "maintenance"];

export const label = (value) => (value ? value.replace("_", " ") : "");

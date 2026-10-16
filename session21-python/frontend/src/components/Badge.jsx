import { label } from "../api.js";

export default function Badge({ value }) {
  return <span className={`badge badge-${value}`}>{label(value)}</span>;
}

const CARDS = [
  { key: "items_total", label: "Total items" },
  { key: "available", label: "Available" },
  { key: "on_loan", label: "On loan" },
  { key: "maintenance", label: "Maintenance" },
  { key: "active_loans", label: "Open loans" },
  { key: "overdue_loans", label: "Overdue", warn: true },
];

export default function StatsCards({ stats, error }) {
  if (error) return <div className="banner error">Could not load stats: {error}</div>;
  return (
    <section className="stats" aria-label="Summary">
      {CARDS.map((card) => {
        const value = stats ? stats[card.key] : null;
        const hot = card.warn && value > 0;
        return (
          <div key={card.key} className={hot ? "stat warn" : "stat"}>
            <div className="stat-value">{value ?? "–"}</div>
            <div className="stat-label">{card.label}</div>
          </div>
        );
      })}
    </section>
  );
}

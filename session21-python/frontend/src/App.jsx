import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import Header from "./components/Header.jsx";
import StatsCards from "./components/StatsCards.jsx";
import ItemsPage from "./components/ItemsPage.jsx";
import LoansPage from "./components/LoansPage.jsx";

export default function App() {
  const [tab, setTab] = useState("items");
  const [info, setInfo] = useState(null);
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState("");
  // Bumped after any change so lists and stats reload.
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => {
    api.info().then(setInfo).catch(() => setInfo(null));
  }, []);

  useEffect(() => {
    api
      .stats()
      .then((s) => {
        setStats(s);
        setStatsError("");
      })
      .catch((err) => setStatsError(err.message));
  }, [version]);

  return (
    <>
      <Header info={info} />
      <main className="container">
        <StatsCards stats={stats} error={statsError} />

        <nav className="tabs" role="tablist">
          <button
            role="tab"
            aria-selected={tab === "items"}
            className={tab === "items" ? "tab active" : "tab"}
            onClick={() => setTab("items")}
          >
            Equipment
          </button>
          <button
            role="tab"
            aria-selected={tab === "loans"}
            className={tab === "loans" ? "tab active" : "tab"}
            onClick={() => setTab("loans")}
          >
            Loans
          </button>
        </nav>

        {tab === "items" ? (
          <ItemsPage version={version} onChange={refresh} />
        ) : (
          <LoansPage version={version} onChange={refresh} />
        )}
      </main>
      <footer className="footer container">
        GearLoan &middot; Srinidhi Narendran (24BCS10037)
      </footer>
    </>
  );
}

export default function Header({ info }) {
  return (
    <header className="header">
      <div className="container header-inner">
        <div className="brand">
          <img src="/favicon.svg" alt="" width="28" height="28" />
          <span>{info?.name || "GearLoan"}</span>
        </div>
        <span className="version" title="Backend version">
          {info ? `v${info.version}` : "offline"}
        </span>
      </div>
    </header>
  );
}

import { Database } from "lucide-react";

type ActiveView = "ask" | "catalogue" | "audit";

type TopBarProps = {
  activeView: ActiveView;
  onChangeView: (view: ActiveView) => void;
};

const navItems: Array<{ id: ActiveView; label: string }> = [
  { id: "ask", label: "Ask" },
  { id: "catalogue", label: "Catalogue" },
  { id: "audit", label: "Audit" }
];

export function TopBar({ activeView, onChangeView }: TopBarProps) {
  return (
    <header className="top-bar">
      <div className="brand-group">
        <span className="brand-name">Vellum-NLQ</span>
        <nav className="nav-tabs" aria-label="Primary">
          {navItems.map((item) => (
            <button
              className={item.id === activeView ? "nav-tab active" : "nav-tab"}
              key={item.id}
              onClick={() => onChangeView(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="status-group">
        <span className="catalogue-pill">
          <Database size={16} />
          health-uk
          <span className="active-dot" aria-hidden="true" />
          <strong>active</strong>
        </span>
        <span className="operational-pill">
          <span className="operational-check" aria-hidden="true">✓</span>
          operational
        </span>
      </div>
    </header>
  );
}

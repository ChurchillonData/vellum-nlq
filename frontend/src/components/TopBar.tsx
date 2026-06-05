import { Database } from "lucide-react";

import type { HealthResponse } from "../types";
import { CleanCheck } from "./CleanCheck";

type ActiveView = "ask" | "catalogue" | "audit";

type TopBarProps = {
  activeView: ActiveView;
  health: HealthResponse | null;
  onChangeView: (view: ActiveView) => void;
};

const navItems: Array<{ id: ActiveView; label: string }> = [
  { id: "ask", label: "Ask" },
  { id: "catalogue", label: "Catalogue" },
  { id: "audit", label: "Audit" }
];

export function TopBar({ activeView, health, onChangeView }: TopBarProps) {
  const isOperational = health?.status === "ok";
  const catalogueName = health?.catalogue ?? "health-uk";
  const dataWindow = health?.data_window
    ? `${formatDate(health.data_window.start_date)} - ${formatDate(health.data_window.end_date)}`
    : null;

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
        <span className={isOperational ? "catalogue-pill" : "catalogue-pill offline"}>
          <Database size={16} />
          {catalogueName}
          <span className={isOperational ? "active-dot" : "active-dot offline"} aria-hidden="true" />
          <strong>{isOperational ? "active" : "offline"}</strong>
        </span>
        {dataWindow && <span className="data-window-pill">{dataWindow}</span>}
        <span className={isOperational ? "operational-pill" : "operational-pill offline"}>
          <span className="operational-check" aria-hidden="true">
            <CleanCheck size="sm" />
          </span>
          {isOperational ? "operational" : "backend offline"}
        </span>
      </div>
    </header>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    month: "short",
    year: "numeric"
  }).format(date);
}

import {
  BarChart3,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Copy,
  FileText,
  Search,
  UserRound,
  WalletCards,
  Users
} from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";

import type { Metric } from "../types";

type CatalogueExplorerProps = {
  metrics: Metric[];
};

const metricIcons = [BarChart3, WalletCards, Users, BarChart3];

export function CatalogueExplorer({ metrics }: CatalogueExplorerProps) {
  const [selectedId, setSelectedId] = useState(metrics[0]?.id ?? "");
  const selected = useMemo(
    () => metrics.find((metric) => metric.id === selectedId) ?? metrics[0],
    [metrics, selectedId]
  );

  if (!selected) {
    return <main className="catalogue-layout">No catalogue loaded.</main>;
  }

  return (
    <main className="catalogue-layout">
      <aside className="metric-sidebar">
        <div className="sidebar-heading">Metric registry</div>
        <div className="metric-search">
          <Search size={17} />
          <span>Search metrics...</span>
          <kbd>Ctrl K</kbd>
        </div>

        <div className="metric-list">
          {metrics.map((metric, index) => {
            const Icon = metricIcons[index % metricIcons.length];

            return (
              <button
                className={metric.id === selected.id ? "metric-list-item active" : "metric-list-item"}
                key={metric.id}
                onClick={() => setSelectedId(metric.id)}
                type="button"
              >
                <span className="metric-list-icon">
                  <Icon size={23} />
                </span>
                <span>
                  <strong>{metric.label}</strong>
                  <small>{metric.id}</small>
                </span>
                <ChevronRight size={18} />
              </button>
            );
          })}
        </div>

        <button className="about-catalogue" type="button">
          <FileText size={18} />
          About the catalogue
        </button>
      </aside>

      <section className="metric-detail">
        <div className="metric-title-row">
          <div className="metric-title-copy">
            <span className="metric-icon">
              <BarChart3 size={28} />
            </span>
            <div>
              <h1>{selected.label}</h1>
              <code>{selected.id}</code>
              <p>{selected.description}</p>
            </div>
          </div>
          <span className="approved-pill">
            <CheckCircle2 size={17} />
            Approved
          </span>
        </div>

        <div className="catalogue-grid">
          <DetailBlock title="Definition">{selected.description}</DetailBlock>
          <DetailBlock title="Formula" wideOnDesktop>
            <div className="copyable-code">
              <code>{selected.formula.expression}</code>
              <Copy size={16} />
            </div>
          </DetailBlock>
          <DetailBlock title="Owner">
            <span className="inline-icon">
              <UserRound size={18} />
              {selected.owner}
            </span>
          </DetailBlock>
          <DetailBlock title="Version">
            <code className="small-code">{selected.version}</code>
          </DetailBlock>
          <DetailBlock title="Time anchor">
            <span className="inline-icon">
              <CalendarDays size={18} />
              <code>{selected.time_anchor}</code>
            </span>
          </DetailBlock>
          <DetailBlock title="Synonyms">{selected.synonyms.join(", ") || "None"}</DetailBlock>
          <DetailBlock title="Allowed dimensions" wideOnDesktop>
            <div className="tag-row">
              {["plan_tier", "treatment_category", "month", "region"].map((dimension) => (
                <span className="tag" key={dimension}>{dimension}</span>
              ))}
            </div>
          </DetailBlock>
          <DetailBlock title="Required joins (preview)" full>
            <div className="copyable-code muted">
              <code>{selected.required_tables.join(" -> ")} (member_id, period)</code>
              <Copy size={16} />
            </div>
          </DetailBlock>
        </div>

        <div className="catalogue-footnote">
          <FileText size={17} />
          Semantic catalogue backed by health-uk model - all definitions versioned and audited.
        </div>
      </section>
    </main>
  );
}

function DetailBlock({
  children,
  full = false,
  title,
  wideOnDesktop = false
}: {
  children: ReactNode;
  full?: boolean;
  title: string;
  wideOnDesktop?: boolean;
}) {
  const className = ["detail-block", full ? "full" : "", wideOnDesktop ? "wide-desktop" : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className}>
      <h2>{title}</h2>
      <div>{children}</div>
    </div>
  );
}

import { BookOpen, Calendar, CheckCircle2, Copy, Database } from "lucide-react";
import { useMemo, useState } from "react";

import type { Metric } from "../types";

type CatalogueExplorerProps = {
  metrics: Metric[];
};

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
        <div className="sidebar-heading">
          <span>Metric registry</span>
          <kbd>⌘K</kbd>
        </div>
        {metrics.map((metric) => (
          <button
            className={metric.id === selected.id ? "metric-list-item active" : "metric-list-item"}
            key={metric.id}
            onClick={() => setSelectedId(metric.id)}
            type="button"
          >
            <BookOpen size={20} />
            <span>
              <strong>{metric.label}</strong>
              <small>{metric.id}</small>
            </span>
          </button>
        ))}
      </aside>

      <section className="metric-detail">
        <div className="metric-title-row">
          <div>
            <span className="metric-icon">
              <Database size={26} />
            </span>
            <h1>{selected.label}</h1>
            <code>{selected.id}</code>
            <p>{selected.description}</p>
          </div>
          <span className="approved-pill">
            <CheckCircle2 size={17} />
            Approved
          </span>
        </div>

        <div className="catalogue-grid">
          <DetailBlock title="Definition">{selected.description}</DetailBlock>
          <DetailBlock title="Formula">
            <div className="copyable-code">
              <code>{selected.formula.expression}</code>
              <Copy size={16} />
            </div>
          </DetailBlock>
          <DetailBlock title="Owner">{selected.owner}</DetailBlock>
          <DetailBlock title="Version">
            <code>{selected.version}</code>
          </DetailBlock>
          <DetailBlock title="Time anchor">
            <span className="inline-icon">
              <Calendar size={17} />
              <code>{selected.time_anchor}</code>
            </span>
          </DetailBlock>
          <DetailBlock title="Synonyms">{selected.synonyms.join(", ") || "None"}</DetailBlock>
          <DetailBlock title="Required tables" wide>
            <div className="tag-row">
              {selected.required_tables.map((table) => (
                <span className="tag" key={table}>{table}</span>
              ))}
            </div>
          </DetailBlock>
        </div>
      </section>
    </main>
  );
}

function DetailBlock({
  children,
  title,
  wide = false
}: {
  children: React.ReactNode;
  title: string;
  wide?: boolean;
}) {
  return (
    <div className={wide ? "detail-block wide" : "detail-block"}>
      <h2>{title}</h2>
      <div>{children}</div>
    </div>
  );
}

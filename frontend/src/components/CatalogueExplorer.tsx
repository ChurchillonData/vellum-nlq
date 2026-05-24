import {
  BarChart3,
  BookOpen,
  CalendarDays,
  ChevronRight,
  ClipboardList,
  Calculator,
  Copy,
  Database,
  Download,
  Filter,
  Gauge,
  GitBranch,
  Layers3,
  Lightbulb,
  LockKeyhole,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
  Tags,
  TrendingUp,
  UserRound,
  WalletCards
} from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";

import type { Metric } from "../types";

type CatalogueExplorerProps = {
  metrics: Metric[];
};

const defaultDimensions = ["plan_tier", "treatment_category", "month", "region"];

export function CatalogueExplorer({ metrics }: CatalogueExplorerProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedId, setSelectedId] = useState("loss_ratio");
  const selectedMetric = useMemo(
    () => metrics.find((metric) => metric.id === selectedId) ?? metrics.find((metric) => metric.id === "loss_ratio") ?? metrics[0],
    [metrics, selectedId]
  );
  const insights = useMemo(() => getMetricInsights(selectedMetric), [selectedMetric]);
  const filteredMetrics = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    if (!query) {
      return metrics;
    }

    return metrics.filter((metric) =>
      [metric.label, metric.id, metric.description, metric.formula.expression, ...metric.synonyms]
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [metrics, searchTerm]);

  if (!selectedMetric) {
    return <main className="catalogue-hub">No catalogue loaded.</main>;
  }

  return (
    <main className="catalogue-hub">
      <section className="catalogue-hero">
        <div className="catalogue-primary-panel">
          <div className="catalogue-primary-header">
            <span className="catalogue-large-icon icon-tone-blue">
              <BarChart3 size={42} />
            </span>
            <div className="catalogue-title-copy">
              <div className="catalogue-title-line">
                <select
                  aria-label="Selected metric"
                  className="metric-switch"
                  onChange={(event) => setSelectedId(event.target.value)}
                  value={selectedMetric.id}
                >
                  {metrics.map((metric) => (
                    <option key={metric.id} value={metric.id}>
                      {toTitleCase(metric.label)}
                    </option>
                  ))}
                </select>
                <code>{selectedMetric.id}</code>
              </div>
              <p>{selectedMetric.description}</p>
            </div>
            <span className="approved-pill catalogue-approved">
              <ShieldCheck size={17} />
              Approved
            </span>
          </div>

          <div className="catalogue-detail-grid">
            <CatalogueBlock icon={<BookOpen size={17} />} title="Definition" wide>{selectedMetric.description}</CatalogueBlock>
            <CatalogueBlock icon={<Calculator size={17} />} title="Formula" tone="blue" wide>
              <div className="catalogue-code-strip">
                <code>{selectedMetric.formula.expression}</code>
                <Copy size={16} />
              </div>
            </CatalogueBlock>
            <CatalogueMeta icon={<UserRound size={21} />} label="Owner" tone="teal" value={formatOwner(selectedMetric.owner)} />
            <CatalogueMeta icon={<GitBranch size={21} />} label="Version" mono tone="violet" value={selectedMetric.version} />
            <CatalogueMeta
              icon={<CalendarDays size={21} />}
              label="Time anchor"
              tone="blue"
              value={`${selectedMetric.time_anchor} (monthly aggregation)`}
              mono
              wide
            />
            <CatalogueBlock icon={<Tags size={17} />} title="Synonyms" tone="amber" wide>
              <div className="catalogue-chip-row">
                {getSynonyms(selectedMetric).map((synonym) => (
                  <span className="catalogue-chip" key={synonym}>{synonym}</span>
                ))}
              </div>
            </CatalogueBlock>
            <CatalogueBlock icon={<Layers3 size={17} />} title="Allowed dimensions" tone="violet" wide>
              <div className="catalogue-chip-row">
                {defaultDimensions.map((dimension) => (
                  <span className="catalogue-chip accent" key={dimension}>{dimension}</span>
                ))}
              </div>
            </CatalogueBlock>
            <CatalogueBlock title="Required joins (preview)" full icon={<Network size={17} />} tone="blue">
              <div className="catalogue-code-strip muted">
                <code>{formatJoinPreview(selectedMetric)}</code>
                <Copy size={16} />
              </div>
            </CatalogueBlock>
          </div>
        </div>

        <aside className="catalogue-side-stack">
          <div className="catalogue-side-card">
            <div className="side-card-heading">
              <span className="side-card-icon icon-tone-amber">
                <Lightbulb size={24} />
              </span>
              <div>
                <h2>Insights</h2>
                <code>{selectedMetric.id}</code>
              </div>
            </div>
            <ul className="insight-list">
              {insights.map((insight) => (
                <li key={insight}>{insight}</li>
              ))}
            </ul>
          </div>

          <div className="catalogue-about-card">
            <span className="about-card-icon icon-tone-blue">
              <ClipboardList size={22} />
            </span>
            <h2>About the catalogue</h2>
            <p>
              Unified metric registry with lineage, definitions, and certification.
              All metrics follow Vellum semantic layer governance for NLQ.
            </p>
            <div className="about-card-stats">
              <span>
                <Database size={17} />
                {Math.max(10, metrics.length)} active metrics
              </span>
              <span>
                <RefreshCw size={17} />
                auto-synced weekly
              </span>
            </div>
          </div>
        </aside>
      </section>

      <section className="catalogue-registry">
        <div className="registry-toolbar">
          <div>
            <h2>
              <ClipboardList size={20} />
              Metric registry explorer
            </h2>
            <span>Full catalog</span>
          </div>
          <div className="registry-actions">
            <label className="registry-search">
              <Search size={17} />
              <input
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search metrics..."
                value={searchTerm}
              />
            </label>
            <button type="button">
              <Filter size={16} />
              All metrics
            </button>
            <button type="button">
              <Download size={16} />
              Export
            </button>
          </div>
        </div>

        <div className="registry-table-wrap">
          <table className="registry-table">
            <thead>
              <tr>
                <th>Metric name</th>
                <th>Definition</th>
                <th>Technical name</th>
                <th>Version</th>
                <th>Allowed dimensions</th>
                <th>Certification</th>
                <th>Updated</th>
                <th aria-label="Open metric" />
              </tr>
            </thead>
            <tbody>
              {filteredMetrics.map((metric, index) => (
                <tr
                  className={metric.id === selectedMetric.id ? "selected" : ""}
                  key={metric.id}
                  onClick={() => setSelectedId(metric.id)}
                >
                  <td>
                    <span className="registry-name">
                      <span className="registry-metric-icon">
                        {getMetricIcon(metric.id, index)}
                      </span>
                      {toTitleCase(metric.label)}
                    </span>
                  </td>
                  <td>{shorten(metric.description)}</td>
                  <td><code>{metric.id}</code></td>
                  <td>{metric.version}</td>
                  <td>{defaultDimensions.join(", ")}</td>
                  <td><span className={index === 0 ? "cert-pill gold" : "cert-pill silver"}>{index === 0 ? "Gold" : "Silver"}</span></td>
                  <td>{index === 0 ? "2h ago" : "4h ago"}</td>
                  <td><ChevronRight size={17} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="catalogue-status-bar">
        <span>
          <ShieldCheck size={17} />
          Vellum semantic layer v2.1
        </span>
        <span>
          <Database size={17} />
          Source systems connected: 6
        </span>
        <span>
          <LockKeyhole size={17} />
          Governed & certified
        </span>
        <span>
          <RefreshCw size={17} />
          Last refreshed: just now
        </span>
      </section>
    </main>
  );
}

function CatalogueBlock({
  children,
  full = false,
  icon,
  title,
  tone = "teal",
  wide = false
}: {
  children: ReactNode;
  full?: boolean;
  icon?: ReactNode;
  title: string;
  tone?: IconTone;
  wide?: boolean;
}) {
  return (
    <div className={["catalogue-block", full ? "full" : "", wide ? "wide" : ""].filter(Boolean).join(" ")}>
      <h2 className={`icon-label icon-tone-${tone}`}>{icon}{title}</h2>
      <div>{children}</div>
    </div>
  );
}

type IconTone = "amber" | "blue" | "teal" | "violet";

function CatalogueMeta({
  icon,
  label,
  mono = false,
  tone = "teal",
  value,
  wide = false
}: {
  icon: ReactNode;
  label: string;
  mono?: boolean;
  tone?: IconTone;
  value: string;
  wide?: boolean;
}) {
  return (
    <div className={["catalogue-meta", wide ? "wide" : ""].filter(Boolean).join(" ")}>
      <span className={`icon-tone-${tone}`}>{icon}</span>
      <div>
        <h2 className={`icon-label icon-tone-${tone}`}>{label}</h2>
        <p className={mono ? "mono" : ""}>{value}</p>
      </div>
    </div>
  );
}

function getMetricIcon(metricId: string, index: number): ReactNode {
  if (metricId.includes("loss")) {
    return <Gauge size={17} />;
  }

  if (metricId.includes("paid")) {
    return <WalletCards size={17} />;
  }

  if (metricId.includes("frequency")) {
    return <TrendingUp size={17} />;
  }

  return index % 2 === 0 ? <BarChart3 size={17} /> : <Calculator size={17} />;
}

function formatJoinPreview(metric: Metric): string {
  if (metric.id === "loss_ratio") {
    return "claims -> premium (member_id, period), member_dimension";
  }

  return `${metric.required_tables.join(" -> ")} (approved join path)`;
}

function getMetricInsights(metric: Metric): string[] {
  if (metric.id === "paid_claims") {
    return [
      "Tracks total settled claim value for the selected reporting window.",
      "Best grouped by region, claim type, provider, or plan tier.",
      "Uses paid date, so it reflects cash movement rather than incurred exposure.",
      "Useful for claims operations monitoring and payment trend reviews."
    ];
  }

  if (metric.id === "claim_frequency") {
    return [
      "Shows utilisation pressure by normalising claim counts against member exposure.",
      "Best grouped by age band, region, plan tier, or month.",
      "Helpful for spotting behaviour changes before claim cost rises fully appear.",
      "Requires clean member-month exposure to avoid misleading comparisons."
    ];
  }

  return [
    "Connects incurred claims to earned premium for a clear profitability signal.",
    "Best grouped by plan tier, month, region, or treatment category.",
    "Uses incurred date, so it is suited to underwriting and actuarial views.",
    "Sensitive to late claims and premium alignment across the same period."
  ];
}

function formatOwner(owner: string): string {
  const normalized = owner.trim();

  if (!normalized) {
    return "Finance Analytics - J. Mercer";
  }

  if (normalized.length < 16) {
    return `${toTitleCase(normalized)} Analytics`;
  }

  return normalized;
}

function getSynonyms(metric: Metric): string[] {
  if (metric.synonyms.length >= 3) {
    return metric.synonyms.slice(0, 3);
  }

  if (metric.id === "loss_ratio") {
    return ["loss rate", "claims leverage", "incurred loss ratio"];
  }

  return [...metric.synonyms, metric.label].slice(0, 3);
}

function shorten(text: string): string {
  return text.length > 82 ? `${text.slice(0, 79)}...` : text;
}

function toTitleCase(text: string): string {
  return text.replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
}

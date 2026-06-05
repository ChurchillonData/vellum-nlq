import {
  AiNetworkIcon,
  Analytics01Icon,
  ArrowDown01Icon,
  ArrowRight01Icon,
  BookOpenTextIcon,
  BulbIcon,
  Calculator01Icon,
  Calendar03Icon,
  CheckmarkBadge02Icon,
  ClipboardCopyIcon,
  CloudDownloadIcon,
  DashboardSpeed02Icon,
  FilterIcon,
  GitBranchIcon,
  HierarchySquare04Icon,
  LanguageSkillIcon,
  Layers01Icon,
  LockKeyIcon,
  PresentationLineChart01Icon,
  RefreshIcon,
  Search01Icon,
  TrendingUpDownIcon,
  UserCircleIcon,
  WalletCardsIcon
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import type { IconSvgElement } from "@hugeicons/react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";

import type { MappingCoverageResponse, Metric } from "../types";

type CatalogueExplorerProps = {
  mappingCoverage: MappingCoverageResponse | null;
  metrics: Metric[];
};

type SynonymTab = "business" | "analyst" | "phrasing";

type SynonymGroup = {
  id: SynonymTab;
  label: string;
  terms: string[];
};

export function CatalogueExplorer({ mappingCoverage, metrics }: CatalogueExplorerProps) {
  const [isMetricMenuOpen, setIsMetricMenuOpen] = useState(false);
  const [isSynonymCardOpen, setIsSynonymCardOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedId, setSelectedId] = useState("loss_ratio");
  const [synonymTab, setSynonymTab] = useState<SynonymTab>("business");
  const selectedMetric = useMemo(
    () => metrics.find((metric) => metric.id === selectedId) ?? metrics.find((metric) => metric.id === "loss_ratio") ?? metrics[0],
    [metrics, selectedId]
  );
  const allowedDimensions = useMemo(() => getAllowedDimensions(selectedMetric), [selectedMetric]);
  const insights = useMemo(() => getMetricInsights(selectedMetric), [selectedMetric]);
  const synonymGroups = useMemo(() => getSynonymGroups(selectedMetric), [selectedMetric]);
  const activeSynonymGroup = synonymGroups.find((group) => group.id === synonymTab) ?? synonymGroups[0];
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
              <Icon icon={Analytics01Icon} size={42} />
            </span>
            <div className="catalogue-title-copy">
              <div className="catalogue-title-line">
                <h1 className="catalogue-metric-title">{toTitleCase(selectedMetric.label)}</h1>
                <div className="metric-selector">
                  <button
                    aria-expanded={isMetricMenuOpen}
                    aria-haspopup="listbox"
                    className="metric-selector-button"
                    onClick={() => setIsMetricMenuOpen((isOpen) => !isOpen)}
                    type="button"
                  >
                    <code>{selectedMetric.id}</code>
                    <Icon icon={ArrowDown01Icon} size={15} />
                  </button>
                  {isMetricMenuOpen ? (
                    <div className="metric-selector-menu" role="listbox">
                      {metrics.map((metric, index) => (
                        <button
                          aria-selected={metric.id === selectedMetric.id}
                          className={metric.id === selectedMetric.id ? "selected" : ""}
                          key={metric.id}
                          onClick={() => {
                            setSelectedId(metric.id);
                            setIsMetricMenuOpen(false);
                            setIsSynonymCardOpen(false);
                            setSynonymTab("business");
                          }}
                          role="option"
                          type="button"
                        >
                          <span className="metric-menu-icon">{getMetricIcon(metric.id, index)}</span>
                          <span>
                            <strong>{toTitleCase(metric.label)}</strong>
                            <code>{metric.id}</code>
                          </span>
                          {metric.id === selectedMetric.id ? <Icon icon={CheckmarkBadge02Icon} size={17} /> : null}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
            <span className="approved-pill catalogue-approved">
              <Icon icon={CheckmarkBadge02Icon} size={17} />
              Approved
            </span>
          </div>

          <div className="catalogue-detail-grid">
            <CatalogueBlock icon={<Icon icon={BookOpenTextIcon} size={17} />} title="Definition" wide>{selectedMetric.description}</CatalogueBlock>
            <CatalogueBlock icon={<Icon icon={Calculator01Icon} size={17} />} title="Formula" tone="blue" wide>
              <div className="catalogue-code-strip formula-sql">
                <code>{renderFormulaSql(selectedMetric.formula.expression)}</code>
                <Icon icon={ClipboardCopyIcon} size={16} />
              </div>
            </CatalogueBlock>
            <CatalogueMeta icon={<Icon icon={UserCircleIcon} size={21} />} label="Owner" tone="teal" value={formatOwner(selectedMetric.owner)} />
            <CatalogueMeta icon={<Icon icon={GitBranchIcon} size={21} />} label="Version" mono tone="violet" value={selectedMetric.version} />
            <CatalogueMeta
              icon={<Icon icon={Calendar03Icon} size={21} />}
              label="Time anchor"
              tone="blue"
              value={`${selectedMetric.time_anchor} (monthly aggregation)`}
              mono
              wide
            />
            <CatalogueBlock icon={<Icon icon={LanguageSkillIcon} size={17} />} title="Synonyms" tone="amber" wide>
              <div className="synonym-preview">
                <div className="catalogue-chip-row">
                {getSynonyms(selectedMetric).map((synonym) => (
                    <span className="catalogue-chip" key={synonym}>{synonym}</span>
                  ))}
                </div>
                <button
                  className="synonym-map-button"
                  onClick={() => setIsSynonymCardOpen((isOpen) => !isOpen)}
                  type="button"
                >
                  <Icon icon={HierarchySquare04Icon} size={15} />
                  {isSynonymCardOpen ? "Hide map" : "View map"}
                </button>
              </div>
              {isSynonymCardOpen ? (
                <div className="synonym-glass-card">
                  <div className="synonym-tabs" role="tablist">
                    {synonymGroups.map((group) => (
                      <button
                        aria-selected={group.id === activeSynonymGroup.id}
                        className={group.id === activeSynonymGroup.id ? "active" : ""}
                        key={group.id}
                        onClick={() => setSynonymTab(group.id)}
                        role="tab"
                        type="button"
                      >
                        {group.label}
                      </button>
                    ))}
                  </div>
                  <div className="synonym-term-grid" role="tabpanel">
                    {activeSynonymGroup.terms.map((term) => (
                      <span key={term}>{term}</span>
                    ))}
                  </div>
                </div>
              ) : null}
            </CatalogueBlock>
            <CatalogueBlock icon={<Icon icon={Layers01Icon} size={17} />} title="Allowed dimensions" tone="violet" wide>
              <div className="catalogue-chip-row">
                {allowedDimensions.map((dimension) => (
                  <span className="catalogue-chip accent" key={dimension}>{dimension}</span>
                ))}
              </div>
            </CatalogueBlock>
            <CatalogueBlock title="Required joins (preview)" full icon={<Icon icon={AiNetworkIcon} size={17} />} tone="blue">
              <div className="catalogue-code-strip muted">
                <code>{formatJoinPreview(selectedMetric)}</code>
                <Icon icon={ClipboardCopyIcon} size={16} />
              </div>
            </CatalogueBlock>
          </div>
        </div>

        <aside className="catalogue-side-stack">
          <div className="catalogue-side-card">
            <div className="side-card-heading">
              <span className="side-card-icon icon-tone-amber">
                <Icon icon={BulbIcon} size={24} />
              </span>
              <div>
                <h2>Insights</h2>
              </div>
            </div>
            <ul className="insight-list">
              {insights.map((insight) => (
                <li key={insight}>{insight}</li>
              ))}
            </ul>
          </div>

          <MappingCoverageCard coverage={mappingCoverage} />
        </aside>
      </section>

      <section className="catalogue-registry">
        <div className="registry-toolbar">
          <div>
            <h2>
              <Icon icon={PresentationLineChart01Icon} size={20} />
              Metric registry explorer
            </h2>
            <span>Full catalog</span>
          </div>
          <div className="registry-actions">
            <label className="registry-search">
              <Icon icon={Search01Icon} size={17} />
              <input
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search metrics..."
                value={searchTerm}
              />
            </label>
            <button type="button">
              <Icon icon={FilterIcon} size={16} />
              All metrics
            </button>
            <button type="button">
              <Icon icon={CloudDownloadIcon} size={16} />
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
                  onClick={() => {
                    setSelectedId(metric.id);
                    setIsSynonymCardOpen(false);
                    setSynonymTab("business");
                  }}
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
                  <td>{getAllowedDimensions(metric).join(", ")}</td>
                  <td><span className={index === 0 ? "cert-pill gold" : "cert-pill silver"}>{index === 0 ? "Gold" : "Silver"}</span></td>
                  <td>{formatReviewedDate(metric.last_reviewed)}</td>
                  <td><Icon icon={ArrowRight01Icon} size={17} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="catalogue-status-bar">
        <span>
          <Icon icon={CheckmarkBadge02Icon} size={17} />
          Vellum semantic layer Vellum 2.5
        </span>
        <span>
          <Icon icon={PresentationLineChart01Icon} size={17} />
          Source systems connected: {metrics.length}
        </span>
        <span>
          <Icon icon={LockKeyIcon} size={17} />
          Governed & certified
        </span>
        <span>
          <Icon icon={RefreshIcon} size={17} />
          Last refreshed: just now
        </span>
      </section>
    </main>
  );
}

function MappingCoverageCard({ coverage }: { coverage: MappingCoverageResponse | null }) {
  if (coverage === null) {
    return (
      <div className="catalogue-side-card mapping-coverage-card">
        <div className="side-card-heading">
          <span className="side-card-icon icon-tone-blue">
            <Icon icon={AiNetworkIcon} size={24} />
          </span>
          <div>
            <h2>Partner mapping</h2>
          </div>
        </div>
        <p>Mapping coverage will appear here when the backend is available.</p>
      </div>
    );
  }

  const tablePercent = percentage(coverage.mapped_tables, coverage.total_tables);
  const columnPercent = percentage(coverage.mapped_columns, coverage.total_columns);

  return (
    <div className="catalogue-side-card mapping-coverage-card">
      <div className="side-card-heading">
        <span className="side-card-icon icon-tone-blue">
          <Icon icon={AiNetworkIcon} size={24} />
        </span>
        <div>
          <h2>Partner mapping</h2>
          <p>{coverage.partner} {"->"} {coverage.catalogue}</p>
        </div>
      </div>

      <div className="mapping-coverage-grid">
        <CoverageMeter label="Tables" total={coverage.total_tables} value={coverage.mapped_tables} percent={tablePercent} />
        <CoverageMeter label="Columns" total={coverage.total_columns} value={coverage.mapped_columns} percent={columnPercent} />
      </div>

      <div className="mapping-gap-list">
        <strong>Open gaps</strong>
        <span>
          {coverage.missing_tables.length + coverage.missing_columns.length === 0
            ? "No missing tables or columns in the example mapping."
            : `${coverage.missing_tables.length} tables, ${coverage.missing_columns.length} columns`}
        </span>
      </div>
    </div>
  );
}

function CoverageMeter({
  label,
  percent,
  total,
  value
}: {
  label: string;
  percent: number;
  total: number;
  value: number;
}) {
  return (
    <div className="coverage-meter">
      <div>
        <span>{label}</span>
        <strong>{value}/{total}</strong>
      </div>
      <div className="coverage-track">
        <span style={{ width: `${percent}%` }} />
      </div>
    </div>
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

function Icon({ icon, size }: { icon: IconSvgElement; size: number }) {
  return <HugeiconsIcon absoluteStrokeWidth icon={icon} size={size} strokeWidth={1.7} />;
}

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
    return <Icon icon={DashboardSpeed02Icon} size={17} />;
  }

  if (metricId.includes("paid")) {
    return <Icon icon={WalletCardsIcon} size={17} />;
  }

  if (metricId.includes("frequency")) {
    return <Icon icon={TrendingUpDownIcon} size={17} />;
  }

  return index % 2 === 0 ? <Icon icon={Analytics01Icon} size={17} /> : <Icon icon={Calculator01Icon} size={17} />;
}

function formatJoinPreview(metric: Metric): string {
  if (metric.join_preview.length > 0) {
    return metric.join_preview.join("; ");
  }

  return `${metric.required_tables.join(" -> ")} (catalogue-approved path)`;
}

function getAllowedDimensions(metric: Metric): string[] {
  if (metric.allowed_dimensions.length > 0) {
    return metric.allowed_dimensions;
  }

  return ["plan_tier", "region"];
}

function renderFormulaSql(expression: string): ReactNode[] {
  const tokenPattern = /(SUM|AVG|COUNT|DISTINCT|NULLIF|MIN|MAX)|(\b\d+(?:\.\d+)?\b)|([a-z_]+\.[a-z_]+)/gi;
  const nodes: ReactNode[] = [];
  let lastIndex = 0;

  for (const match of expression.matchAll(tokenPattern)) {
    const token = match[0];
    const index = match.index ?? 0;

    if (index > lastIndex) {
      nodes.push(expression.slice(lastIndex, index));
    }

    if (match[1]) {
      nodes.push(<span className="sql-function" key={`${token}-${index}`}>{token}</span>);
    } else if (match[2]) {
      nodes.push(<span className="sql-number" key={`${token}-${index}`}>{token}</span>);
    } else {
      nodes.push(<span className="sql-identifier" key={`${token}-${index}`}>{token}</span>);
    }

    lastIndex = index + token.length;
  }

  if (lastIndex < expression.length) {
    nodes.push(expression.slice(lastIndex));
  }

  return nodes;
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

  if (metric.id === "decline_rate") {
    return [
      "Tracks the share of billed service value that was declined.",
      "Best grouped by consultant specialty, plan tier, or region.",
      "Useful for spotting provider behaviour and adjudication pressure.",
      "Requires claim line and decline reason lineage for defensible review."
    ];
  }

  if (metric.id === "claim_severity") {
    return [
      "Measures average incurred cost per claim in the selected period.",
      "Best grouped by plan tier, region, or treatment category.",
      "Useful for identifying expensive claim mixes and outlier patterns.",
      "Should be interpreted alongside frequency to separate cost from usage."
    ];
  }

  if (metric.id === "incurred_claims") {
    return [
      "Shows total incurred claim value anchored by incurred date.",
      "Best grouped by plan tier, region, or month.",
      "Useful for underwriting reviews and reserve-aware performance analysis.",
      "Complements paid claims by capturing exposure before final cash settlement."
    ];
  }

  return [
    `${toTitleCase(metric.label)} is governed by the ${formatOwner(metric.owner)} catalogue owner.`,
    `Anchored on ${metric.time_anchor} for consistent period filtering.`,
    `Supports grouping by ${getAllowedDimensions(metric).join(", ")}.`,
    "Returns SQL provenance, validation results, and audit trace metadata."
  ];
}

function getSynonymGroups(metric: Metric): SynonymGroup[] {
  const catalogueSynonyms = Array.from(new Set([metric.label, metric.id, ...metric.synonyms]));

  if (metric.id === "paid_claims") {
    return [
      {
        id: "business",
        label: "Business terms",
        terms: [
          "paid claims",
          "claims paid",
          "claim payments",
          "settled claims",
          "paid loss",
          "claims payout",
          "payment volume",
          "benefit payments",
          "reimbursed claims",
          "cash claims"
        ]
      },
      {
        id: "analyst",
        label: "Analyst language",
        terms: [
          "net paid amount",
          "paid claim amount",
          "claim line payments",
          "posted payments",
          "paid loss amount",
          "settlement value",
          "paid date total",
          "claims cash flow",
          "net claim paid",
          "payment run total"
        ]
      },
      {
        id: "phrasing",
        label: "User phrasing",
        terms: [
          "how much did we pay in claims",
          "show claims paid",
          "total payouts last month",
          "claims money paid out",
          "what did claims cost in cash",
          "payments by region",
          "settled claims by plan",
          "claims paid over time",
          "how much was reimbursed",
          "paid claims trend"
        ]
      }
    ];
  }

  if (metric.id === "claim_frequency") {
    return [
      {
        id: "business",
        label: "Business terms",
        terms: [
          "claim frequency",
          "claims per member",
          "claim rate",
          "utilisation rate",
          "claims incidence",
          "member claim activity",
          "claim volume rate",
          "claims usage",
          "service utilisation",
          "claim count rate"
        ]
      },
      {
        id: "analyst",
        label: "Analyst language",
        terms: [
          "claims per 1,000 member months",
          "distinct claims per exposure",
          "claim count normalized",
          "incidence per member month",
          "member-month frequency",
          "utilisation per exposure",
          "frequency numerator",
          "exposure adjusted claims",
          "claim density",
          "normalized claim volume"
        ]
      },
      {
        id: "phrasing",
        label: "User phrasing",
        terms: [
          "how often are members claiming",
          "claims per member this quarter",
          "are people claiming more",
          "claim activity by region",
          "usage by plan tier",
          "how frequent are claims",
          "member claims trend",
          "claims volume per member",
          "where is utilisation rising",
          "claim frequency by month"
        ]
      }
    ];
  }

  if (metric.id === "loss_ratio") {
    return [
      {
        id: "business",
        label: "Business terms",
        terms: [
          "loss ratio",
          "loss rate",
          "claims ratio",
          "claims leverage",
          "underwriting ratio",
          "plan profitability",
          "premium loss ratio",
          "incurred loss ratio",
          "claims to premium",
          "medical loss ratio"
        ]
      },
      {
        id: "analyst",
        label: "Analyst language",
        terms: [
          "incurred claims over earned premium",
          "net incurred divided by premium",
          "claims-to-premium ratio",
          "incurred loss over premium",
          "premium adequacy ratio",
          "loss ratio KPI",
          "financial KPI loss ratio",
          "claims cost ratio",
          "earned premium denominator",
          "incurred amount numerator"
        ]
      },
      {
        id: "phrasing",
        label: "User phrasing",
        terms: [
          "how profitable was the plan",
          "claims compared to premium",
          "did premiums cover claims",
          "loss ratio by plan tier",
          "claims versus premium",
          "how much premium was used by claims",
          "which plan has high losses",
          "underwriting performance by month",
          "show loss rate for Q1",
          "how is claims leverage trending"
        ]
      }
    ];
  }

  return [
    {
      id: "business",
      label: "Business terms",
      terms: expandTerms(catalogueSynonyms, [
        `${metric.label} KPI`,
        `${metric.label} measure`,
        `${metric.label} metric`,
        `${metric.label} trend`,
        `${metric.label} by plan`
      ])
    },
    {
      id: "analyst",
      label: "Analyst language",
      terms: expandTerms(catalogueSynonyms, [
        metric.formula.expression,
        metric.formula.numerator,
        metric.formula.denominator ?? metric.time_anchor,
        `${metric.time_anchor} anchored metric`,
        `${metric.owner} owned metric`
      ])
    },
    {
      id: "phrasing",
      label: "User phrasing",
      terms: expandTerms(catalogueSynonyms, [
        `show ${metric.label}`,
        `${metric.label} for Q1`,
        `${metric.label} by region`,
        `${metric.label} by plan tier`,
        `what changed in ${metric.label}`
      ])
    }
  ];
}

function expandTerms(primaryTerms: string[], fallbackTerms: string[]): string[] {
  return Array.from(new Set([...primaryTerms, ...fallbackTerms])).slice(0, 10);
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

  return [...metric.synonyms, metric.label].slice(0, 3);
}

function formatReviewedDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(date);
}

function shorten(text: string): string {
  return text.length > 82 ? `${text.slice(0, 79)}...` : text;
}

function percentage(value: number, total: number): number {
  if (total <= 0) {
    return 0;
  }

  return Math.round((value / total) * 100);
}

function toTitleCase(text: string): string {
  return text.replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
}

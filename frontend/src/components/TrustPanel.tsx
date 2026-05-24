import { CheckCircle2, Code2, Copy, Shield } from "lucide-react";

import type { AskResponse, Metric } from "../types";

type TrustPanelProps = {
  askResult: AskResponse;
  metric: Metric;
};

export function TrustPanel({ askResult, metric }: TrustPanelProps) {
  const answer = askResult.answer;
  const validation = answer?.validation;
  const statusLabel = validation?.passed ? "validated" : askResult.status;

  return (
    <aside className="trust-panel">
      <div className="panel-header">
        <h2>
          <Shield size={22} />
          Trust and transparency
        </h2>
        <span className={`validation-pill ${validation?.passed ? "ok" : "muted"}`}>
          <CheckCircle2 size={15} />
          {statusLabel}
        </span>
      </div>

      <dl className="metadata-list">
        <MetaRow label="Metric used" value={metric.id} />
        <MetaRow label="Metric version" value={metric.version} mono />
        <MetaRow label="Time anchor" value={metric.time_anchor} mono />
        <MetaRow label="Tables used" value={answer?.provenance.tables_used?.join(", ") ?? "Not generated"} />
        <MetaRow
          label="Validation result"
          value={
            validation?.passed
              ? `${validation.rules_checked.length} rules checked`
              : askResult.safety?.rule_id ?? "Pending"
          }
        />
        <MetaRow label="Audit / Query ID" value={askResult.query_id} mono />
        <MetaRow label="Execution mode" value={answer?.execution_mode ?? "not executed"} mono />
      </dl>

      <div className="sql-header">
        <span>
          <Code2 size={18} />
          Generated SQL
        </span>
        <button
          className="icon-button"
          disabled={!answer?.sql}
          onClick={() => answer?.sql && navigator.clipboard.writeText(answer.sql)}
          type="button"
        >
          <Copy size={16} />
          Copy
        </button>
      </div>
      <pre className="sql-block">{answer?.sql ?? "-- No SQL generated for this state."}</pre>
    </aside>
  );
}

function MetaRow({
  label,
  mono = false,
  value
}: {
  label: string;
  mono?: boolean;
  value: string;
}) {
  return (
    <div className="metadata-row">
      <dt>{label}</dt>
      <dd className={mono ? "mono" : ""}>{value}</dd>
    </div>
  );
}

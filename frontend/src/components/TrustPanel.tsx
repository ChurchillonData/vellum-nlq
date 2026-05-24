import {
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  Code2,
  Copy,
  Shield
} from "lucide-react";

import type { AskResponse, Metric } from "../types";

type TrustPanelProps = {
  askResult: AskResponse;
  metric: Metric;
};

export function TrustPanel({ askResult, metric }: TrustPanelProps) {
  if (askResult.status === "clarification_required") {
    return <ClarificationPanel askResult={askResult} />;
  }

  if (askResult.status === "blocked") {
    return <BlockedPanel askResult={askResult} />;
  }

  return <AnswerPanel askResult={askResult} metric={metric} />;
}

function AnswerPanel({ askResult, metric }: TrustPanelProps) {
  const answer = askResult.answer;
  const validation = answer?.validation;
  const joins = answer?.provenance.joins_used?.join("; ") ?? "claims -> premium (member_id)";

  return (
    <aside className="trust-panel">
      <div className="panel-header">
        <h2>
          <Shield size={26} />
          Trust & transparency
        </h2>
        <span className="validation-pill ok">
          <CheckCircle2 size={15} />
          validated
        </span>
      </div>

      <dl className="metadata-list">
        <MetaRow label="Metric used" value={`${metric.id} (financial_kpi)`} mono />
        <MetaRow label="Metric version" value={metric.version} mono />
        <MetaRow label="Time anchor" value={metric.time_anchor} mono />
        <MetaRow label="Joins used" value={joins} mono />
        <MetaRow
          label="Validation result"
          value={
            validation?.passed
              ? `${validation.rules_checked.length} rules checked - no violations`
              : "pending"
          }
          tone="success"
        />
        <MetaRow label="Audit / Query ID" value={askResult.query_id} mono />
        <MetaRow label="Latency" value="234 ms execution - 72 ms planning" mono />
      </dl>

      <SqlBlock sql={answer?.sql ?? "-- No SQL generated for this state."} />
    </aside>
  );
}

function ClarificationPanel({ askResult }: { askResult: AskResponse }) {
  const metrics = askResult.candidates.map((candidate) => candidate.metric_id).join(", ");

  return (
    <aside className="trust-panel">
      <div className="panel-header">
        <h2>
          <ClipboardList size={25} />
          Resolution state
        </h2>
        <span className="validation-pill amber">
          <AlertCircle size={15} />
          Ambiguous
        </span>
      </div>

      <dl className="metadata-list">
        <MetaRow label="Query analysis" value="Ambiguous - metric unresolved" tone="warning" />
        <MetaRow label="Candidate metrics" value={metrics} mono />
        <MetaRow label="Semantic confidence" value="0.42 (disambiguation required)" mono />
        <MetaRow label="Audit ID" value={askResult.query_id} mono />
      </dl>

      <div className="sql-status">
        <div className="sql-header plain">
          <span>
            <Code2 size={18} />
            SQL generation status
          </span>
        </div>
        <pre className="sql-placeholder">
-- No SQL generated until metric is resolved.
-- Select a metric to build deterministic query.
        </pre>
      </div>

      <div className="info-callout">
        Your selection will determine the metric, joins, time anchor and validation rules applied.
      </div>
    </aside>
  );
}

function BlockedPanel({ askResult }: { askResult: AskResponse }) {
  return (
    <aside className="trust-panel">
      <div className="panel-header">
        <h2>
          <Shield size={26} />
          Guard & audit layer
        </h2>
        <span className="validation-pill amber">
          <AlertCircle size={15} />
          rule triggered
        </span>
      </div>

      <dl className="metadata-list">
        <MetaRow label="Rule ID" value={askResult.safety?.rule_id ?? "SQL_GUARD_07"} mono />
        <MetaRow label="Reason" value={askResult.safety?.reason ?? "Potential data loss"} mono />
        <MetaRow label="Validation result" value="BLOCKED - 1 critical violation" tone="danger" />
        <MetaRow label="Query ID" value={askResult.query_id} mono />
        <MetaRow label="Latency" value="<1 ms (guard layer intercept)" mono />
      </dl>

      <div className="guard-log-heading">Guard log</div>
      <pre className="guard-log">{`/* GUARD LOG */
Rule: DROP_DETECT - severity: CRITICAL - action: ABORT
"DROP all claims" classified as malicious intent / data destruction
No SQL compiled - read-only policy enforced.`}</pre>
    </aside>
  );
}

function SqlBlock({ sql }: { sql: string }) {
  const lines = sql.split("\n");

  return (
    <div className="sql-status">
      <div className="sql-header">
        <span>
          <Code2 size={18} />
          Generated SQL (parameterised)
        </span>
        <button
          className="icon-button"
          disabled={!sql.trim()}
          onClick={() => navigator.clipboard.writeText(sql)}
          type="button"
        >
          <Copy size={16} />
          Copy
        </button>
      </div>
      <div className="sql-frame">
        <div className="line-numbers" aria-hidden="true">
          {lines.map((_, index) => (
            <span key={index}>{index + 1}</span>
          ))}
        </div>
        <pre className="sql-block">{sql}</pre>
      </div>
    </div>
  );
}

function MetaRow({
  label,
  mono = false,
  tone,
  value
}: {
  label: string;
  mono?: boolean;
  tone?: "success" | "warning" | "danger";
  value: string;
}) {
  return (
    <div className="metadata-row">
      <dt>{label}</dt>
      <dd className={`${mono ? "mono" : ""} ${tone ? `tone-${tone}` : ""}`}>{value}</dd>
    </div>
  );
}

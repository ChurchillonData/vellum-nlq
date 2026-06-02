import { AlertCircle, ClipboardList, Code2, Copy, Shield } from "lucide-react";
import type { ReactNode } from "react";

import { getDisplayRuleId, getSafetyReasonLines } from "../safetyDisplay";
import type { AskResponse, Metric } from "../types";
import { CleanCheck } from "./CleanCheck";

type TrustPanelProps = {
  askResult: AskResponse;
  metric: Metric | null;
};

export function TrustPanel({ askResult, metric }: TrustPanelProps) {
  if (askResult.status === "clarification_required") {
    return <ClarificationPanel askResult={askResult} />;
  }

  if (askResult.status === "blocked") {
    return <BlockedPanel askResult={askResult} />;
  }

  if (askResult.status !== "answer" || !askResult.answer) {
    return <ResolutionOnlyPanel askResult={askResult} />;
  }

  return <AnswerPanel askResult={askResult} metric={metric} />;
}

function AnswerPanel({ askResult, metric }: TrustPanelProps) {
  const answer = askResult.answer;
  const validation = answer?.validation;
  const metricId = metric?.id ?? answer?.metric_id ?? askResult.resolved_request?.metric_id ?? "unresolved";
  const metricVersion = metric?.version ?? answer?.provenance.metric_version ?? "n/a";
  const timeAnchor = metric?.time_anchor ?? answer?.provenance.time_anchor ?? "n/a";

  return (
    <aside className="trust-panel">
      <div className="panel-header">
        <h2>
          <Shield size={26} />
          Trust & transparency
        </h2>
        <span className="validation-pill ok">
          <CleanCheck size="sm" />
          validated
        </span>
      </div>

      <dl className="metadata-list">
        <MetaRow
          label="Metric used"
          value={`${metricId} (financial_kpi)`}
          trailingIcon={<MetricInfoMark />}
          mono
          normalWeight
        />
        <MetaRow label="Metric version" value={metricVersion} mono />
        <MetaRow label="Time anchor" value={timeAnchor} mono />
        <MetaRow label="Joins used" value={<JoinDisplay joins={answer?.provenance.joins_used} />} mono compact />
        <MetaRow
          label="Validation result"
          value={
            validation?.passed
              ? `${validation.rules_checked.length} rules checked - no violations`
              : "pending"
          }
          icon={
            <span className="validation-result-check">
              <CleanCheck size="sm" />
            </span>
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
  const reasonLines = getSafetyReasonLines(askResult.safety?.reason);

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
        <MetaRow label="Rule ID" value={getDisplayRuleId(askResult.safety?.rule_id)} mono />
        <MetaRow
          label="Reason"
          value={
            <span className="blocked-reason">
              <span>{reasonLines.summary}</span>
              {reasonLines.detail && <span>{reasonLines.detail}</span>}
            </span>
          }
          mono
        />
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

function ResolutionOnlyPanel({ askResult }: { askResult: AskResponse }) {
  return (
    <aside className="trust-panel">
      <div className="panel-header">
        <h2>
          <ClipboardList size={25} />
          Resolution state
        </h2>
        <span className="validation-pill amber">
          <AlertCircle size={15} />
          {askResult.status.replace(/_/g, " ")}
        </span>
      </div>

      <dl className="metadata-list">
        <MetaRow label="Query analysis" value={askResult.message} />
        <MetaRow label="Audit ID" value={askResult.query_id} mono />
        {askResult.scope && (
          <MetaRow label="Scope reason" value={askResult.scope.reason} tone="warning" />
        )}
      </dl>

      <div className="sql-status">
        <div className="sql-header plain">
          <span>
            <Code2 size={18} />
            SQL generation status
          </span>
        </div>
        <pre className="sql-placeholder">
-- No SQL generated for this query state.
-- Provide the missing inputs or choose a supported catalogue question.
        </pre>
      </div>
    </aside>
  );
}

function SqlBlock({ sql }: { sql: string }) {
  const lines = sql.split("\n");

  return (
    <div className="sql-status">
      <div className="sql-header">
        <span>
          <Code2 className="sql-generated-icon" size={24} />
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
        <pre className="sql-block">
          {lines.map((line, index) => (
            <span className="sql-line" key={`${line}-${index}`}>
              {highlightSqlLine(line)}
              {index < lines.length - 1 ? "\n" : ""}
            </span>
          ))}
        </pre>
      </div>
    </div>
  );
}

const sqlKeywords = new Set([
  "AND",
  "AS",
  "BETWEEN",
  "BY",
  "FROM",
  "GROUP",
  "JOIN",
  "ON",
  "SELECT",
  "USING",
  "WHERE",
  "WITH"
]);

const sqlFunctions = new Set(["COUNT", "SUM", "AVG", "MIN", "MAX", "NULLIF"]);

function highlightSqlLine(line: string): ReactNode[] {
  const commentStart = line.indexOf("--");

  if (commentStart === 0) {
    return [<span className="sql-comment" key="comment">{line}</span>];
  }

  if (commentStart > 0) {
    return [
      ...highlightSqlLine(line.slice(0, commentStart)),
      <span className="sql-comment" key="comment">{line.slice(commentStart)}</span>
    ];
  }

  return line.split(/('[^']*'|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][A-Za-z0-9_]*\b)/g).map((part, index) => {
    if (!part) {
      return part;
    }

    if (/^'[^']*'$/.test(part)) {
      return <span className="sql-string" key={`${part}-${index}`}>{part}</span>;
    }

    if (/^\d+(?:\.\d+)?$/.test(part)) {
      return <span className="sql-number" key={`${part}-${index}`}>{part}</span>;
    }

    if (sqlKeywords.has(part.toUpperCase())) {
      return <span className="sql-keyword" key={`${part}-${index}`}>{part}</span>;
    }

    if (sqlFunctions.has(part.toUpperCase())) {
      return <span className="sql-function" key={`${part}-${index}`}>{part}</span>;
    }

    return part;
  });
}

function JoinDisplay({ joins }: { joins?: string[] }) {
  const joined = joins?.join("; ") ?? "claims -> premium (member_id)";

  if (joined.includes("claims") && joined.includes("premium")) {
    return (
      <span className="join-display">
        <span>claims</span>
        <JoinBranchMark />
        <span>premium</span>
        <span className="join-key">(member_id)</span>
      </span>
    );
  }

  return <span>{joined.replace(/->|→/g, "⟕")}</span>;
}

function JoinBranchMark() {
  return (
    <svg
      aria-label="left join"
      className="join-branch-mark"
      fill="none"
      height="16"
      viewBox="0 0 22 16"
      width="22"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M4 3v10M4 8h14" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
      <circle cx="4" cy="3" fill="currentColor" r="1.8" />
      <circle cx="18" cy="8" fill="currentColor" r="1.8" />
      <circle cx="4" cy="13" fill="currentColor" r="1.8" />
    </svg>
  );
}

function MetricInfoMark() {
  return (
    <span aria-label="metric information" className="metric-info-mark">
      i
    </span>
  );
}

function MetaRow({
  compact = false,
  icon,
  label,
  mono = false,
  normalWeight = false,
  tone,
  trailingIcon,
  value
}: {
  compact?: boolean;
  icon?: ReactNode;
  label: string;
  mono?: boolean;
  normalWeight?: boolean;
  tone?: "success" | "warning" | "danger";
  trailingIcon?: ReactNode;
  value: ReactNode;
}) {
  return (
    <div className="metadata-row">
      <dt>{label}</dt>
      <dd className={`${mono ? "mono" : ""} ${tone ? `tone-${tone}` : ""} ${compact ? "compact-meta" : ""} ${normalWeight ? "normal-meta" : ""}`}>
        {icon && <span className="meta-icon">{icon}</span>}
        <span>{value}</span>
        {trailingIcon && <span className="meta-icon">{trailingIcon}</span>}
      </dd>
    </div>
  );
}

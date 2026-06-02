import { AlertTriangle, Shield } from "lucide-react";

import type { AskResponse, Metric } from "../../types";
import { CleanCheck } from "../CleanCheck";
import { JoinDisplay } from "./JoinDisplay";
import { MetaRow } from "./MetaRow";
import { MetricInfoMark } from "./MetricInfoMark";
import { SqlBlock } from "./SqlBlock";
import { ValidationResult, ValidationStatusIcon } from "./ValidationResult";

export function AnswerTrustPanel({
  askResult,
  metric
}: {
  askResult: AskResponse;
  metric: Metric | null;
}) {
  const answer = askResult.answer;
  const validation = answer?.validation;
  const metricId =
    answer?.metric_id ?? askResult.resolved_request?.metric_id ?? metric?.id ?? "unresolved";
  const metricVersion = answer?.provenance.metric_version ?? metric?.version ?? "n/a";
  const timeAnchor = answer?.provenance.time_anchor ?? metric?.time_anchor ?? "n/a";
  const queryId = answer?.query_id ?? askResult.query_id;
  const latency = answer?.latency ? formatLatency(answer.latency) : "pending";
  const validationPassed = validation?.passed !== false;

  return (
    <aside className="trust-panel">
      <div className="panel-header">
        <h2>
          <Shield size={26} />
          Trust & transparency
        </h2>
        <span className={`validation-pill ${validationPassed ? "ok" : "danger"}`}>
          {validationPassed ? <CleanCheck size="sm" /> : <AlertTriangle size={15} />}
          {validationPassed ? "validated" : "validation failed"}
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
        <MetaRow
          label="Joins used"
          value={<JoinDisplay joins={answer?.provenance.joins_used} />}
          mono
          compact
        />
        <MetaRow
          label="Validation result"
          value={<ValidationResult validation={validation} />}
          icon={<ValidationStatusIcon validation={validation} />}
          tone={validationPassed ? "success" : "danger"}
        />
        <MetaRow label="Audit / Query ID" value={queryId} mono />
        <MetaRow label="Latency" value={latency} mono />
      </dl>

      {validationPassed ? (
        <SqlBlock
          compactSql={answer?.compact_sql}
          sql={answer?.sql ?? "-- No SQL generated for this state."}
        />
      ) : (
        <UnsafeSqlNotice />
      )}
    </aside>
  );
}

function UnsafeSqlNotice() {
  return (
    <div className="unsafe-sql-notice" role="status">
      <AlertTriangle size={18} />
      <span>Generated SQL hidden because validation failed.</span>
    </div>
  );
}

function formatLatency(latency: {
  execution_ms?: number | null;
  planning_ms: number;
  total_ms: number;
}) {
  const planning = `${latency.planning_ms.toFixed(2)} ms planning`;
  const total = `${latency.total_ms.toFixed(2)} ms total`;

  if (latency.execution_ms === null || latency.execution_ms === undefined) {
    return `${planning} - ${total}`;
  }

  return `${latency.execution_ms.toFixed(2)} ms execution - ${planning} - ${total}`;
}

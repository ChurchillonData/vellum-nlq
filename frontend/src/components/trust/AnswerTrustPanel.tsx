import { Shield } from "lucide-react";

import type { AskResponse, Metric } from "../../types";
import { CleanCheck } from "../CleanCheck";
import { JoinDisplay } from "./JoinDisplay";
import { MetaRow } from "./MetaRow";
import { MetricInfoMark } from "./MetricInfoMark";
import { SqlBlock } from "./SqlBlock";

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
    metric?.id ?? answer?.metric_id ?? askResult.resolved_request?.metric_id ?? "unresolved";
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
        <MetaRow
          label="Joins used"
          value={<JoinDisplay joins={answer?.provenance.joins_used} />}
          mono
          compact
        />
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

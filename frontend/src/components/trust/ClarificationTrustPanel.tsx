import { AlertCircle, ClipboardList, Code2 } from "lucide-react";

import type { AskResponse } from "../../types";
import { MetaRow } from "./MetaRow";

export function ClarificationTrustPanel({ askResult }: { askResult: AskResponse }) {
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

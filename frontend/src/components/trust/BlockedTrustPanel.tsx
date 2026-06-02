import { AlertCircle, Shield } from "lucide-react";

import { getDisplayRuleId, getSafetyReasonLines } from "../../safetyDisplay";
import type { AskResponse } from "../../types";
import { MetaRow } from "./MetaRow";

export function BlockedTrustPanel({ askResult }: { askResult: AskResponse }) {
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

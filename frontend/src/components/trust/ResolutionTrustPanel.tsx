import { AlertCircle, ClipboardList, Code2 } from "lucide-react";

import type { AskResponse } from "../../types";
import { MetaRow } from "./MetaRow";

export function ResolutionTrustPanel({ askResult }: { askResult: AskResponse }) {
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

import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Copy,
  Database,
  FileCode2,
  Search,
  ShieldCheck
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { fetchAuditRecord } from "../api";
import type { AuditRecord, Metric } from "../types";
import { BackendTools } from "./BackendTools";

type AuditExplorerProps = {
  latestQueryId: string;
  metrics: Metric[];
};

export function AuditExplorer({ latestQueryId, metrics }: AuditExplorerProps) {
  const [queryId, setQueryId] = useState(latestQueryId);
  const [record, setRecord] = useState<AuditRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setQueryId(latestQueryId);
  }, [latestQueryId]);

  useEffect(() => {
    if (latestQueryId.startsWith("q_")) {
      lookupAudit(latestQueryId);
    }
  }, [latestQueryId]);

  async function lookupAudit(nextQueryId = queryId) {
    const trimmedQueryId = nextQueryId.trim();
    if (!trimmedQueryId) {
      setError("Enter a query ID to inspect.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const nextRecord = await fetchAuditRecord(trimmedQueryId);
      setRecord(nextRecord);
    } catch {
      setRecord(null);
      setError("No audit record found for that query ID on the current backend.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    lookupAudit();
  }

  return (
    <main className="audit-page">
      <section className="audit-hero">
        <div>
          <p className="eyebrow">Audit trace</p>
          <h1>Every answer leaves a trail.</h1>
          <p>
            Inspect the exact request, metric resolution, generated SQL, validation
            rules, and execution summary for a Vellum query.
          </p>
        </div>

        <form className="audit-search-panel" onSubmit={handleSubmit}>
          <label htmlFor="audit-query-id">Query ID</label>
          <div className="audit-search-row">
            <Search size={20} />
            <input
              id="audit-query-id"
              onChange={(event) => setQueryId(event.target.value)}
              placeholder="q_..."
              value={queryId}
            />
            <button disabled={isLoading} type="submit">
              {isLoading ? "Loading" : "Lookup"}
            </button>
          </div>
          {latestQueryId && (
            <button
              className="audit-latest-button"
              onClick={() => lookupAudit(latestQueryId)}
              type="button"
            >
              Use latest query
            </button>
          )}
        </form>
      </section>

      <BackendTools metrics={metrics} />

      {error && <div className="audit-message error">{error}</div>}

      {record ? (
        <AuditRecordView record={record} />
      ) : (
        !error && (
          <section className="audit-empty">
            <ClipboardList size={30} />
            <h2>No audit record loaded</h2>
            <p>Run a question in the Ask workspace, then open Audit to inspect it.</p>
          </section>
        )
      )}
    </main>
  );
}

function AuditRecordView({ record }: { record: AuditRecord }) {
  const validationPassed = record.validation?.passed;
  const resultShape = record.provenance?.result_shape;

  return (
    <section className="audit-grid">
      <div className="audit-summary-card">
        <div className="audit-card-header">
          <span className="audit-icon blue">
            <ClipboardList size={22} />
          </span>
          <div>
            <p className="eyebrow">Trace summary</p>
            <h2>{record.query_id}</h2>
          </div>
          <StatusPill status={record.status ?? record.event_type} />
        </div>

        <div className="audit-facts">
          <Fact label="Event" value={record.event_type} />
          <Fact label="Created" value={formatDate(record.created_at)} />
          <Fact label="Metric" value={record.metric_id ?? "not resolved"} />
          <Fact label="Status" value={record.status ?? "recorded"} />
          <Fact label="Execution" value={record.execution?.mode ?? "not executed"} />
          <Fact label="Rows" value={formatValue(record.execution?.row_count ?? "n/a")} />
        </div>

        {record.execution?.answer && (
          <div className="audit-answer">
            <strong>Answer summary</strong>
            <p>{record.execution.answer}</p>
          </div>
        )}
      </div>

      <div className="audit-panel">
        <PanelTitle icon={<ShieldCheck size={20} />} title="Validation" />
        {record.validation ? (
          <>
            <div className={`audit-validation ${validationPassed ? "passed" : "failed"}`}>
              {validationPassed ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
              {validationPassed ? "Passed" : "Failed"}
            </div>
            <div className="audit-chip-row">
              {record.validation.rules_checked.map((rule) => (
                <span key={rule}>{rule}</span>
              ))}
            </div>
            {record.validation.rejections.length > 0 && (
              <JsonBlock title="Rejections" value={record.validation.rejections} />
            )}
          </>
        ) : (
          <p className="audit-muted">No SQL validation was needed for this state.</p>
        )}
      </div>

      <div className="audit-panel">
        <PanelTitle icon={<Database size={20} />} title="Resolved request" />
        <JsonBlock title="Request" value={record.request ?? {}} />
        <JsonBlock title="Resolved" value={record.resolved_request ?? {}} />
      </div>

      <div className="audit-panel">
        <PanelTitle icon={<FileCode2 size={20} />} title="Generated SQL" />
        {record.sql ? (
          <div className="audit-sql-card">
            <button
              className="audit-copy-button"
              onClick={() => navigator.clipboard.writeText(record.sql ?? "")}
              type="button"
            >
              <Copy size={15} />
              Copy
            </button>
            <pre>{record.sql}</pre>
          </div>
        ) : (
          <p className="audit-muted">No SQL was compiled for this query state.</p>
        )}
      </div>

      <div className="audit-panel wide">
        <PanelTitle icon={<ShieldCheck size={20} />} title="Provenance" />
        <div className="audit-facts compact">
          <Fact label="Metric version" value={record.provenance?.metric_version ?? "n/a"} />
          <Fact label="Time anchor" value={record.provenance?.time_anchor ?? "n/a"} />
          <Fact label="Grain" value={resultShape?.grain ?? "n/a"} />
          <Fact label="Max rows" value={formatValue(resultShape?.max_rows ?? "n/a")} />
        </div>
        <JsonBlock title="Tables, joins and parameters" value={provenanceDetails(record)} />
      </div>

      {(record.safety || record.scope || record.availability || record.candidates?.length) && (
        <div className="audit-panel wide">
          <PanelTitle icon={<AlertTriangle size={20} />} title="Resolution notes" />
          {record.safety && <JsonBlock title="Safety" value={record.safety} />}
          {record.scope && <JsonBlock title="Scope" value={record.scope} />}
          {record.availability && (
            <JsonBlock title="Availability" value={record.availability} />
          )}
          {record.candidates?.length ? (
            <JsonBlock title="Candidates" value={record.candidates} />
          ) : null}
        </div>
      )}
    </section>
  );
}

function StatusPill({ status }: { status: string }) {
  const tone = useMemo(() => {
    if (status === "answer") {
      return "ok";
    }
    if (status === "blocked" || status === "out_of_scope") {
      return "danger";
    }
    return "neutral";
  }, [status]);

  return <span className={`audit-status ${tone}`}>{status.replace(/_/g, " ")}</span>;
}

function PanelTitle({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="audit-panel-title">
      {icon}
      <h3>{title}</h3>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="audit-json-block">
      <span>{title}</span>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </div>
  );
}

function provenanceDetails(record: AuditRecord) {
  return {
    tables_used: record.provenance?.tables_used ?? [],
    joins_used: record.provenance?.joins_used ?? [],
    parameters: record.parameters ?? {},
    formula: record.provenance?.formula ?? null,
    result_shape: record.provenance?.result_shape ?? null
  };
}

function formatDate(value?: string) {
  if (!value) {
    return "n/a";
  }

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function formatValue(value: unknown) {
  if (value === null || value === undefined) {
    return "n/a";
  }
  return String(value);
}

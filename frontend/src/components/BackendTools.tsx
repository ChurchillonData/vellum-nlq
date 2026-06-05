import { Play, Search, TerminalSquare } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import { executeQuery, previewQuery, resolveQuery } from "../api";
import type {
  AnalyticsRequestPayload,
  Metric,
  QueryExecuteResponse,
  QueryPreviewResponse,
  QueryResolveResponse
} from "../types";

type BackendToolsProps = {
  metrics: Metric[];
};

type ToolResult =
  | { type: "resolve"; value: QueryResolveResponse }
  | { type: "preview"; value: QueryPreviewResponse }
  | { type: "execute"; value: QueryExecuteResponse };

export function BackendTools({ metrics }: BackendToolsProps) {
  const defaultMetric = metrics.find((metric) => metric.id === "loss_ratio") ?? metrics[0];
  const [question, setQuestion] = useState(
    "What was loss ratio for the Comprehensive plan tier in Q1 2026?"
  );
  const [metricId, setMetricId] = useState(defaultMetric?.id ?? "loss_ratio");
  const [startDate, setStartDate] = useState("2026-01-01");
  const [endDate, setEndDate] = useState("2026-03-31");
  const [planTier, setPlanTier] = useState("Comprehensive");
  const [groupBy, setGroupBy] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ToolResult | null>(null);
  const activeMetric = useMemo(
    () => metrics.find((metric) => metric.id === metricId) ?? null,
    [metricId, metrics]
  );
  const metricOptions = metrics.length ? metrics : [{ id: metricId, label: metricId }];

  async function runTool(type: ToolResult["type"]) {
    setIsRunning(true);
    setError(null);

    try {
      if (type === "resolve") {
        const value = await resolveQuery({
          end_date: endDate,
          group_by: parseGroupBy(groupBy),
          plan_tier: cleanOptional(planTier),
          question,
          start_date: startDate
        });
        setResult({ type, value });
        return;
      }

      const payload: AnalyticsRequestPayload = {
        end_date: endDate,
        group_by: parseGroupBy(groupBy),
        metric_id: metricId,
        plan_tier: cleanOptional(planTier),
        start_date: startDate
      };

      if (type === "preview") {
        setResult({ type, value: await previewQuery(payload) });
        return;
      }

      setResult({ type, value: await executeQuery(payload) });
    } catch (toolError) {
      setResult(null);
      setError(toolError instanceof Error ? toolError.message : "Backend tool request failed.");
    } finally {
      setIsRunning(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runTool("preview");
  }

  return (
    <section className="backend-tools">
      <div className="backend-tools-header">
        <div>
          <p className="eyebrow">Backend route wiring</p>
          <h2>Resolve, preview, and execute from the UI.</h2>
          <p>
            This panel calls the development endpoints directly while the Ask page
            remains the main product flow.
          </p>
        </div>
        <span>{activeMetric?.version ?? "Vellum 2.5"}</span>
      </div>

      <form className="backend-tools-form" onSubmit={handleSubmit}>
        <label>
          Question
          <input value={question} onChange={(event) => setQuestion(event.target.value)} />
        </label>
        <label>
          Metric
          <select value={metricId} onChange={(event) => setMetricId(event.target.value)}>
            {metricOptions.map((metric) => (
              <option key={metric.id} value={metric.id}>
                {metric.label} ({metric.id})
              </option>
            ))}
          </select>
        </label>
        <label>
          Start date
          <input value={startDate} onChange={(event) => setStartDate(event.target.value)} type="date" />
        </label>
        <label>
          End date
          <input value={endDate} onChange={(event) => setEndDate(event.target.value)} type="date" />
        </label>
        <label>
          Plan tier
          <input value={planTier} onChange={(event) => setPlanTier(event.target.value)} />
        </label>
        <label>
          Group by
          <input
            placeholder="consultant_specialty"
            value={groupBy}
            onChange={(event) => setGroupBy(event.target.value)}
          />
        </label>
      </form>

      <div className="backend-tool-actions">
        <button disabled={isRunning} onClick={() => void runTool("resolve")} type="button">
          <Search size={16} />
          Resolve
        </button>
        <button disabled={isRunning} onClick={() => void runTool("preview")} type="button">
          <TerminalSquare size={16} />
          Preview SQL
        </button>
        <button disabled={isRunning} onClick={() => void runTool("execute")} type="button">
          <Play size={16} />
          Execute
        </button>
      </div>

      {error ? <div className="backend-tool-error">{error}</div> : null}
      {result ? <BackendToolResult result={result} /> : null}
    </section>
  );
}

function BackendToolResult({ result }: { result: ToolResult }) {
  if (result.type === "resolve") {
    return (
      <div className="backend-tool-result">
        <strong>Resolution: {result.value.status}</strong>
        <p>{result.value.message}</p>
        <JsonPreview value={result.value.resolved_request ?? result.value.candidates} />
      </div>
    );
  }

  return (
    <div className="backend-tool-result">
      <strong>
        {result.type === "preview" ? "Preview" : "Execution"}: {result.value.metric_id}
      </strong>
      {"answer" in result.value ? <p>{result.value.answer}</p> : null}
      <dl className="backend-tool-facts">
        <div>
          <dt>Query ID</dt>
          <dd>{result.value.query_id}</dd>
        </div>
        <div>
          <dt>Validation</dt>
          <dd>{result.value.validation.passed ? "passed" : "failed"}</dd>
        </div>
        <div>
          <dt>Rows</dt>
          <dd>{"row_count" in result.value ? result.value.row_count : "preview"}</dd>
        </div>
      </dl>
      <pre className="backend-tool-sql">{result.value.compact_sql}</pre>
    </div>
  );
}

function JsonPreview({ value }: { value: unknown }) {
  return <pre className="backend-tool-json">{JSON.stringify(value, null, 2)}</pre>;
}

function cleanOptional(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function parseGroupBy(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

import { useEffect, useMemo, useState } from "react";

import { askQuestion, fetchAskExamples, fetchHealth, fetchMetrics } from "./api";
import { AskWorkspace } from "./components/AskWorkspace";
import { AuditExplorer } from "./components/AuditExplorer";
import { CatalogueExplorer } from "./components/CatalogueExplorer";
import { TopBar } from "./components/TopBar";
import type { AskExample, AskRequestPayload, AskResponse, HealthResponse, Metric } from "./types";

type ActiveView = "ask" | "catalogue" | "audit";

export default function App() {
  const [activeView, setActiveView] = useState<ActiveView>("ask");
  const [question, setQuestion] = useState("");
  const [askResult, setAskResult] = useState<AskResponse | null>(null);
  const [askExamples, setAskExamples] = useState<AskExample[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => {
        setHealth({ catalogue: "health-uk", status: "offline" });
      });
  }, []);

  useEffect(() => {
    fetchMetrics()
      .then((response) => setMetrics(response.metrics))
      .catch(() => {
        setMetrics([]);
        setNotice("Backend API is not connected. Start the API to load catalogue data.");
      });
  }, []);

  useEffect(() => {
    fetchAskExamples()
      .then((response) => setAskExamples(response.examples))
      .catch(() => {
        setAskExamples([]);
        setNotice("Backend API is not connected. Start the API to load demo examples.");
      });
  }, []);

  const selectedMetric = useMemo(() => {
    const metricId = askResult?.answer?.metric_id ?? askResult?.resolved_request?.metric_id;
    return metrics.find((metric) => metric.id === metricId) ?? null;
  }, [askResult, metrics]);

  async function runQuestion(nextQuestion = question, overrides: Partial<AskRequestPayload> = {}) {
    const trimmedQuestion = nextQuestion.trim();
    if (!trimmedQuestion) {
      setNotice("Enter a question before running the ask flow.");
      return;
    }

    const payload: AskRequestPayload = { question: trimmedQuestion, ...overrides };
    setQuestion(payload.question);
    setIsRunning(true);
    setNotice(null);

    try {
      const response = await askQuestion(payload);
      setAskResult(response);
    } catch {
      setAskResult(null);
      setNotice("Backend API is not connected. No answer was generated.");
    } finally {
      setIsRunning(false);
    }
  }

  function runExample(example: AskExample) {
    runQuestion(example.question, {
      end_date: example.end_date,
      group_by: example.group_by,
      plan_tier: example.plan_tier,
      start_date: example.start_date
    });
  }

  return (
    <div className="app-shell">
      <TopBar activeView={activeView} health={health} onChangeView={setActiveView} />

      {activeView === "ask" && (
        <AskWorkspace
          askResult={askResult}
          askExamples={askExamples}
          isRunning={isRunning}
          metric={selectedMetric}
          notice={notice}
          onQuestionChange={setQuestion}
          onRun={runQuestion}
          onRunExample={runExample}
          question={question}
        />
      )}

      {activeView === "catalogue" && <CatalogueExplorer metrics={metrics} />}

      {activeView === "audit" && <AuditExplorer latestQueryId={askResult?.query_id ?? ""} />}
    </div>
  );
}

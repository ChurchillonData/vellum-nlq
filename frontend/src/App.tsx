import { useEffect, useMemo, useState } from "react";

import { askQuestion, fetchAskExamples, fetchHealth, fetchMetrics } from "./api";
import { AskWorkspace } from "./components/AskWorkspace";
import { AuditExplorer } from "./components/AuditExplorer";
import { CatalogueExplorer } from "./components/CatalogueExplorer";
import { TopBar } from "./components/TopBar";
import {
  demoAskExamples,
  demoAskResponse,
  demoMetrics,
  demoQuestions,
  getDemoAskResponse
} from "./demoData";
import type { AskExample, AskRequestPayload, AskResponse, HealthResponse, Metric } from "./types";

type ActiveView = "ask" | "catalogue" | "audit";

export default function App() {
  const [activeView, setActiveView] = useState<ActiveView>("ask");
  const [question, setQuestion] = useState(demoQuestions[0]);
  const [askResult, setAskResult] = useState<AskResponse>(demoAskResponse);
  const [askExamples, setAskExamples] = useState<AskExample[]>(demoAskExamples);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>(demoMetrics);
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
        setNotice("Backend API is not connected. Showing demo catalogue data.");
      });
  }, []);

  useEffect(() => {
    fetchAskExamples()
      .then((response) => setAskExamples(response.examples))
      .catch(() => {
        setNotice("Backend API is not connected. Showing saved demo examples.");
      });
  }, []);

  const selectedMetric = useMemo(() => {
    const metricId =
      askResult.answer?.metric_id ?? askResult.resolved_request?.metric_id ?? "loss_ratio";
    return metrics.find((metric) => metric.id === metricId) ?? metrics[0];
  }, [askResult, metrics]);

  async function runQuestion(nextQuestion = question, overrides: Partial<AskRequestPayload> = {}) {
    const payload: AskRequestPayload = { question: nextQuestion, ...overrides };
    setQuestion(payload.question);
    setIsRunning(true);
    setNotice(null);

    try {
      const response = await askQuestion(payload);
      setAskResult(response);
    } catch {
      setNotice("Backend API is not connected. Showing the saved demo answer.");
      setAskResult(getDemoAskResponse(payload.question));
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

      {activeView === "audit" && <AuditExplorer latestQueryId={askResult.query_id} />}
    </div>
  );
}

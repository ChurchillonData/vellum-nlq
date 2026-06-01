import { useEffect, useMemo, useState } from "react";

import { askQuestion, fetchAskExamples, fetchMetrics } from "./api";
import { AskWorkspace } from "./components/AskWorkspace";
import { CatalogueExplorer } from "./components/CatalogueExplorer";
import { TopBar } from "./components/TopBar";
import {
  demoAskExamples,
  demoAskResponse,
  demoMetrics,
  demoQuestions,
  getDemoAskResponse
} from "./demoData";
import type { AskExample, AskRequestPayload, AskResponse, Metric } from "./types";

type ActiveView = "ask" | "catalogue" | "audit";

export default function App() {
  const [activeView, setActiveView] = useState<ActiveView>("ask");
  const [question, setQuestion] = useState(demoQuestions[0]);
  const [askResult, setAskResult] = useState<AskResponse>(demoAskResponse);
  const [askExamples, setAskExamples] = useState<AskExample[]>(demoAskExamples);
  const [metrics, setMetrics] = useState<Metric[]>(demoMetrics);
  const [isRunning, setIsRunning] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

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
      <TopBar activeView={activeView} onChangeView={setActiveView} />

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

      {activeView === "audit" && (
        <main className="audit-page">
          <section>
            <p className="eyebrow">Audit trace</p>
            <h1>Query provenance is built into every answer.</h1>
            <p>
              Use an answer query ID from the Ask workspace to inspect the backend
              audit payload. The frontend shell is ready for the audit browser view
              once the demo needs it.
            </p>
          </section>
        </main>
      )}
    </div>
  );
}

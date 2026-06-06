import { useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";

import { askQuestion, fetchAskExamples, fetchHealth, fetchMappingCoverage, fetchMetrics } from "./api";
import { AskWorkspace } from "./components/AskWorkspace";
import { AuditExplorer } from "./components/AuditExplorer";
import { CatalogueExplorer } from "./components/CatalogueExplorer";
import { TopBar } from "./components/TopBar";
import type {
  AskExample,
  AskRequestPayload,
  AskResponse,
  HealthResponse,
  MappingCoverageResponse,
  Metric
} from "./types";
import {
  ASK_ANSWER_COMPLETION_DELAY_MS,
  ASK_STATE_COMPLETION_DELAY_MS
} from "./uiTiming";

type ActiveView = "ask" | "catalogue" | "audit";

export default function App() {
  const [activeView, setActiveView] = useState<ActiveView>("ask");
  const [question, setQuestion] = useState("");
  const [askResult, setAskResult] = useState<AskResponse | null>(null);
  const [askExamples, setAskExamples] = useState<AskExample[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [mappingCoverage, setMappingCoverage] = useState<MappingCoverageResponse | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const runCompletionTimer = useRef<number | undefined>(undefined);

  useEffect(() => {
    return () => clearRunCompletionTimer(runCompletionTimer);
  }, []);

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

  useEffect(() => {
    fetchMappingCoverage("example-insurer")
      .then(setMappingCoverage)
      .catch(() => setMappingCoverage(null));
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
    clearRunCompletionTimer(runCompletionTimer);
    setIsRunning(true);
    setNotice(null);

    try {
      const response = await askQuestion(payload);
      setAskResult(response);
      finishRunAfterVisibleWork(response);
    } catch (error) {
      setAskResult(null);
      setNotice(
        error instanceof Error
          ? error.message
          : "Backend API is not connected. No answer was generated."
      );
      setIsRunning(false);
    }
  }

  function finishRunAfterVisibleWork(response: AskResponse) {
    const completionDelay = getRunCompletionDelay(response);
    runCompletionTimer.current = window.setTimeout(() => {
      setIsRunning(false);
    }, completionDelay);
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

      {activeView === "catalogue" && (
        <CatalogueExplorer mappingCoverage={mappingCoverage} metrics={metrics} />
      )}

      {activeView === "audit" && (
        <AuditExplorer latestQueryId={askResult?.query_id ?? ""} metrics={metrics} />
      )}
    </div>
  );
}

function clearRunCompletionTimer(timer: MutableRefObject<number | undefined>) {
  if (timer.current !== undefined) {
    window.clearTimeout(timer.current);
    timer.current = undefined;
  }
}

function getRunCompletionDelay(response: AskResponse) {
  if (prefersReducedMotion()) {
    return 0;
  }

  if (response.status === "answer" && response.answer) {
    return ASK_ANSWER_COMPLETION_DELAY_MS;
  }

  return ASK_STATE_COMPLETION_DELAY_MS;
}

function prefersReducedMotion() {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

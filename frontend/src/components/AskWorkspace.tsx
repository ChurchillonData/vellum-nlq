import { AlertTriangle, BarChart3, HelpCircle, Play, ShieldCheck } from "lucide-react";

import type { AskResponse, Metric } from "../types";
import { ResultTable } from "./ResultTable";
import { TrustPanel } from "./TrustPanel";

type AskWorkspaceProps = {
  askResult: AskResponse;
  demoQuestions: string[];
  isRunning: boolean;
  metric: Metric;
  notice: string | null;
  onQuestionChange: (question: string) => void;
  onRun: (question?: string) => void;
  question: string;
};

export function AskWorkspace({
  askResult,
  demoQuestions,
  isRunning,
  metric,
  notice,
  onQuestionChange,
  onRun,
  question
}: AskWorkspaceProps) {
  const stateClass = `query-input ${askResult.status}`;

  return (
    <main className="ask-layout">
      <section className="ask-main">
        {notice && <div className="notice">{notice}</div>}

        <div className="query-area">
          <label htmlFor="question">Natural language query</label>
          <div className="query-row">
            <textarea
              className={stateClass}
              id="question"
              onChange={(event) => onQuestionChange(event.target.value)}
              value={question}
            />
            <button
              className="run-button"
              disabled={isRunning}
              onClick={() => onRun()}
              type="button"
            >
              <Play size={17} />
              {isRunning ? "Running" : "Run"}
            </button>
          </div>
          <div className="suggestion-row">
            {demoQuestions.slice(1, 5).map((item) => (
              <button
                className="suggestion"
                key={item}
                onClick={() => onRun(item)}
                type="button"
              >
                <BarChart3 size={15} />
                {item}
              </button>
            ))}
          </div>
        </div>

        <WorkspaceState askResult={askResult} metric={metric} />
      </section>

      <TrustPanel askResult={askResult} metric={metric} />
    </main>
  );
}

function WorkspaceState({
  askResult,
  metric
}: {
  askResult: AskResponse;
  metric: Metric;
}) {
  if (askResult.status === "answer" && askResult.answer) {
    return (
      <section className="result-section">
        <p className="section-label">Result summary</p>
        <div className="answer-card">
          <div className="answer-icon success">
            <ShieldCheck size={24} />
          </div>
          <div className="answer-content">
            <p className="answer-text">{askResult.answer.answer}</p>
            <ResultTable rows={askResult.answer.rows} />
            <p className="row-note">
              {askResult.answer.row_count} row
              {askResult.answer.row_count === 1 ? "" : "s"} · {metric.formula.expression}
            </p>
          </div>
        </div>
      </section>
    );
  }

  if (askResult.status === "clarification_required") {
    return (
      <section className="state-card amber">
        <div className="state-heading">
          <HelpCircle size={22} />
          Clarification needed
        </div>
        <p>{askResult.message}</p>
        <div className="candidate-grid">
          {askResult.candidates.map((candidate) => (
            <button className="candidate-card" key={candidate.metric_id} type="button">
              <strong>{candidate.label}</strong>
              <span>{candidate.reason}</span>
            </button>
          ))}
        </div>
      </section>
    );
  }

  if (askResult.status === "blocked") {
    return (
      <section className="state-card red">
        <div className="state-heading">
          <AlertTriangle size={22} />
          Request refused
        </div>
        <p>{askResult.message}</p>
        <code>{askResult.safety?.rule_id} · {askResult.safety?.reason}</code>
      </section>
    );
  }

  return (
    <section className="state-card neutral">
      <div className="state-heading">
        <HelpCircle size={22} />
        More information needed
      </div>
      <p>{askResult.message}</p>
    </section>
  );
}

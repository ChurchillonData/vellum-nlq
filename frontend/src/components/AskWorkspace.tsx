import {
  AlertTriangle,
  BarChart3,
  BotMessageSquare,
  CircleSlash,
  HelpCircle,
  Play,
  ShieldAlert,
  Sparkles,
  Users,
  WalletCards
} from "lucide-react";
import { useState } from "react";

import { getDisplayRuleId, getSafetyReasonLines } from "../safetyDisplay";
import type { AskExample, AskRequestPayload, AskResponse, Candidate, Metric } from "../types";
import { CleanCheck } from "./CleanCheck";
import { ResultTable } from "./ResultTable";
import { TrustPanel } from "./TrustPanel";

type AskWorkspaceProps = {
  askResult: AskResponse;
  askExamples: AskExample[];
  isRunning: boolean;
  metric: Metric;
  notice: string | null;
  onQuestionChange: (question: string) => void;
  onRun: (question?: string, overrides?: Partial<AskRequestPayload>) => void;
  onRunExample: (example: AskExample) => void;
  question: string;
};

export function AskWorkspace({
  askResult,
  askExamples,
  isRunning,
  metric,
  notice,
  onQuestionChange,
  onRun,
  onRunExample,
  question
}: AskWorkspaceProps) {
  const isBlocked = askResult.status === "blocked";
  const isClarifying = askResult.status === "clarification_required";
  const [showExamples, setShowExamples] = useState(false);
  const actionLabel = isBlocked ? "Blocked" : isClarifying ? "Clarify" : "Run";
  const ActionIcon = isBlocked ? CircleSlash : isClarifying ? Sparkles : Play;
  const planTierExample =
    askExamples.find((example) => example.id === "answer_loss_ratio_by_plan_tier") ??
    askExamples.find((example) => example.expected_status === "answer");
  const clarificationDefaults = getClarificationDefaults(askResult);
  const extraExamples = askExamples.slice(2);

  return (
    <main className="ask-layout">
      <section className="ask-main">
        {notice && <div className="notice">{notice}</div>}

        <div className="query-area">
          <label htmlFor="question">
            {isBlocked ? "Restricted action" : "Natural language query"}
          </label>
          <div className="query-row">
            <div className={`query-box ${askResult.status}`}>
              <BotMessageSquare size={27} />
              <textarea
                id="question"
                onChange={(event) => onQuestionChange(event.target.value)}
                value={question}
              />
            </div>
            <button
              className={isBlocked ? "run-button blocked" : "run-button"}
              disabled={isRunning || isBlocked}
              onClick={() => onRun()}
              type="button"
            >
              <ActionIcon size={18} />
              {isRunning ? "Running" : actionLabel}
            </button>
          </div>

          {!isBlocked && (
            <>
              <div className="suggestion-row">
                <button
                  className="suggestion"
                  onClick={() => {
                    if (planTierExample) {
                      onRunExample(planTierExample);
                    }
                  }}
                  type="button"
                >
                  <BarChart3 size={16} />
                  loss ratio by plan tier
                </button>
                <button
                  className="suggestion"
                  onClick={() =>
                    onRun("Show claim severity for the Comprehensive plan tier in Q1 2026.")
                  }
                  type="button"
                >
                  <Users size={16} />
                  average claim amount per member
                </button>
                <button
                  aria-expanded={showExamples}
                  className="suggestion"
                  onClick={() => setShowExamples((isOpen) => !isOpen)}
                  type="button"
                >
                  <span className="suggestion-plus">{showExamples ? "-" : "+"}</span>
                  More examples
                </button>
              </div>

              {showExamples && (
                <div className="more-examples">
                  {extraExamples.map((item) => (
                    <button
                      className="example-option"
                      key={item.id}
                      onClick={() => {
                        setShowExamples(false);
                        onRunExample(item);
                      }}
                      type="button"
                    >
                      <span>{item.label}</span>
                      <small>{item.question}</small>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <WorkspaceState
          askResult={askResult}
          metric={metric}
          onSelectCandidate={(candidate) =>
            onRun(question, {
              ...clarificationDefaults,
              metric_id: candidate.metric_id
            })
          }
        />
      </section>

      <TrustPanel askResult={askResult} metric={metric} />
    </main>
  );
}

function WorkspaceState({
  askResult,
  metric,
  onSelectCandidate
}: {
  askResult: AskResponse;
  metric: Metric;
  onSelectCandidate: (candidate: Candidate) => void;
}) {
  if (askResult.status === "answer" && askResult.answer) {
    return (
      <section className="result-section">
        <p className="section-label">Result summary</p>
        <div className="answer-card">
          <div className="answer-icon success">
            <CleanCheck size="lg" />
          </div>
          <div className="answer-content">
            <p className="answer-text">
              <HighlightedAnswer text={askResult.answer.answer} />
            </p>
            <ResultTable rows={askResult.answer.rows} />
            <p className="row-note">
              {askResult.answer.row_count} row
              {askResult.answer.row_count === 1 ? "" : "s"} - based on{" "}
              {metric.id === "loss_ratio" ? "incurred claims / earned premium" : metric.formula.expression}
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
          <HelpCircle size={25} />
          Clarification needed
        </div>
        <p>{askResult.message}</p>
        <div className="candidate-grid">
          {askResult.candidates.map((candidate, index) => (
            <button
              className="candidate-card"
              key={candidate.metric_id}
              onClick={() => onSelectCandidate(candidate)}
              type="button"
            >
              <span className="candidate-icon">
                {index === 1 ? (
                  <WalletCards size={24} />
                ) : index === 2 ? (
                  <Users size={24} />
                ) : (
                  <BarChart3 size={24} />
                )}
              </span>
              <strong>{candidate.label}</strong>
              <span>{candidate.reason}</span>
            </button>
          ))}
        </div>
        <div className="state-footnote">
          After selection, Vellum will generate validated SQL and full provenance.
        </div>
      </section>
    );
  }

  if (askResult.status === "blocked") {
    const reasonLines = getSafetyReasonLines(askResult.safety?.reason);

    return (
      <section className="state-card red">
        <div className="state-heading">
          <AlertTriangle size={25} />
          Request refused
        </div>
        <p>{askResult.message}</p>
        <div className="safety-rule-box">
          <span className="safety-rule-icon" aria-hidden="true">
            <ShieldAlert size={25} />
          </span>
          <code>
            Safety rule fired: <strong>{getDisplayRuleId(askResult.safety?.rule_id)}</strong>
            <span className="safety-rule-summary">{reasonLines.summary}</span>
            {reasonLines.detail && <span className="safety-rule-detail">{reasonLines.detail}</span>}
          </code>
        </div>
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

function getClarificationDefaults(askResult: AskResponse): Partial<AskRequestPayload> {
  return {
    end_date: askResult.resolved_request?.end_date ?? "2026-03-31",
    plan_tier: askResult.resolved_request?.plan_tier ?? "Comprehensive",
    start_date: askResult.resolved_request?.start_date ?? "2026-01-01"
  };
}

function HighlightedAnswer({ text }: { text: string }) {
  const parts = text.split(/(0\.\d{3}|\d{1,3}\.\d%)/g);

  return (
    <>
      {parts.map((part, index) =>
        /^(0\.\d{3}|\d{1,3}\.\d%)$/.test(part) ? (
          <strong
            className={part.endsWith("%") ? "answer-percent" : "answer-number"}
            key={`${part}-${index}`}
          >
            {part}
          </strong>
        ) : (
          part
        )
      )}
    </>
  );
}

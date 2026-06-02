import {
  BarChart3,
  BotMessageSquare,
  CircleSlash,
  Play,
  Sparkles,
  Users
} from "lucide-react";
import { useState } from "react";

import type { AskExample, AskRequestPayload, AskResponse, Metric } from "../types";
import { EmptyAskState } from "./EmptyAskState";
import { TrustPanel } from "./TrustPanel";
import { WorkspaceState } from "./WorkspaceState";

type AskWorkspaceProps = {
  askResult: AskResponse | null;
  askExamples: AskExample[];
  isRunning: boolean;
  metric: Metric | null;
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
  const isBlocked = askResult?.status === "blocked";
  const isClarifying = askResult?.status === "clarification_required";
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
            <div className={`query-box ${askResult?.status ?? ""}`}>
              <BotMessageSquare size={27} />
              <textarea
                id="question"
                onChange={(event) => onQuestionChange(event.target.value)}
                placeholder="Ask a governed claims analytics question..."
                value={question}
              />
            </div>
            <button
              className={isBlocked ? "run-button blocked" : "run-button"}
              disabled={isRunning || isBlocked || !question.trim()}
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
                    } else {
                      onRun("Show loss ratio by plan tier in Q1 2026.");
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
                {extraExamples.length > 0 && (
                  <button
                    aria-expanded={showExamples}
                    className="suggestion"
                    onClick={() => setShowExamples((isOpen) => !isOpen)}
                    type="button"
                  >
                    <span className="suggestion-plus">{showExamples ? "-" : "+"}</span>
                    More examples
                  </button>
                )}
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

        {askResult ? (
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
        ) : (
          <EmptyAskState />
        )}
      </section>

      {askResult && <TrustPanel askResult={askResult} metric={metric} />}
    </main>
  );
}

function getClarificationDefaults(askResult: AskResponse | null): Partial<AskRequestPayload> {
  return {
    end_date: askResult?.resolved_request?.end_date ?? "2026-03-31",
    plan_tier: askResult?.resolved_request?.plan_tier ?? "Comprehensive",
    start_date: askResult?.resolved_request?.start_date ?? "2026-01-01"
  };
}

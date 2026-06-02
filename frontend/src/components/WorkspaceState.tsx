import {
  AlertTriangle,
  BarChart3,
  HelpCircle,
  ShieldAlert,
  Users,
  WalletCards
} from "lucide-react";

import { getDisplayRuleId, getSafetyReasonLines } from "../safetyDisplay";
import type { AskResponse, Candidate, Metric } from "../types";
import { CleanCheck } from "./CleanCheck";
import { HighlightedAnswer } from "./HighlightedAnswer";
import { ResultTable } from "./ResultTable";

type WorkspaceStateProps = {
  askResult: AskResponse;
  metric: Metric | null;
  onSelectCandidate: (candidate: Candidate) => void;
};

export function WorkspaceState({
  askResult,
  metric,
  onSelectCandidate
}: WorkspaceStateProps) {
  if (askResult.status === "answer" && askResult.answer) {
    return <AnswerState askResult={askResult} metric={metric} />;
  }

  if (askResult.status === "clarification_required") {
    return (
      <ClarificationState
        askResult={askResult}
        onSelectCandidate={onSelectCandidate}
      />
    );
  }

  if (askResult.status === "blocked") {
    return <BlockedState askResult={askResult} />;
  }

  return <NeutralState message={askResult.message} />;
}

function AnswerState({
  askResult,
  metric
}: {
  askResult: AskResponse;
  metric: Metric | null;
}) {
  if (!askResult.answer) {
    return null;
  }

  const formulaText =
    metric?.id === "loss_ratio"
      ? "incurred claims / earned premium"
      : metric?.formula.expression ??
        askResult.answer.provenance.formula ??
        "catalogue formula";

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
            {askResult.answer.row_count === 1 ? "" : "s"} - based on {formulaText}
          </p>
        </div>
      </div>
    </section>
  );
}

function ClarificationState({
  askResult,
  onSelectCandidate
}: {
  askResult: AskResponse;
  onSelectCandidate: (candidate: Candidate) => void;
}) {
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
              <CandidateIcon index={index} />
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

function BlockedState({ askResult }: { askResult: AskResponse }) {
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
          Safety rule fired:{" "}
          <strong>{getDisplayRuleId(askResult.safety?.rule_id)}</strong>
          <span className="safety-rule-summary">{reasonLines.summary}</span>
          {reasonLines.detail && (
            <span className="safety-rule-detail">{reasonLines.detail}</span>
          )}
        </code>
      </div>
    </section>
  );
}

function NeutralState({ message }: { message: string }) {
  return (
    <section className="state-card neutral">
      <div className="state-heading">
        <HelpCircle size={22} />
        More information needed
      </div>
      <p>{message}</p>
    </section>
  );
}

function CandidateIcon({ index }: { index: number }) {
  if (index === 1) {
    return <WalletCards size={24} />;
  }

  if (index === 2) {
    return <Users size={24} />;
  }

  return <BarChart3 size={24} />;
}

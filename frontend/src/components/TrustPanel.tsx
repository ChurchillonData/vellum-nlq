import type { AskResponse, Metric } from "../types";
import { AnswerTrustPanel } from "./trust/AnswerTrustPanel";
import { BlockedTrustPanel } from "./trust/BlockedTrustPanel";
import { ClarificationTrustPanel } from "./trust/ClarificationTrustPanel";
import { ResolutionTrustPanel } from "./trust/ResolutionTrustPanel";

type TrustPanelProps = {
  askResult: AskResponse;
  metric: Metric | null;
};

export function TrustPanel({ askResult, metric }: TrustPanelProps) {
  if (askResult.status === "clarification_required") {
    return <ClarificationTrustPanel askResult={askResult} />;
  }

  if (askResult.status === "blocked") {
    return <BlockedTrustPanel askResult={askResult} />;
  }

  if (askResult.status !== "answer" || !askResult.answer) {
    return <ResolutionTrustPanel askResult={askResult} />;
  }

  return <AnswerTrustPanel askResult={askResult} metric={metric} />;
}

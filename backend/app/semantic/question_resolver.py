import re
from dataclasses import dataclass
from datetime import date

from app.analytics.models import AnalyticsRequest
from app.semantic.models import Catalogue, MetricSpec


AMBIGUOUS_CLAIMS_WORDS = {"claim", "claims", "number", "numbers", "looking"}


@dataclass(frozen=True)
class MetricCandidate:
    """One metric that may answer a natural-language question."""

    metric_id: str
    label: str
    description: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class QuestionResolution:
    """Resolution result before SQL planning or execution."""

    status: str
    question: str
    candidates: tuple[MetricCandidate, ...]
    resolved_request: AnalyticsRequest | None
    message: str


def resolve_question(
    catalogue: Catalogue,
    question: str,
    start_date: date,
    end_date: date,
    plan_tier: str | None = None,
) -> QuestionResolution:
    """Resolve a simple question into one metric or a clarification prompt."""
    tokens = set(_tokenize(question))
    candidates = _rank_candidates(catalogue, question, tokens)

    if _is_claims_ambiguous(tokens, candidates):
        candidates = _claims_candidates(catalogue)

    if not candidates:
        return QuestionResolution(
            status="unresolved",
            question=question,
            candidates=(),
            resolved_request=None,
            message="No catalogue metric matched the question.",
        )

    top_candidate = candidates[0]
    has_competing_strong_match = (
        len(candidates) > 1 and candidates[1].confidence >= 0.70
    )
    if top_candidate.confidence >= 0.70 and not has_competing_strong_match:
        return QuestionResolution(
            status="resolved",
            question=question,
            candidates=tuple(candidates),
            resolved_request=AnalyticsRequest(
                metric_id=top_candidate.metric_id,
                start_date=start_date,
                end_date=end_date,
                plan_tier=plan_tier,
            ),
            message=f"Resolved to metric: {top_candidate.metric_id}.",
        )

    return QuestionResolution(
        status="clarification_required",
        question=question,
        candidates=tuple(candidates),
        resolved_request=None,
        message="Multiple catalogue metrics may answer this question.",
    )


def _rank_candidates(
    catalogue: Catalogue,
    question: str,
    tokens: set[str],
) -> list[MetricCandidate]:
    candidates = []
    question_normalized = _normalize(question)

    for metric in catalogue.metrics.values():
        score, reason = _score_metric(metric, question_normalized, tokens)
        if score > 0:
            candidates.append(
                MetricCandidate(
                    metric_id=metric.id,
                    label=metric.label,
                    description=metric.description,
                    confidence=score,
                    reason=reason,
                )
            )

    return sorted(candidates, key=lambda item: (-item.confidence, item.metric_id))


def _score_metric(
    metric: MetricSpec,
    question_normalized: str,
    tokens: set[str],
) -> tuple[float, str]:
    if metric.id in question_normalized:
        return 0.95, "metric ID matched"

    for synonym in metric.synonyms:
        if _normalize(synonym) in question_normalized:
            return 0.90, f"synonym matched: {synonym}"

    label = _normalize(metric.label)
    if label in question_normalized:
        return 0.88, f"metric label matched: {metric.label}"

    metric_words = set(_tokenize(metric.label))
    metric_words.update(_tokenize(" ".join(metric.synonyms)))
    overlap = tokens & metric_words
    if overlap:
        confidence = min(0.65, 0.25 + (0.10 * len(overlap)))
        return confidence, f"keyword overlap: {', '.join(sorted(overlap))}"

    return 0, ""


def _is_claims_ambiguous(tokens: set[str], candidates: list[MetricCandidate]) -> bool:
    has_claims_word = bool(tokens & AMBIGUOUS_CLAIMS_WORDS)
    lacks_specific_metric = all(candidate.confidence < 0.70 for candidate in candidates)
    return has_claims_word and lacks_specific_metric


def _claims_candidates(catalogue: Catalogue) -> list[MetricCandidate]:
    candidate_ids = ("loss_ratio", "paid_claims", "claim_frequency")
    return [
        MetricCandidate(
            metric_id=metric.id,
            label=metric.label,
            description=metric.description,
            confidence=0.42,
            reason="ambiguous claims question",
        )
        for metric_id in candidate_ids
        if (metric := catalogue.metrics.get(metric_id)) is not None
    ]


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", _normalize(value))


def _normalize(value: str) -> str:
    return value.casefold().replace("-", "_")

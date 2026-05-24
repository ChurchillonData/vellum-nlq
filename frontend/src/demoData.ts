import type { AskResponse, Metric } from "./types";

export const demoQuestions = [
  "What was loss ratio for the Comprehensive plan tier in Q1 2026?",
  "Show loss ratio by plan tier in Q1 2026.",
  "Show paid claims by region for the last six months.",
  "How are the claims numbers looking?",
  "Drop all claims from the database."
];

export const demoAskResponse: AskResponse = {
  status: "answer",
  query_id: "vellum:audit:9f3a2d1c-84b2",
  question: demoQuestions[0],
  message: "Resolved to metric: loss_ratio.",
  resolved_request: {
    metric_id: "loss_ratio",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    plan_tier: "Comprehensive",
    group_by: []
  },
  candidates: [
    {
      metric_id: "loss_ratio",
      label: "Loss ratio",
      confidence: 0.9,
      reason: "synonym matched: incurred loss ratio"
    }
  ],
  safety: null,
  scope: null,
  answer: {
    query_id: "vellum:audit:9f3a2d1c-84b2",
    metric_id: "loss_ratio",
    answer: "Comprehensive plan tier loss ratio in Q1 2026 was 0.847 (84.7%).",
    row_count: 1,
    rows: [{ quarter: "2026 Q1", plan_tier: "Comprehensive", loss_ratio: 0.847 }],
    sql: `-- vellum-nlq - loss_ratio Vellum 2.5
WITH premium_data AS (
  SELECT member_id, SUM(premium_amt) AS total_premium
  FROM uk_claims_db.premium
  WHERE quarter = '2026-Q1'
  GROUP BY member_id
), claim_loss AS (
  SELECT member_id, SUM(claim_amount) AS incurred_loss
  FROM uk_claims_db.claims
  WHERE plan_tier = 'Comprehensive'
    AND incurred_date BETWEEN '2026-01-01' AND '2026-03-31'
  GROUP BY member_id
)
SELECT SUM(incurred_loss)/SUM(total_premium) AS loss_ratio
FROM claim_loss JOIN premium_data USING(member_id);`,
    parameters: {
      start_date: "2026-01-01",
      end_date: "2026-03-31",
      plan_tier: "Comprehensive"
    },
    provenance: {
      metric_id: "loss_ratio",
      metric_label: "Loss ratio",
      metric_version: "Vellum 2.5",
      metric_description: "Incurred claims divided by earned premium for the selected reporting slice.",
      formula: "SUM(claims.net_incurred_amount) / NULLIF(SUM(premium.earned_amount), 0)",
      time_anchor: "claims.incurred_date",
      tables_used: ["claims", "premium"],
      joins_used: ["claims -> premium (member_id)"],
      result_shape: {
        columns: ["loss_ratio"],
        grain: "single_metric",
        max_rows: 1
      }
    },
    validation: {
      passed: true,
      rules_checked: [
        "comments_absent",
        "parseable_sql",
        "single_statement",
        "select_only",
        "table_allowlist",
        "column_allowlist",
        "function_allowlist",
        "join_allowlist",
        "result_size_control",
        "literal_parameter_check",
        "read_replica_policy"
      ],
      rejections: []
    },
    execution_mode: "local_demo"
  }
};

export const demoClarificationResponse: AskResponse = {
  status: "clarification_required",
  query_id: "vellum:clarify:7c8e9f1a",
  question: "How are the claims numbers looking?",
  message:
    "\"claims numbers\" can refer to multiple business metrics. Select the intended KPI:",
  resolved_request: null,
  candidates: [
    {
      metric_id: "loss_ratio",
      label: "Loss Ratio",
      confidence: 0.42,
      reason: "Incurred claims / earned premium"
    },
    {
      metric_id: "paid_claims",
      label: "Paid Claims (GBP)",
      confidence: 0.38,
      reason: "Total claim amount paid in GBP"
    },
    {
      metric_id: "claim_frequency",
      label: "Claim Frequency",
      confidence: 0.35,
      reason: "Claims per member per period"
    }
  ],
  safety: null,
  scope: null,
  answer: null
};

export const demoBlockedResponse: AskResponse = {
  status: "blocked",
  query_id: "vellum:reject:ddl_9f3b2e",
  question: "Drop all claims from the database.",
  message:
    "The operation \"DROP TABLE / destructive DDL\" is not permitted on the analytics read-replica. Vellum-NLQ enforces guardrails against mutable commands.",
  resolved_request: null,
  candidates: [],
  safety: {
    rule_id: "SQL_GUARD_07 / DDL_BLOCKLIST",
    severity: "critical",
    reason: "Command contains DROP + claims - potential data loss."
  },
  scope: null,
  answer: null
};

export function getDemoAskResponse(question: string): AskResponse {
  const normalized = question.toLowerCase();

  if (normalized.includes("drop") || normalized.includes("delete")) {
    return { ...demoBlockedResponse, question };
  }

  if (normalized.includes("claims numbers")) {
    return { ...demoClarificationResponse, question };
  }

  return { ...demoAskResponse, question };
}

export const demoMetrics: Metric[] = [
  {
    id: "loss_ratio",
    label: "Loss ratio",
    description: "Incurred claims divided by earned premium for the selected reporting slice.",
    formula: {
      numerator: "SUM(claims.net_incurred_amount)",
      denominator: "SUM(premium.earned_amount)",
      expression: "SUM(claims.net_incurred_amount) / NULLIF(SUM(premium.earned_amount), 0)"
    },
    required_tables: ["claims", "premium"],
    time_anchor: "claims.incurred_date",
    currency: null,
    filters_default: ["claims.status != 'void'"],
    synonyms: ["loss ratio", "incurred loss ratio"],
    owner: "actuarial",
    version: "Vellum 2.5",
    last_reviewed: "2026-05-22"
  },
  {
    id: "paid_claims",
    label: "Paid claims",
    description: "Sum of claim line payments posted in the selected period.",
    formula: {
      numerator: "SUM(claim_lines.net_paid_amount)",
      denominator: null,
      expression: "SUM(claim_lines.net_paid_amount)"
    },
    required_tables: ["claim_lines"],
    time_anchor: "claim_lines.paid_date",
    currency: "GBP",
    filters_default: [],
    synonyms: ["paid claims", "claim payments"],
    owner: "claims",
    version: "Vellum 2.5",
    last_reviewed: "2026-05-22"
  },
  {
    id: "claim_frequency",
    label: "Claim frequency",
    description: "Distinct claims per 1,000 member months.",
    formula: {
      numerator: "COUNT(DISTINCT claims.id)",
      denominator: "SUM(enrolment_months.member_months)",
      expression: "COUNT(DISTINCT claims.id) * 1000 / NULLIF(SUM(enrolment_months.member_months), 0)"
    },
    required_tables: ["claims", "enrolment_months"],
    time_anchor: "claims.incurred_date",
    currency: null,
    filters_default: ["claims.status != 'void'"],
    synonyms: ["claim frequency", "claims per member"],
    owner: "actuarial",
    version: "Vellum 2.5",
    last_reviewed: "2026-05-22"
  }
];

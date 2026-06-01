import type { AskExample, AskResponse, Metric } from "./types";

export const demoQuestions = [
  "What was incurred loss ratio in Q1?",
  "Show loss ratio by plan tier in Q1 2026.",
  "Show paid claims by region for the last six months.",
  "How are the claims numbers looking?",
  "Drop all claims from the database."
];

export const demoAskExamples: AskExample[] = [
  {
    id: "answer_loss_ratio_q1",
    label: "Loss ratio in Q1",
    question: demoQuestions[0],
    expected_status: "answer",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    plan_tier: "Comprehensive",
    group_by: []
  },
  {
    id: "answer_paid_claims_plan_tier",
    label: "Paid claims by plan tier filter",
    question: "Show paid claims for the Comprehensive plan tier.",
    expected_status: "answer",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    plan_tier: "Comprehensive",
    group_by: []
  },
  {
    id: "answer_claim_frequency_plan_tier",
    label: "Claim frequency by plan tier filter",
    question: "Show claim frequency for the Comprehensive plan tier.",
    expected_status: "answer",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    plan_tier: "Comprehensive",
    group_by: []
  },
  {
    id: "answer_incurred_claims_plan_tier",
    label: "Incurred claims by plan tier filter",
    question: "Show incurred claims for the Comprehensive plan tier.",
    expected_status: "answer",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    plan_tier: "Comprehensive",
    group_by: []
  },
  {
    id: "answer_claim_severity_plan_tier",
    label: "Claim severity by plan tier filter",
    question: "Show claim severity for the Comprehensive plan tier.",
    expected_status: "answer",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    plan_tier: "Comprehensive",
    group_by: []
  },
  {
    id: "answer_decline_rate_q1",
    label: "Decline rate in Q1",
    question: "What was decline rate for the Comprehensive plan tier in Q1 2026?",
    expected_status: "answer",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    plan_tier: "Comprehensive",
    group_by: []
  },
  {
    id: "answer_decline_rate_by_specialty",
    label: "Decline rate by specialty",
    question: "What was decline rate by consultant specialty for the Comprehensive plan tier in Q1 2026?",
    expected_status: "answer",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    plan_tier: "Comprehensive",
    group_by: ["consultant_specialty"]
  },
  {
    id: "answer_loss_ratio_by_plan_tier",
    label: "Loss ratio by plan tier",
    question: demoQuestions[1],
    expected_status: "answer",
    start_date: "2026-01-01",
    end_date: "2026-03-31",
    group_by: ["plan_tier"]
  },
  {
    id: "answer_paid_claims_by_region",
    label: "Paid claims by region",
    question: demoQuestions[2],
    expected_status: "answer",
    group_by: ["region"]
  },
  {
    id: "answer_claim_frequency_ytd",
    label: "Claim frequency YTD",
    question: "Show claim frequency year to date.",
    expected_status: "answer",
    group_by: []
  },
  {
    id: "date_required_loss_ratio",
    label: "Date range required",
    question: "What was loss ratio for the Comprehensive plan tier?",
    expected_status: "date_range_required",
    plan_tier: "Comprehensive",
    group_by: []
  },
  {
    id: "clarify_claims_numbers",
    label: "Ambiguous claims numbers",
    question: demoQuestions[3],
    expected_status: "clarification_required",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  },
  {
    id: "clarify_claims_performance",
    label: "Ambiguous claims performance",
    question: "Show me claims performance.",
    expected_status: "clarification_required",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  },
  {
    id: "clarify_claims_happening",
    label: "Ambiguous claims trend wording",
    question: "What is happening with claims?",
    expected_status: "clarification_required",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  },
  {
    id: "blocked_drop_claims",
    label: "Blocked DROP intent",
    question: demoQuestions[4],
    expected_status: "blocked",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  },
  {
    id: "blocked_delete_premium",
    label: "Blocked DELETE intent",
    question: "Delete all premium records.",
    expected_status: "blocked",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  },
  {
    id: "blocked_update_claims",
    label: "Blocked UPDATE intent",
    question: "Update every claim status to closed.",
    expected_status: "blocked",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  },
  {
    id: "out_of_scope_loss_ratio_forecast",
    label: "Out-of-scope forecast",
    question: "What will loss ratio be next quarter?",
    expected_status: "out_of_scope",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  },
  {
    id: "out_of_scope_claims_prediction",
    label: "Out-of-scope claims prediction",
    question: "Predict paid claims for Q2.",
    expected_status: "out_of_scope",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  },
  {
    id: "out_of_scope_future_projection",
    label: "Out-of-scope future projection",
    question: "Forecast claim frequency next month.",
    expected_status: "out_of_scope",
    start_date: "2026-01-01",
    end_date: "2026-03-31"
  }
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

export const demoOutOfScopeResponse: AskResponse = {
  status: "out_of_scope",
  query_id: "vellum:scope:forecast_4a2b",
  question: "What will loss ratio be next quarter?",
  message:
    "Forecasting is outside the current Vellum-NLQ analytics catalogue. Ask for a historical period instead.",
  resolved_request: null,
  candidates: [],
  safety: null,
  scope: {
    reason_id: "FORECASTING_NOT_SUPPORTED",
    reason: "The current demo supports governed historical analytics, not prediction."
  },
  answer: null
};

export const demoDateRequiredResponse: AskResponse = {
  status: "date_range_required",
  query_id: "vellum:date:loss_ratio_2b1f",
  question: "What was loss ratio for the Comprehensive plan tier?",
  message: "A date range is required before Vellum can calculate this metric.",
  resolved_request: {
    metric_id: "loss_ratio",
    start_date: "",
    end_date: "",
    plan_tier: "Comprehensive",
    group_by: []
  },
  candidates: [],
  safety: null,
  scope: null,
  answer: null
};

export function getDemoAskResponse(question: string): AskResponse {
  const normalized = question.toLowerCase();

  if (
    normalized.includes("drop") ||
    normalized.includes("delete") ||
    normalized.includes("update") ||
    normalized.includes("truncate") ||
    normalized.includes("alter") ||
    normalized.includes("insert")
  ) {
    return { ...demoBlockedResponse, question };
  }

  if (
    normalized.includes("forecast") ||
    normalized.includes("predict") ||
    normalized.includes("next quarter") ||
    normalized.includes("next month")
  ) {
    return { ...demoOutOfScopeResponse, question };
  }

  if (
    normalized.includes("claims numbers") ||
    normalized.includes("claims performance") ||
    normalized.includes("happening with claims")
  ) {
    return { ...demoClarificationResponse, question };
  }

  if (normalized.includes("loss ratio") && !normalized.match(/q\d|quarter|2026|last|year to date|ytd/)) {
    return { ...demoDateRequiredResponse, question };
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
    last_reviewed: "2026-05-22",
    allowed_dimensions: ["plan_tier", "region"],
    join_preview: [
      "claims.member_id -> members.id (many_to_one)",
      "premium.member_id -> members.id (many_to_one)"
    ]
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
    last_reviewed: "2026-05-22",
    allowed_dimensions: ["plan_tier", "region"],
    join_preview: [
      "claim_lines.claim_id -> claims.id (many_to_one)",
      "claims.member_id -> members.id (many_to_one)"
    ]
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
    last_reviewed: "2026-05-22",
    allowed_dimensions: ["plan_tier", "region"],
    join_preview: [
      "enrolment_months.member_id -> members.id (many_to_one)",
      "claims.member_id -> members.id (many_to_one)"
    ]
  },
  {
    id: "decline_rate",
    label: "Decline rate",
    description: "Declined claim value divided by billed claim value for the selected reporting slice.",
    formula: {
      numerator: "SUM(claim_lines.declined_amount)",
      denominator: "SUM(claim_lines.billed_amount)",
      expression: "SUM(claim_lines.declined_amount) / NULLIF(SUM(claim_lines.billed_amount), 0)"
    },
    required_tables: ["claim_lines", "claims"],
    time_anchor: "claim_lines.service_date",
    currency: null,
    filters_default: ["claim_lines.billed_amount > 0"],
    synonyms: ["decline rate", "denial rate", "rejection rate"],
    owner: "claims governance",
    version: "Vellum 2.5",
    last_reviewed: "2026-05-22",
    allowed_dimensions: ["consultant_specialty", "plan_tier", "region"],
    join_preview: [
      "claim_lines.claim_id -> claims.id (many_to_one)",
      "claim_lines.provider_id -> providers.id (many_to_one)"
    ]
  },
  {
    id: "incurred_claims",
    label: "Incurred claims",
    description: "Total incurred claim value anchored on the date the claim was incurred.",
    formula: {
      numerator: "SUM(claims.net_incurred_amount)",
      denominator: null,
      expression: "SUM(claims.net_incurred_amount)"
    },
    required_tables: ["claims"],
    time_anchor: "claims.incurred_date",
    currency: "GBP",
    filters_default: ["claims.status != 'void'"],
    synonyms: ["incurred claims", "incurred loss", "claim cost"],
    owner: "actuarial",
    version: "Vellum 2.5",
    last_reviewed: "2026-05-22",
    allowed_dimensions: ["plan_tier", "region"],
    join_preview: ["claims.member_id -> members.id (many_to_one)"]
  },
  {
    id: "claim_severity",
    label: "Claim severity",
    description: "Average incurred value per distinct claim in the selected reporting period.",
    formula: {
      numerator: "SUM(claims.net_incurred_amount)",
      denominator: "COUNT(DISTINCT claims.id)",
      expression: "SUM(claims.net_incurred_amount) / NULLIF(COUNT(DISTINCT claims.id), 0)"
    },
    required_tables: ["claims"],
    time_anchor: "claims.incurred_date",
    currency: "GBP",
    filters_default: ["claims.status != 'void'"],
    synonyms: ["claim severity", "average claim size", "average claim amount"],
    owner: "actuarial",
    version: "Vellum 2.5",
    last_reviewed: "2026-05-22",
    allowed_dimensions: ["plan_tier", "region"],
    join_preview: ["claims.member_id -> members.id (many_to_one)"]
  }
];

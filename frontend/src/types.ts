export type AskStatus =
  | "answer"
  | "clarification_required"
  | "blocked"
  | "date_range_required"
  | "out_of_scope"
  | "unresolved";

export type Candidate = {
  metric_id: string;
  label: string;
  confidence: number;
  reason: string;
};

export type Validation = {
  passed: boolean;
  rules_checked: string[];
  rejections: Array<{ rule: string; message: string }>;
};

export type Provenance = {
  metric_id?: string;
  metric_label?: string;
  metric_version?: string;
  metric_description?: string;
  formula?: string;
  time_anchor?: string;
  tables_used?: string[];
  joins_used?: string[];
  result_shape?: {
    columns: string[];
    grain: string;
    max_rows: number;
  };
};

export type AskAnswer = {
  query_id: string;
  metric_id: string;
  answer: string;
  row_count: number;
  rows: Record<string, unknown>[];
  sql: string;
  parameters: Record<string, unknown>;
  provenance: Provenance;
  validation: Validation;
  execution_mode: string;
};

export type AskResponse = {
  status: AskStatus;
  query_id: string;
  question: string;
  message: string;
  resolved_request: {
    metric_id: string;
    start_date: string;
    end_date: string;
    plan_tier?: string | null;
    group_by?: string[];
  } | null;
  candidates: Candidate[];
  safety: { rule_id: string; severity: string; reason: string } | null;
  scope: { reason_id: string; reason: string } | null;
  answer: AskAnswer | null;
};

export type AskRequestPayload = {
  question: string;
  metric_id?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  plan_tier?: string | null;
  group_by?: string[];
};

export type AskExample = AskRequestPayload & {
  id: string;
  label: string;
  expected_status: AskStatus;
};

export type AskExamplesResponse = {
  examples: AskExample[];
};

export type Metric = {
  id: string;
  label: string;
  description: string;
  formula: {
    numerator: string;
    denominator: string | null;
    expression: string;
  };
  required_tables: string[];
  time_anchor: string;
  currency: string | null;
  filters_default: string[];
  synonyms: string[];
  owner: string;
  version: string;
  last_reviewed: string;
};

export type MetricsResponse = {
  catalogue: string;
  metrics: Metric[];
};

export type AuditRecord = {
  query_id: string;
  event_type: string;
  created_at?: string;
  status?: AskStatus | string;
  request?: Record<string, unknown>;
  resolved_request?: Record<string, unknown> | null;
  candidates?: Candidate[];
  safety?: { rule_id: string; severity: string; reason: string } | null;
  scope?: { reason_id: string; reason: string } | null;
  metric_id?: string | null;
  sql?: string | null;
  parameters?: Record<string, unknown> | null;
  provenance?: Provenance | null;
  validation?: Validation | null;
  execution?: {
    mode?: string;
    row_count?: number;
    answer?: string;
  } | null;
};

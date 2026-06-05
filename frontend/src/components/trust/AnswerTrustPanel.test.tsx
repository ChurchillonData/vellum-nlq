import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { AskResponse, Metric } from "../../types";
import { AnswerTrustPanel } from "./AnswerTrustPanel";

describe("AnswerTrustPanel", () => {
  it("renders answer-specific provenance and latency", () => {
    render(<AnswerTrustPanel askResult={askResult} metric={staleMetric} />);

    expect(screen.getByText("paid_claims (financial_kpi)")).toBeInTheDocument();
    expect(screen.getByText("claim_lines.paid_date")).toBeInTheDocument();
    expect(screen.getByText("q_live_answer")).toBeInTheDocument();
    expect(
      screen.getByText("8.50 ms execution - 2.25 ms planning - 10.75 ms total")
    ).toBeInTheDocument();
    expect(screen.queryByText("loss_ratio (financial_kpi)")).not.toBeInTheDocument();
  });

  it("shows validation violations and hides unsafe SQL", async () => {
    const user = userEvent.setup();

    render(<AnswerTrustPanel askResult={failedValidationResult} metric={staleMetric} />);

    expect(screen.getByText("validation failed")).toBeInTheDocument();
    expect(screen.getByText(/blocked - 2 violations/i)).toBeInTheDocument();
    expect(screen.queryByText(/unknown_table/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /show 2 violations/i }));

    expect(screen.getByText(/unknown_table/i)).toBeInTheDocument();
    expect(screen.getByText(/unsafe_function/i)).toBeInTheDocument();
    expect(
      screen.getByText("Generated SQL hidden because validation failed.")
    ).toBeInTheDocument();
    expect(screen.queryByText(/Generated SQL \(parameterised\)/i)).not.toBeInTheDocument();
  });
});

const askResult: AskResponse = {
  answer: {
    answer: "Paid claims were GBP 123.45.",
    compact_sql: "SELECT SUM(net_paid_amount) AS paid_claims",
    dataset: {
      claim_count: 10,
      member_count: 5,
      name: "demo",
      premium_row_count: 5
    },
    execution_mode: "local_demo",
    latency: {
      execution_ms: 8.5,
      planning_ms: 2.25,
      total_ms: 10.75
    },
    metric_id: "paid_claims",
    parameters: {},
    provenance: {
      formula: "SUM(claim_lines.net_paid_amount)",
      joins_used: ["claim_lines.claim_id = claims.id (many_to_one)"],
      metric_description: "Paid claims.",
      metric_label: "Paid claims",
      metric_version: "Vellum 2.5",
      result_shape: {
        columns: ["paid_claims"],
        grain: "single_metric",
        max_rows: 1
      },
      tables_used: ["claim_lines", "claims"],
      time_anchor: "claim_lines.paid_date"
    },
    query_id: "q_live_answer",
    row_count: 1,
    rows: [{ paid_claims: 123.45 }],
    sql: "SELECT SUM(claim_lines.net_paid_amount) AS paid_claims",
    validation: {
      passed: true,
      rejections: [],
      rules_checked: ["select_only", "join_allowlist"]
    }
  },
  candidates: [],
  availability: null,
  message: "Resolved to metric: paid_claims.",
  query_id: "q_live_answer",
  question: "How much did we pay?",
  resolved_request: {
    end_date: "2026-03-31",
    metric_id: "paid_claims",
    start_date: "2026-01-01"
  },
  safety: null,
  scope: null,
  status: "answer"
};

const staleMetric: Metric = {
  allowed_dimensions: [],
  currency: null,
  description: "Stale loss-ratio metric.",
  filters_default: [],
  formula: {
    denominator: "SUM(premium.earned_amount)",
    expression: "loss ratio expression",
    numerator: "SUM(claims.net_incurred_amount)"
  },
  id: "loss_ratio",
  join_preview: [],
  label: "Loss ratio",
  last_reviewed: "2026-05-22",
  owner: "actuarial",
  required_tables: ["claims", "premium"],
  synonyms: [],
  time_anchor: "claims.incurred_date",
  version: "Vellum 2.5"
};

const failedValidationResult: AskResponse = {
  ...askResult,
  answer: {
    ...askResult.answer!,
    validation: {
      passed: false,
      rejections: [
        {
          message: "Unknown table users is not allowed.",
          rule: "unknown_table"
        },
        {
          message: "Function pg_sleep is not allowed.",
          rule: "unsafe_function"
        }
      ],
      rules_checked: ["select_only", "table_allowlist"]
    }
  }
};

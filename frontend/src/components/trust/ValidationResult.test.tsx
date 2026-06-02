import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ValidationResult } from "./ValidationResult";

describe("ValidationResult", () => {
  it("counts checked rules and expands or collapses the rule list", async () => {
    const user = userEvent.setup();

    render(
      <ValidationResult
        validation={{
          passed: true,
          rejections: [],
          rules_checked: ["select_only", "table_allowlist", "join_allowlist"]
        }}
      />
    );

    expect(screen.getByText(/1 of 3 rules checked/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/3 of 3 rules checked/i)).toBeInTheDocument();
    });
    expect(screen.queryByText("select only")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /show 3 rules/i }));

    expect(screen.getByText("select only")).toBeInTheDocument();
    expect(screen.getByText("table allowlist")).toBeInTheDocument();
    expect(screen.getByText("join allowlist")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /hide 3 rules/i }));

    expect(screen.queryByText("select only")).not.toBeInTheDocument();
  });

  it("expands or collapses validation violations", async () => {
    const user = userEvent.setup();

    render(
      <ValidationResult
        validation={{
          passed: false,
          rejections: [
            {
              message: "Unknown table users is not allowed.",
              rule: "unknown_table"
            }
          ],
          rules_checked: ["select_only"]
        }}
      />
    );

    expect(screen.getByText(/blocked - 1 violation/i)).toBeInTheDocument();
    expect(screen.queryByText(/unknown_table/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /show 1 violation/i }));

    expect(screen.getByText(/unknown_table/i)).toBeInTheDocument();
  });
});

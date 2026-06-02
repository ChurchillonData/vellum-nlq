import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ValidationResult } from "./ValidationResult";

describe("ValidationResult", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("counts checked rules from one to the final rule count", () => {
    vi.useFakeTimers();

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

    act(() => {
      vi.advanceTimersByTime(70);
    });

    expect(screen.getByText(/3 of 3 rules checked/i)).toBeInTheDocument();
    expect(screen.getByText("select only")).toBeInTheDocument();
    expect(screen.getByText("table allowlist")).toBeInTheDocument();
    expect(screen.getByText("join allowlist")).toBeInTheDocument();
  });
});

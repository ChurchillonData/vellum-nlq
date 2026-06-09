import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Metric } from "../types";
import { CatalogueExplorer, getNewestRegistryPageWindow } from "./CatalogueExplorer";

describe("getNewestRegistryPageWindow", () => {
  it("keeps the newest partial bucket on page 1", () => {
    expect(getNewestRegistryPageWindow(12, 5, 1)).toEqual({
      endIndex: 12,
      startIndex: 10
    });
    expect(getNewestRegistryPageWindow(12, 5, 2)).toEqual({
      endIndex: 10,
      startIndex: 5
    });
    expect(getNewestRegistryPageWindow(12, 5, 3)).toEqual({
      endIndex: 5,
      startIndex: 0
    });
  });

  it("keeps page 1 full when the newest bucket has exactly five records", () => {
    expect(getNewestRegistryPageWindow(10, 5, 1)).toEqual({
      endIndex: 10,
      startIndex: 5
    });
    expect(getNewestRegistryPageWindow(10, 5, 2)).toEqual({
      endIndex: 5,
      startIndex: 0
    });
  });

  it("returns an empty window when no metrics match", () => {
    expect(getNewestRegistryPageWindow(0, 5, 1)).toEqual({
      endIndex: 0,
      startIndex: 0
    });
  });
});

describe("CatalogueExplorer registry filters", () => {
  it("resets to the newest registry page when All metrics is clicked", async () => {
    const user = userEvent.setup();

    render(<CatalogueExplorer mappingCoverage={null} metrics={makeMetrics(12)} />);

    expect(screen.getByText("Metric 11")).toBeInTheDocument();
    expect(screen.getByText("Metric 12")).toBeInTheDocument();
    expect(screen.queryByText("Metric 06")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "2" }));

    expect(screen.getByText("Metric 06")).toBeInTheDocument();
    expect(screen.queryByText("Metric 12")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /all metrics/i }));

    expect(screen.getByText("Metric 11")).toBeInTheDocument();
    expect(screen.getByText("Metric 12")).toBeInTheDocument();
    expect(screen.queryByText("Metric 06")).not.toBeInTheDocument();
  });
});

function makeMetrics(count: number): Metric[] {
  return Array.from({ length: count }, (_, index) => {
    const displayNumber = String(index + 1).padStart(2, "0");

    return {
      allowed_dimensions: ["plan_tier", "region"],
      currency: null,
      description: `Governed description for metric ${displayNumber}.`,
      filters_default: [],
      formula: {
        denominator: null,
        expression: `SUM(metric_${displayNumber}.amount)`,
        numerator: `SUM(metric_${displayNumber}.amount)`
      },
      id: `metric_${displayNumber}`,
      join_preview: [],
      label: `Metric ${displayNumber}`,
      last_reviewed: "2026-05-22",
      owner: "Finance Analytics",
      required_tables: [`metric_${displayNumber}`],
      synonyms: [`metric ${displayNumber}`],
      time_anchor: `metric_${displayNumber}.date`,
      version: "Vellum 2.5"
    };
  });
}

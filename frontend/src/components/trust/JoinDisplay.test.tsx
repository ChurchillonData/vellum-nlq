import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { JoinDisplay } from "./JoinDisplay";

describe("JoinDisplay", () => {
  it("renders each provenance join with relationship type", () => {
    render(
      <JoinDisplay
        joins={[
          "claim_lines.claim_id = claims.id (many_to_one)",
          "claim_lines.provider_id = providers.id (many_to_one)"
        ]}
      />
    );

    expect(screen.getByText("claim_lines.claim_id")).toBeInTheDocument();
    expect(screen.getByText("claims.id")).toBeInTheDocument();
    expect(screen.getByText("claim_lines.provider_id")).toBeInTheDocument();
    expect(screen.getByText("providers.id")).toBeInTheDocument();
    expect(screen.getAllByText("many_to_one")).toHaveLength(2);
  });

  it("does not show a fixed fallback join when no joins are used", () => {
    render(<JoinDisplay joins={[]} />);

    expect(screen.getByText("No joins used")).toBeInTheDocument();
    expect(screen.queryByText(/claims -> premium/i)).not.toBeInTheDocument();
  });
});

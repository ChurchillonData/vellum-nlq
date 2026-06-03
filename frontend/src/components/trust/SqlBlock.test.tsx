import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SqlBlock } from "./SqlBlock";

describe("SqlBlock", () => {
  const explainableSql = "SELECT *\nFROM physical_claims";
  const compactSql = "SELECT loss_ratio\nFROM semantic.loss_ratio_base";

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("copies the SQL view currently shown", async () => {
    const user = userEvent.setup();
    const writeText = vi
      .spyOn(navigator.clipboard, "writeText")
      .mockResolvedValue(undefined);

    render(<SqlBlock compactSql={compactSql} sql={explainableSql} />);

    await user.click(screen.getByRole("button", { name: /copy/i }));
    expect(writeText).toHaveBeenLastCalledWith(explainableSql);

    await user.click(screen.getByRole("button", { name: /compact/i }));
    await user.click(screen.getByRole("button", { name: /copy/i }));

    expect(writeText).toHaveBeenLastCalledWith(compactSql);
  });

  it("reveals generated SQL with a typewriter effect", () => {
    vi.useFakeTimers();
    const { container } = render(<SqlBlock sql={explainableSql} />);
    const sqlBlock = container.querySelector(".sql-block");

    expect(sqlBlock?.textContent).not.toContain(explainableSql);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(sqlBlock?.textContent).toContain(explainableSql);
  });
});

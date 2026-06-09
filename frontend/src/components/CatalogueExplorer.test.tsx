import { describe, expect, it } from "vitest";

import { getNewestRegistryPageWindow } from "./CatalogueExplorer";

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

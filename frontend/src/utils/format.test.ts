import { describe, expect, it } from "vitest";

import { formatDateTime, titleCase } from "./format";

describe("format utilities", () => {
  it("converts snake case and spaced values into title case labels", () => {
    expect(titleCase("crash_loop_back_off")).toBe("Crash Loop Back Off");
    expect(titleCase("  high   memory  ")).toBe("High Memory");
  });

  it("uses an em dash fallback when a timestamp is missing", () => {
    expect(formatDateTime(null)).toBe("—");
    expect(formatDateTime()).toBe("—");
  });
});

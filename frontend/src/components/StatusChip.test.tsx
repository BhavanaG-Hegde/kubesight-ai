import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusChip } from "./StatusChip";

describe("StatusChip", () => {
  it("renders normalized incident and health labels", () => {
    render(<StatusChip value="image_pull_back_off" />);

    expect(screen.getByText("Image Pull Back Off")).toBeInTheDocument();
  });
});

import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { IncidentDetailPage } from "./IncidentDetailPage";
import { renderWithProviders } from "../test/test-utils";
import type { AIAnalysisListResponse, IncidentRead } from "../types/domain";

const mocks = vi.hoisted(() => ({
  getAIAnalyses: vi.fn<() => Promise<AIAnalysisListResponse>>(),
  getIncident: vi.fn<() => Promise<IncidentRead>>(),
  updateIncident: vi.fn(),
}));

vi.mock("../api/incidents", () => ({
  getIncident: mocks.getIncident,
  updateIncident: mocks.updateIncident,
}));

vi.mock("../api/ai", () => ({
  analyzeIncident: vi.fn(),
  askAI: vi.fn(),
  getAIAnalyses: mocks.getAIAnalyses,
}));

const incident: IncidentRead = {
  id: "incident-1",
  cluster_name: "local-kind",
  namespace: "payments",
  pod_name: "payment-service-7f89",
  incident_type: "crash_loop_back_off",
  severity: "critical",
  status: "open",
  title: "CrashLoopBackOff detected",
  summary: "payment-service restarted repeatedly after startup probe failures.",
  root_cause: "Startup probe fails after migrations timeout.",
  recommendation: "Check migration duration and database connectivity.",
  resolution: null,
  detection_source: "rule_engine",
  first_seen_at: "2026-01-02T03:04:05Z",
  last_seen_at: "2026-01-02T03:09:05Z",
  resolved_at: null,
  created_at: "2026-01-02T03:04:05Z",
  updated_at: "2026-01-02T03:09:05Z",
};

describe("IncidentDetailPage", () => {
  beforeEach(() => {
    mocks.getIncident.mockResolvedValue(incident);
    mocks.getAIAnalyses.mockResolvedValue({
      items: [
        {
          id: "analysis-1",
          incident_id: "incident-1",
          pod_id: null,
          model_name: "llama3.2",
          question: null,
          response: "The pod is likely failing because startup work exceeds probe limits.",
          created_at: "2026-01-02T03:10:05Z",
        },
      ],
    });
    mocks.updateIncident.mockResolvedValue({ ...incident, status: "acknowledged" });
  });

  it("loads incident context and saves edited resolution fields", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
      </Routes>,
      { route: "/incidents/incident-1" },
    );

    expect(await screen.findByRole("heading", { name: "CrashLoopBackOff detected" })).toBeVisible();
    expect(screen.getByText(/payment-service restarted repeatedly/i)).toBeInTheDocument();
    expect(screen.getAllByText(/startup work exceeds probe limits/i)).toHaveLength(2);

    await user.clear(screen.getByLabelText("Resolution"));
    await user.type(screen.getByLabelText("Resolution"), "Increased startup probe threshold.");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(mocks.updateIncident).toHaveBeenCalledWith(
        "incident-1",
        expect.objectContaining({
          recommendation: "Check migration duration and database connectivity.",
          resolution: "Increased startup probe threshold.",
          root_cause: "Startup probe fails after migrations timeout.",
          status: "open",
        }),
      );
    });
  });
});

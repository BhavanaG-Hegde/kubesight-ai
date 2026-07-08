import { expect, test } from "@playwright/test";
import type { Page, Route } from "@playwright/test";

const now = "2026-01-02T03:09:05Z";

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test("redirects unauthenticated users to login", async ({ page }) => {
  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/login$/);
});

test("renders the authenticated dashboard", async ({ page }) => {
  await authenticate(page);
  await page.goto("/dashboard");

  await expect(page.getByRole("heading", { name: "Cluster Dashboard" })).toBeVisible();
  await expect(page.getByText("Total Pods")).toBeVisible();
  await expect(page.getByText("CrashLoopBackOff detected")).toBeVisible();
});

test("renders analytics charts from mocked telemetry", async ({ page }) => {
  await authenticate(page);
  await page.goto("/analytics");

  await expect(page.getByRole("heading", { name: "Analytics" })).toBeVisible();
  await expect(page.getByText("Incident Trends")).toBeVisible();
  await expect(page.getByText("Resource Trends")).toBeVisible();
});

test("opens incident detail with AI guidance", async ({ page }) => {
  await authenticate(page);
  await page.goto("/incidents/incident-1");

  await expect(page.getByRole("heading", { name: "CrashLoopBackOff detected" })).toBeVisible();
  await expect(page.getByText(/startup work exceeds probe limits/i).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Save" })).toBeVisible();
});

async function authenticate(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("kubesight_token", "smoke-test-token");
  });
}

async function mockApi(page: Page) {
  await page.route("**/api/v1/auth/me", jsonRoute(user));
  await page.route("**/api/v1/kubernetes/summary", jsonRoute(clusterSummary));
  await page.route("**/api/v1/incidents/incident-1", async (route) => {
    if (route.request().method() === "PATCH") {
      await route.fulfill({ json: { ...incident, resolution: "Smoke test resolution." } });
      return;
    }
    await route.fulfill({ json: incident });
  });
  await page.route("**/api/v1/incidents?**", jsonRoute({ total: 1, limit: 100, offset: 0, items: [incident] }));
  await page.route("**/api/v1/analytics/overview?**", jsonRoute(analyticsOverview));
  await page.route("**/api/v1/ai/analyses?**", jsonRoute(aiAnalyses));
}

function jsonRoute(body: unknown) {
  return async (route: Route) => {
    await route.fulfill({ json: body });
  };
}

const user = {
  id: "user-1",
  email: "demo@kubesight.local",
  full_name: "KubeSight Demo",
  role: "admin",
  is_active: true,
  created_at: now,
  updated_at: now,
};

const clusterSummary = {
  total_pods: 12,
  running_pods: 10,
  pending_pods: 1,
  failed_pods: 1,
  restart_count: 9,
};

const incident = {
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
  first_seen_at: now,
  last_seen_at: now,
  resolved_at: null,
  created_at: now,
  updated_at: now,
};

const aiAnalyses = {
  items: [
    {
      id: "analysis-1",
      incident_id: "incident-1",
      pod_id: null,
      model_name: "llama3.2",
      question: null,
      response: "The pod is likely failing because startup work exceeds probe limits.",
      created_at: now,
    },
  ],
};

const analyticsOverview = {
  days: 30,
  generated_at: now,
  total_incidents: 4,
  open_incidents: 1,
  critical_incidents: 1,
  resolved_incidents: 3,
  incident_trends: [
    { date: "2026-01-01", total: 1, critical: 1, warning: 0, info: 0 },
    { date: "2026-01-02", total: 3, critical: 0, warning: 2, info: 1 },
  ],
  resource_trends: [
    {
      sampled_at: "2026-01-02T03:00:00Z",
      cpu_millicores: 420,
      memory_mebibytes: 850,
      restart_count: 8,
      health_score: 88,
    },
    {
      sampled_at: now,
      cpu_millicores: 510,
      memory_mebibytes: 920,
      restart_count: 9,
      health_score: 83,
    },
  ],
  severity_distribution: [
    { label: "critical", value: 1 },
    { label: "warning", value: 2 },
    { label: "info", value: 1 },
  ],
  status_distribution: [
    { label: "open", value: 1 },
    { label: "resolved", value: 3 },
  ],
  incident_type_distribution: [
    { label: "crash_loop_back_off", value: 2 },
    { label: "high_memory", value: 1 },
  ],
  top_failing_pods: [
    {
      namespace: "payments",
      pod_name: "payment-service-7f89",
      incident_count: 3,
      critical_count: 1,
      last_seen_at: now,
    },
  ],
  top_cpu_pods: [
    {
      namespace: "payments",
      pod_name: "payment-service-7f89",
      cpu_millicores: 510,
      memory_mebibytes: 920,
      restart_count: 9,
      health_score: 83,
    },
  ],
  top_memory_pods: [
    {
      namespace: "payments",
      pod_name: "payment-service-7f89",
      cpu_millicores: 510,
      memory_mebibytes: 920,
      restart_count: 9,
      health_score: 83,
    },
  ],
  top_restarting_pods: [
    {
      namespace: "payments",
      pod_name: "payment-service-7f89",
      cpu_millicores: 510,
      memory_mebibytes: 920,
      restart_count: 9,
      health_score: 83,
    },
  ],
};

import { test, expect, type Page, type Route } from "@playwright/test";

const BASE = process.env.E2E_BASE_URL ?? "http://localhost:3001";

/* ─── Mock Data ──────────────────────────────────────────────── */

const MOCK_MONITORS = [
  {
    id: "mon-aaa-111",
    name: "Nike Brand Monitor",
    keywords: ["nike", "just do it", "swoosh"],
    boolean_query: null,
    sources: ["tiktok", "instagram", "youtube"],
    competitor_brands: ["adidas", "puma"],
    is_active: true,
    created_at: new Date(Date.now() - 7 * 86400000).toISOString(),
    updated_at: new Date().toISOString(),
    next_run_at: new Date(Date.now() + 3600000).toISOString(),
    last_run_status: "completed",
    last_run_completed_at: new Date(Date.now() - 1800000).toISOString(),
    last_run_error: null,
    alert_count_24h: 3,
    mention_count: 142,
  },
  {
    id: "mon-bbb-222",
    name: "Competitor Watch",
    keywords: ["adidas", "puma", "under armour"],
    boolean_query: "(adidas OR puma) NOT collab",
    sources: ["tiktok"],
    competitor_brands: [],
    is_active: true,
    created_at: new Date(Date.now() - 14 * 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    next_run_at: null,
    last_run_status: "failed",
    last_run_completed_at: new Date(Date.now() - 86400000).toISOString(),
    last_run_error: "Rate limited by source",
    alert_count_24h: 0,
    mention_count: 57,
  },
];

const MOCK_MENTIONS = [
  {
    id: "mention-1",
    source: "tiktok",
    source_id: "tt123456",
    author_name: "SneakerFan99",
    author_handle: "sneakerfan99",
    content: "Just saw the new Nike Air Max campaign — so fire! The just do it slogan is timeless. #nike #sneakers",
    url: "https://tiktok.com/@sneakerfan99/video/123456",
    published_at: new Date(Date.now() - 3600000).toISOString(),
    sentiment_score: 0.85,
    sentiment_label: "positive",
    intent: "recommendation",
    engagement_total: 1250,
    reach_estimate: 50000,
    language: "en",
    geo_country: "US",
    media_urls: ["https://example.com/thumb1.jpg"],
    metadata: {},
  },
  {
    id: "mention-2",
    source: "instagram",
    source_id: "ig789012",
    author_name: null,
    author_handle: "fitness_daily",
    content: "Nike quality has gone downhill lately. My new shoes fell apart after 2 weeks. Not worth the price anymore.",
    url: "https://instagram.com/p/ig789012",
    published_at: new Date(Date.now() - 7200000).toISOString(),
    sentiment_score: -0.72,
    sentiment_label: "negative",
    intent: "complaint",
    engagement_total: 340,
    reach_estimate: 12000,
    language: "en",
    geo_country: "GB",
    media_urls: [],
    metadata: {},
  },
  {
    id: "mention-3",
    source: "youtube",
    source_id: "yt345678",
    author_name: "TechReviewer",
    author_handle: "techreviewer",
    content: "Comparing Nike vs Adidas running shoes — which one is actually better for marathon training?",
    url: "https://youtube.com/watch?v=345678",
    published_at: new Date(Date.now() - 14400000).toISOString(),
    sentiment_score: 0.1,
    sentiment_label: "neutral",
    intent: null,
    engagement_total: 5600,
    reach_estimate: 200000,
    language: "en",
    geo_country: "US",
    media_urls: [],
    metadata: {},
  },
];

const MOCK_PROFILE = {
  id: "e2e-user-id",
  email: "test@example.com",
  tier: "pro",
  subscription_status: "active",
  follower_count: null,
};

/* ─── Route Setup ────────────────────────────────────────────── */

async function setupMocks(page: Page) {
  await page.route(/\/v1\//, async (route: Route) => {
    const url = route.request().url();
    const path = new URL(url).pathname;

    // Mentions endpoint: /v1/monitors/{id}/mentions
    if (path.match(/\/v1\/monitors\/[^/]+\/mentions/)) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: MOCK_MENTIONS, total: MOCK_MENTIONS.length }),
      });
    }

    // Run now endpoint: /v1/monitors/{id}/run
    if (path.match(/\/v1\/monitors\/[^/]+\/run/)) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "enqueued", monitor_id: "mon-aaa-111" }),
      });
    }

    // Single monitor detail: /v1/monitors/{id}
    if (path.match(/\/v1\/monitors\/[a-z0-9-]+$/)) {
      const id = path.split("/").pop();
      const monitor = MOCK_MONITORS.find((m) => m.id === id);
      return route.fulfill({
        status: monitor ? 200 : 404,
        contentType: "application/json",
        body: JSON.stringify(monitor ?? { error: { code: "not_found", message: "Monitor not found" } }),
      });
    }

    const responses: Record<string, unknown> = {
      "/v1/auth/profile": MOCK_PROFILE,
      "/v1/conversations": [],
      "/v1/usage": { messages_used: 5, messages_limit: 20, tier: "pro" },
      "/v1/monitors": MOCK_MONITORS,
      "/v1/preferences": { theme: "dark" },
    };

    const body = responses[path] ?? {};
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

/* ─── Tests ──────────────────────────────────────────────────── */

test.describe("Monitoring: Navigation & Layout", () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
  });

  test("NavigationRail has Monitoring link with correct href", async ({ page }) => {
    await page.goto(`${BASE}/dashboard?__e2e_auth=1`);
    const link = page.getByRole("link", { name: "Monitoring" });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "/dashboard/monitoring");
  });

  test("Canvas tab bar has Monitor tab", async ({ page }) => {
    await page.goto(`${BASE}/dashboard?__e2e_auth=1`);
    await expect(page.getByRole("tab", { name: "Monitor" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Discover" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Studio" })).toBeVisible();
  });

  test("clicking Monitoring nav link navigates to monitoring page", async ({ page }) => {
    await page.goto(`${BASE}/dashboard?__e2e_auth=1`);
    await page.getByRole("link", { name: "Monitoring" }).click();
    await expect(page).toHaveURL(/\/dashboard\/monitoring/);
  });
});

test.describe("Monitoring Page: Full Layout", () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
  });

  test("monitoring page renders header and summary stats", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1`);
    // Use heading role to avoid matching nav link text
    await expect(page.getByRole("heading", { name: "Monitoring" })).toBeVisible();
    // Summary chips
    await expect(page.getByText("Monitors")).toBeVisible();
    await expect(page.getByText("Alerts (24h)")).toBeVisible();
    await expect(page.getByText("Total Mentions")).toBeVisible();
  });

  test("monitoring page renders monitor cards", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1`);
    await expect(page.getByText("Nike Brand Monitor")).toBeVisible();
    await expect(page.getByText("Competitor Watch")).toBeVisible();
    // Sources — use first() since tiktok appears on both cards
    await expect(page.getByText("tiktok").first()).toBeVisible();
    await expect(page.getByText("instagram").first()).toBeVisible();
    // Mention counts
    await expect(page.getByText("142 mentions")).toBeVisible();
    await expect(page.getByText("57 mentions")).toBeVisible();
  });

  test("failed monitor shows error message", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1`);
    await expect(page.getByText("Rate limited by source")).toBeVisible();
  });

  test("monitor with alerts shows alert count", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1`);
    await expect(page.getByText("3 alerts (24h)")).toBeVisible();
  });
});

test.describe("Monitoring Page: Monitor Detail", () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
  });

  test("clicking monitor card shows detail panel with actions", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1`);
    await page.getByText("Nike Brand Monitor").first().click();
    // Detail panel — use exact: true for the big Run Now button
    await expect(page.getByRole("button", { name: "Run Now", exact: true })).toBeVisible();
    await expect(page.getByText("Investigate with AI")).toBeVisible();
    // Keywords displayed
    await expect(page.getByText(/Keywords:.*nike/)).toBeVisible();
    // Mentions header
    await expect(page.getByText(/Mentions \(/)).toBeVisible();
  });

  test("mention cards render with correct data", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1`);
    await page.getByText("Nike Brand Monitor").first().click();

    // Wait for mentions to load
    await expect(page.getByText("@sneakerfan99")).toBeVisible();

    // Check mention content
    await expect(page.getByText(/Just saw the new Nike Air Max campaign/)).toBeVisible();
    await expect(page.getByText(/Nike quality has gone downhill/)).toBeVisible();
    await expect(page.getByText(/Comparing Nike vs Adidas/)).toBeVisible();

    // Check sentiment labels
    await expect(page.getByText("positive").first()).toBeVisible();
    await expect(page.getByText("negative").first()).toBeVisible();
    await expect(page.getByText("neutral").first()).toBeVisible();

    // Check intent labels
    await expect(page.getByText("recommendation")).toBeVisible();
    await expect(page.getByText("complaint")).toBeVisible();

    // Check engagement
    await expect(page.getByText("1,250 engagement")).toBeVisible();
    await expect(page.getByText("5,600 engagement")).toBeVisible();

    // Check author handles
    await expect(page.getByText("@fitness_daily")).toBeVisible();
    await expect(page.getByText("@techreviewer")).toBeVisible();
  });

  test("mention source links render correctly", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1`);
    await page.getByText("Nike Brand Monitor").first().click();
    await expect(page.getByText("@sneakerfan99")).toBeVisible();

    // Source links should exist
    const sourceLinks = page.getByText("Source");
    expect(await sourceLinks.count()).toBeGreaterThan(0);
  });
});

test.describe("Canvas: Monitor Workbench", () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
  });

  test("Monitor tab shows workbench with monitor picker", async ({ page }) => {
    await page.goto(`${BASE}/dashboard?__e2e_auth=1`);
    await page.getByRole("tab", { name: "Monitor" }).click();
    await page.waitForTimeout(500);

    const panel = page.getByRole("tabpanel", { name: "Monitor" });
    await expect(panel).toBeVisible();

    // Monitor card in the picker (use button role to distinguish from select option)
    await expect(panel.getByRole("button", { name: /Nike Brand Monitor/ })).toBeVisible();
  });

  test("selecting monitor in workbench shows quick actions", async ({ page }) => {
    await page.goto(`${BASE}/dashboard?__e2e_auth=1`);
    await page.getByRole("tab", { name: "Monitor" }).click();
    await page.waitForTimeout(500);

    const panel = page.getByRole("tabpanel", { name: "Monitor" });
    // Click the Nike monitor button (not the select option)
    await panel.getByRole("button", { name: /Nike Brand Monitor/ }).click();
    await page.waitForTimeout(500);

    // Quick action buttons should appear
    await expect(panel.getByText("Ask AI to triage")).toBeVisible();
    await expect(panel.getByText("Summarize spike")).toBeVisible();
    await expect(panel.getByText("View analytics")).toBeVisible();
  });

  test("workbench shows Run button after selecting monitor", async ({ page }) => {
    await page.goto(`${BASE}/dashboard?__e2e_auth=1`);
    await page.getByRole("tab", { name: "Monitor" }).click();
    await page.waitForTimeout(500);

    const panel = page.getByRole("tabpanel", { name: "Monitor" });
    await panel.getByRole("button", { name: /Nike Brand Monitor/ }).click();
    await page.waitForTimeout(300);

    // Run button in workbench summary bar
    await expect(panel.getByRole("button", { name: /Run/ })).toBeVisible();
  });
});

test.describe("Monitoring Page: Preselection via URL", () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
  });

  test("preselects monitor from URL search param", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1&monitor=mon-aaa-111`);
    // Should auto-select Nike monitor — detail panel has the big "Run Now" button
    await expect(page.getByRole("button", { name: "Run Now", exact: true })).toBeVisible();
    await expect(page.getByText(/Keywords:.*nike/)).toBeVisible();
  });

  test("shows not-found banner for unknown monitor ID", async ({ page }) => {
    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1&monitor=mon-unknown-999`);
    // Banner text: "Monitor mon-unkn… not found" (8-char slice + unicode ellipsis)
    await expect(page.getByText(/mon-unkn.*not found/)).toBeVisible();
  });
});

test.describe("Monitoring: Empty State", () => {
  test("shows empty state when no monitors exist", async ({ page }) => {
    await page.route(/\/v1\//, async (route: Route) => {
      const path = new URL(route.request().url()).pathname;
      const responses: Record<string, unknown> = {
        "/v1/auth/profile": MOCK_PROFILE,
        "/v1/conversations": [],
        "/v1/usage": { messages_used: 5, messages_limit: 20, tier: "pro" },
        "/v1/monitors": [],
        "/v1/preferences": { theme: "dark" },
      };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(responses[path] ?? {}),
      });
    });

    await page.goto(`${BASE}/dashboard/monitoring?__e2e_auth=1`);
    await expect(page.getByText("No monitors yet")).toBeVisible();
    await expect(page.getByText("Go to Chat")).toBeVisible();
  });

  test("canvas workbench shows empty state when no monitors", async ({ page }) => {
    await page.route(/\/v1\//, async (route: Route) => {
      const path = new URL(route.request().url()).pathname;
      const responses: Record<string, unknown> = {
        "/v1/auth/profile": MOCK_PROFILE,
        "/v1/conversations": [],
        "/v1/usage": { messages_used: 5, messages_limit: 20, tier: "pro" },
        "/v1/monitors": [],
        "/v1/preferences": { theme: "dark" },
      };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(responses[path] ?? {}),
      });
    });

    await page.goto(`${BASE}/dashboard?__e2e_auth=1`);
    await page.getByRole("tab", { name: "Monitor" }).click();
    await page.waitForTimeout(500);

    await expect(page.getByText("Brand Monitoring")).toBeVisible();
    await expect(page.getByText("Create Monitor via Chat")).toBeVisible();
  });
});

test.describe("Monitoring: Capability Discovery", () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
  });

  test("at least one monitoring capability shows in welcome", async ({ page }) => {
    await page.goto(`${BASE}/dashboard?__e2e_auth=1`);
    await page.waitForTimeout(500);

    const monitoringCapNames = [
      /Create Monitor/i,
      /My Monitors/i,
      /Search Monitor Mentions/i,
      /Action Packet/i,
      /Analyze Mention Video/i,
      /Save Mentions/i,
      /Monitor Analytics/i,
    ];

    let found = false;
    for (const pattern of monitoringCapNames) {
      const btn = page.getByRole("button", { name: pattern });
      if (await btn.isVisible().catch(() => false)) {
        found = true;
        break;
      }
    }
    expect(found).toBe(true);
  });
});

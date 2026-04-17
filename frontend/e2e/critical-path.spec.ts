import { expect, test, gotoAuthed, injectBearerAuth } from "./fixtures";

test("session guard redirects unauthenticated users to /login", async ({ page }) => {
  await page.goto("/search");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Sign in to Freddy" })).toBeVisible();
});

test("old page routes redirect to canvas home", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);

  for (const route of ["/search", "/trends", "/fraud"]) {
    await gotoAuthed(page, route);
    await expect(page).toHaveURL(/\/dashboard(\?|$)/);
    await expect(page.getByRole("heading", { name: "Freddy" })).toBeVisible();
  }
});

test("canvas layout renders for authenticated user", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, "/dashboard");

  await expect(page.getByRole("heading", { name: "Freddy" })).toBeVisible();
  await expect(page.getByText("Search, analyze, create")).toBeVisible();
  await expect(page.getByRole("button", { name: "New Chat" })).toBeVisible();
  await expect(page.getByRole("toolbar", { name: "Workspace view" })).toBeVisible();
});

test("desktop split shell collapses chat via dead-zone release and restores from gutter", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, "/dashboard");

  const separator = page.getByRole("separator", { name: "Resize chat and canvas panels" });
  await expect(separator).toBeVisible();

  const box = await separator.boundingBox();
  expect(box).not.toBeNull();
  if (!box) throw new Error("Resize handle did not render");

  const startX = box.x + box.width / 2;
  const startY = box.y + box.height / 2;

  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX - 36, startY);

  await expect(page.getByText("Release to hide chat")).toBeVisible();

  await page.mouse.up();

  const restoreGutter = page.getByLabel("Restore chat panel");
  await expect(restoreGutter).toBeVisible();

  await restoreGutter.click();
  await expect(separator).toBeVisible();
});

test("chat stream journey renders tool and text events", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);

  const CONV_ID = "e2e-stream-test-conv";

  // Mock conversation GET so loadMessages doesn't 404 and navigate away
  await page.route(`**/v1/conversations/${CONV_ID}`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: CONV_ID,
        title: "E2E Test Conversation",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
    }),
  );

  // Mock SSE stream to bypass Vite proxy buffering.
  // Navigating to /dashboard/c/${CONV_ID} directly means send() fires from user input (not useEffect),
  // so React StrictMode double-effect cleanup cannot abort the stream mid-processing.
  const sseBody = [
    "event: tool_call\n",
    'data: {"tool":"fake_search","args":{"query":"search fitness"},"iteration":0}\n',
    "\n",
    "event: tool_result\n",
    'data: {"tool":"fake_search","summary":"Found results","iteration":0}\n',
    "\n",
    "event: text_delta\n",
    'data: {"text":"Deterministic fake response: search fitness"}\n',
    "\n",
    "event: done\n",
    'data: {"finish_reason":"complete","text":"Deterministic fake response: search fitness","cost_usd":0,"gemini_calls":1,"actions_taken":[]}\n',
    "\n",
  ].join("");
  await page.route("**/v1/agent/chat/stream", (route) =>
    route.fulfill({ status: 200, contentType: "text/event-stream", body: sseBody }),
  );

  // Legacy deep-link should still redirect to canonical /dashboard/c/:id.
  await gotoAuthed(page, `/c/${CONV_ID}`);
  await expect(page).toHaveURL(new RegExp(`/dashboard/c/${CONV_ID}`));

  // When the user types, handleSend → send() fires as a user action (StrictMode-safe)
  await gotoAuthed(page, `/dashboard/c/${CONV_ID}`);
  const input = page.getByPlaceholder("Ask about any video, creator, or trend...");
  await expect(input).toBeVisible({ timeout: 10000 });

  await input.fill("search fitness");
  await input.press("Enter");

  await expect(page.getByText("fake_search")).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(/Deterministic fake response/i)).toBeVisible({ timeout: 15000 });
});

test("settings logout calls backend and redirects to /login", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, "/dashboard/settings");

  const logoutResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/v1/auth/logout") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Sign out" }).click();

  expect((await logoutResponsePromise).status()).toBe(204);
  await expect(page).toHaveURL(/\/login$/);
});

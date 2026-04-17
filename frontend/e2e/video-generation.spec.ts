import { expect, test, gotoAuthed, injectBearerAuth } from "./fixtures";

const conversationId = process.env.E2E_VIDEO_CONVERSATION_ID;

test.beforeEach(() => {
  if (!conversationId) {
    throw new Error("Missing E2E_VIDEO_CONVERSATION_ID");
  }
});

test("project preview render and recompose flow works in studio", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, `/dashboard/c/${conversationId}`);

  await page.getByRole("tab", { name: "Studio" }).click();
  await expect(page.getByRole("heading", { name: "E2E Storyboard Project" })).toBeVisible();

  await page.getByRole("button", { name: "Preview anchor" }).click();
  await expect(page.getByAltText("Hook")).toBeVisible();

  await page.getByRole("button", { name: "Preview remaining" }).click();
  await expect(page.getByAltText("Proof")).toBeVisible();
  await expect(page.getByAltText("Call to action")).toBeVisible();

  for (const sceneTitle of ["Hook", "Proof", "Call to action"]) {
    await page.getByRole("button", { name: `Approve preview for ${sceneTitle}` }).click();
    await expect(page.getByRole("button", { name: `Unapprove preview for ${sceneTitle}` })).toBeVisible({
      timeout: 15_000,
    });
  }

  await expect(page.getByRole("button", { name: "Render project" })).toBeEnabled();
  await page.getByRole("button", { name: "Render project" }).click();
  await expect(page.locator("video")).toBeVisible({ timeout: 30_000 });

  await page.getByRole("button", { name: "Regenerate Hook" }).click();
  await expect(page.getByText("Render stale")).toBeVisible();

  await page.getByRole("button", { name: "Approve preview for Hook" }).click();
  await expect(page.getByRole("button", { name: "Recompose" })).toBeEnabled();
  await page.getByRole("button", { name: "Recompose" }).click();
  await expect(page.locator("video")).toBeVisible({ timeout: 30_000 });
});

test("library analysis detail shows seeded summary, creative patterns, and demographics", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, "/dashboard/library");

  await expect(page.getByRole("heading", { name: "Analysis Library" })).toBeVisible();
  await page.getByRole("button", { name: /Seeded Library Analysis/ }).click();

  await expect(page.getByText("Deterministic fake analysis summary for browser verification.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Creative Patterns" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Demographics" })).toBeVisible();
  await expect(page.getByText("tutorial")).toBeVisible();
  await expect(page.getByText("18–24")).toBeVisible();
});

test("chat-first storyboard pipeline reaches final render on the canvas", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, `/dashboard/c/${conversationId}`);

  const studioTab = page.getByRole("tab", { name: "Studio" });
  const studioPanel = page.getByRole("tabpanel", { name: "Studio" });
  const chatLog = page.getByRole("log", { name: "Chat messages" });
  const chatInput = () => page.locator("textarea").first();
  await expect(chatInput()).toBeVisible({ timeout: 10_000 });

  await chatInput().fill("Create a storyboard about creator marketing in a cinematic style");
  await chatInput().press("Enter");
  await expect(chatLog.getByText("create_storyboard")).toBeVisible({ timeout: 15_000 });
  await studioTab.click();
  await expect(studioPanel.getByRole("heading", { level: 3, name: /creator marketing in a cinematic style/i })).toBeVisible({
    timeout: 15_000,
  });

  await chatInput().fill("Preview the anchor scene");
  await chatInput().press("Enter");
  await expect(chatLog.getByText("preview_cadre").first()).toBeVisible({ timeout: 15_000 });
  await expect(studioPanel.locator("article img")).toHaveCount(1, { timeout: 15_000 });

  await chatInput().fill("Preview the remaining scenes");
  await chatInput().press("Enter");
  await expect(chatLog.getByText("The remaining storyboard previews are ready for review.").first()).toBeVisible({
    timeout: 15_000,
  });
  await expect(studioPanel.locator("article img")).toHaveCount(2, { timeout: 15_000 });

  await chatInput().fill("Approve all previews");
  await chatInput().press("Enter");
  await expect(chatLog.getByText("All ready previews are approved. You can render the final video now.").first()).toBeVisible({
    timeout: 15_000,
  });
  await expect(studioPanel.getByRole("button", { name: "Render project" })).toBeEnabled({ timeout: 15_000 });

  await chatInput().fill("Render the video");
  await chatInput().press("Enter");
  await expect(chatLog.getByText("generate_video_from_inspiration").first()).toBeVisible({ timeout: 15_000 });
  await expect(studioPanel.locator("video").first()).toBeVisible({ timeout: 30_000 });

  await chatInput().fill("Regenerate the first scene");
  await chatInput().press("Enter");
  await expect(chatLog.getByText("The first storyboard scene has a fresh preview.").first()).toBeVisible({
    timeout: 15_000,
  });
  await expect(studioPanel.getByText("Render stale")).toBeVisible({ timeout: 15_000 });

  await chatInput().fill("Approve all previews");
  await chatInput().press("Enter");
  await expect(chatLog.getByText("All ready previews are approved. You can render the final video now.").first()).toBeVisible({
    timeout: 15_000,
  });
  await expect(studioPanel.getByRole("button", { name: "Recompose" })).toBeEnabled({ timeout: 15_000 });

  await chatInput().fill("Recompose the video");
  await chatInput().press("Enter");
  await expect(chatLog.getByText("generate_video_from_inspiration").first()).toBeVisible({ timeout: 15_000 });
  await expect(studioPanel.locator("video").first()).toBeVisible({ timeout: 30_000 });
});

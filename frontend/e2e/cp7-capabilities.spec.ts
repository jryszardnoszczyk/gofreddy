import { expect, test, gotoAuthed, injectBearerAuth } from "./fixtures";

// PR-031: Dedicated analysis/creator pages were removed and replaced with the
// chat-canvas architecture. These tests verify redirect behaviour and that the
// new layout renders correctly.

test("cp7 old analyze route redirects to canvas home", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, "/analyze");

  // React Router legacy redirect should land on canonical dashboard path.
  await expect(page).toHaveURL(/\/dashboard(\?|$)/);
  await expect(page.getByRole("heading", { name: "Freddy" })).toBeVisible();
});

test("cp7 old creators route redirects to canvas home", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, "/creators");

  await expect(page).toHaveURL(/\/dashboard(\?|$)/);
  await expect(page.getByRole("heading", { name: "Freddy" })).toBeVisible();
});

test("cp7 canvas layout renders chat panel and sidebar for pro user", async ({ page, tokens }) => {
  await injectBearerAuth(page, tokens.pro);
  await gotoAuthed(page, "/dashboard");

  await expect(page.getByRole("heading", { name: "Freddy" })).toBeVisible();
  await expect(page.getByRole("button", { name: "New Chat" })).toBeVisible();
  await expect(page.getByText("Search, analyze, create")).toBeVisible();
  await expect(page.getByRole("toolbar", { name: "Workspace view" })).toBeVisible();
});

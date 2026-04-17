import { expect, test as base, type Page } from "@playwright/test";

export type E2ETokens = {
  free: string;
  pro: string;
};

export const test = base.extend<{ tokens: E2ETokens }>({
  tokens: async ({}, use) => {
    const free = process.env.E2E_FREE_TOKEN;
    const pro = process.env.E2E_PRO_TOKEN;
    if (!free || !pro) {
      throw new Error("Missing E2E_FREE_TOKEN or E2E_PRO_TOKEN for critical-path tests");
    }
    await use({ free, pro });
  },
});

export { expect };

export async function injectBearerAuth(page: Page, token: string): Promise<void> {
  await page.setExtraHTTPHeaders({ authorization: `Bearer ${token}` });
}

export async function gotoAuthed(page: Page, path: string): Promise<void> {
  const separator = path.includes("?") ? "&" : "?";
  await page.goto(`${path}${separator}__e2e_auth=1`);
}

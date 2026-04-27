export const ROUTES = {
  landing: "/",
  login: "/login",
  authCallback: "/auth/callback",

  dashboard: "/dashboard",
  dashboardSettingsChild: "settings",
  dashboardSettings: "/dashboard/settings",
  dashboardSessionsChild: "sessions",
  dashboardSessions: "/dashboard/sessions",
} as const;

export const LEGACY_PRODUCT_ROUTES = [
  "/analyze",
  "/search",
  "/creators",
  "/trends",
  "/fraud",
  "/deepfake",
  "/brands",
  "/chat",
  "/analysis/:id/*",
  "/creators/:platform/:username/*",
] as const;

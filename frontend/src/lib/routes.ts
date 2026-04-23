export const ROUTES = {
  landing: "/",
  pricing: "/pricing",
  login: "/login",
  authCallback: "/auth/callback",

  dashboard: "/dashboard",
  dashboardConversationChild: "c/:conversationId",
  dashboardSettingsChild: "settings",
  dashboardUsageChild: "usage",
  dashboardLibraryChild: "library",
  dashboardMonitoringChild: "monitoring",
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

export function toDashboardConversationPath(conversationId: string): string {
  return `/dashboard/c/${conversationId}`;
}

export function toLegacyConversationPath(conversationId: string): string {
  return `/c/${conversationId}`;
}

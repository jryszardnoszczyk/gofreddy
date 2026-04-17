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
  dashboardConversationPattern: "/dashboard/c/:conversationId",
  dashboardSettings: "/dashboard/settings",
  dashboardUsage: "/dashboard/usage",
  dashboardLibrary: "/dashboard/library",
  dashboardMonitoring: "/dashboard/monitoring",
  dashboardSessionsChild: "sessions",
  dashboardSessions: "/dashboard/sessions",

  legacyConversationPattern: "/c/:conversationId",
  legacySettings: "/settings",
  legacyUsage: "/usage",
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

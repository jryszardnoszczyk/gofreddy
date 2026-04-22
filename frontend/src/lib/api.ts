import {
  getMeV1AuthMeGet,
  logoutV1AuthLogoutPost,
  type AuthMeResponse,
} from "./generated";
import type { Auth } from "./generated/client";
import { client } from "./generated/client.gen";
import { supabase } from "./supabase";

const BASE = import.meta.env.VITE_API_URL ?? "";

type GeneratedResult<T> = {
  data?: T;
  error?: unknown;
  response?: Response;
};

export type AuthProfile = AuthMeResponse;

type ExtractedError = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

client.setConfig({
  baseUrl: BASE || undefined,
  responseStyle: "fields",
  throwOnError: false,
  auth: async (auth: Auth) => {
    if (auth.type === "http" && auth.scheme === "bearer") {
      return await getAccessToken();
    }
    return undefined;
  },
});

function getE2EBypassAccessToken(): string | undefined {
  if (import.meta.env.VITE_E2E_BYPASS_AUTH !== "1" || import.meta.env.DEV !== true) {
    return undefined;
  }
  if (typeof window === "undefined") {
    return undefined;
  }
  const hostname = window.location.hostname;
  const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
  if (!isLocalhost) {
    return undefined;
  }
  // NOTE: Removed __e2e_auth URL param check — it breaks after internal navigation
  // (e.g., /dashboard → /dashboard/c/{id}) which drops query params.
  // The VITE_E2E_BYPASS_AUTH env var + DEV + localhost guards are sufficient.
  const token = import.meta.env.VITE_E2E_BYPASS_ACCESS_TOKEN;
  return typeof token === "string" && token.trim() ? token.trim() : undefined;
}

async function getAccessToken(): Promise<string | undefined> {
  const bypassToken = getE2EBypassAccessToken();
  if (bypassToken) {
    return bypassToken;
  }
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function pickString(record: Record<string, unknown>, keys: string[]): string | undefined {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }
  return undefined;
}

function extractError(error: unknown, status: number, statusText: string): ExtractedError {
  const fallback: ExtractedError = {
    code: `http_${status}`,
    message: statusText || "Request failed",
  };

  if (!error) return fallback;
  if (typeof error === "string") {
    return { ...fallback, message: error };
  }

  if (!isRecord(error)) {
    return fallback;
  }

  const envelope = isRecord(error.error) ? error.error : undefined;
  const source = envelope ?? error;

  const code = pickString(source, ["code"]) ?? fallback.code;
  const message = pickString(source, ["message"]) ?? fallback.message;

  return { code, message, details: source };
}

function invalidResponse(message: string): ApiError {
  return new ApiError(500, "invalid_response", message);
}

async function ensureSuccessfulResponse(result: GeneratedResult<unknown>): Promise<Response> {
  const response = result.response;

  if (!(response instanceof Response)) {
    throw new ApiError(0, "network_error", "Network request failed");
  }

  if (!response.ok) {
    await handleErrorStatus(response);

    const parsed = extractError(result.error, response.status, response.statusText);
    throw new ApiError(response.status, parsed.code, parsed.message, parsed.details);
  }

  return response;
}

async function resolveJsonResult<T>(result: GeneratedResult<T>, endpointName: string): Promise<T> {
  await ensureSuccessfulResponse(result);

  if (result.data === undefined) {
    throw invalidResponse(`Invalid ${endpointName} response: expected JSON payload`);
  }

  return result.data;
}

export async function resolveNoContentResult(
  result: GeneratedResult<unknown>,
  endpointName: string,
): Promise<void> {
  const response = await ensureSuccessfulResponse(result);
  if (response.status !== 204 && response.status !== 205) {
    throw invalidResponse(
      `Invalid ${endpointName} response: expected 204/205 no-content status`,
    );
  }
}

export class ApiError extends Error {
  status: number;
  code: string;
  details?: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// ─── Token Refresh (single-flight) ───────────────────────────────────────

let refreshPromise: Promise<boolean> | null = null;

async function handleSessionExpired(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const { error } = await Promise.race([
        supabase.auth.refreshSession(),
        new Promise<{ error: Error }>((resolve) =>
          setTimeout(() => resolve({ error: new Error("refresh_timeout") }), 5000)
        ),
      ]);
      return !error;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

async function forceSignOut(): Promise<never> {
  await supabase.auth.signOut();
  window.location.href = "/login";
  throw new ApiError(401, "session_expired", "Session expired");
}

// ─── Rate Limit Helpers ──────────────────────────────────────────────────

export function extractRetryAfter(response: Response): number | null {
  const header = response.headers.get("Retry-After");
  if (!header) return null;
  const seconds = parseInt(header, 10);
  return Number.isFinite(seconds) ? Math.max(1, seconds) : null;
}

/**
 * Handle 429 (rate limit) and 401 (session expired) responses.
 * Throws ApiError for 429. For 401, attempts token refresh then throws.
 * Returns false if the status was not 429 or 401 (caller should handle other errors).
 */
async function handleErrorStatus(response: Response): Promise<never | false> {
  if (response.status === 429) {
    const retryAfter = extractRetryAfter(response);
    const message = retryAfter
      ? `Rate limit reached. Try again in ${retryAfter} seconds.`
      : "Rate limit reached. Please wait a moment.";
    throw new ApiError(429, "rate_limited", message);
  }

  if (response.status === 401) {
    const refreshed = await handleSessionExpired();
    if (!refreshed) await forceSignOut();
    throw new ApiError(401, "session_refreshed", "Session was refreshed — please retry your request.");
  }

  return false;
}

export async function getAuthProfile(): Promise<AuthProfile> {
  const result = await getMeV1AuthMeGet();
  return resolveJsonResult<AuthProfile>(result, "auth profile");
}

export async function logoutApiSession(): Promise<void> {
  const result = await logoutV1AuthLogoutPost();
  const response = result.response;

  if (!(response instanceof Response)) {
    throw new ApiError(0, "network_error", "Network request failed");
  }

  if (response.status === 401 || response.status === 403) {
    // Session is already invalid at the API layer; local sign-out should continue.
    return;
  }

  await resolveNoContentResult(result, "logout");
}

// ─── API Key Management ───────────────────────────────────────────────────

export interface ApiKeyCreateResult {
  id: string;
  key: string;
  key_prefix: string;
  name: string | null;
}

export interface ApiKeyInfo {
  id: string;
  key_prefix: string;
  name: string | null;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

async function apiKeyFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${BASE}${path}`, { ...init, headers: { ...headers, ...init.headers } });

  if (!res.ok) {
    await handleErrorStatus(res);

    const body = await res.json().catch(() => null);
    const parsed = extractError(body, res.status, res.statusText);
    throw new ApiError(res.status, parsed.code, parsed.message, parsed.details);
  }

  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

export async function createApiKey(name?: string): Promise<ApiKeyCreateResult> {
  return apiKeyFetch<ApiKeyCreateResult>("/v1/api-keys", {
    method: "POST",
    body: JSON.stringify({ name: name || null }),
  });
}

export async function listApiKeys(): Promise<ApiKeyInfo[]> {
  return apiKeyFetch<ApiKeyInfo[]>("/v1/api-keys");
}

export async function revokeApiKey(keyId: string): Promise<void> {
  await apiKeyFetch<unknown>(`/v1/api-keys/${keyId}`, { method: "DELETE" });
}

// ─── Monitor Types ──────────────────────────────────────────────────────

export interface MonitorResponse {
  id: string;
  name: string;
  keywords: string;
  sources: string[];
  is_active: boolean;
  created_at: string;
  competitor_brands?: string[];
}

export interface MonitorSummary {
  id: string;
  name: string;
  keywords: string[];
  boolean_query: string | null;
  sources: string[];
  competitor_brands: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  next_run_at: string | null;
  last_run_status: string | null;
  last_run_completed_at: string | null;
  last_run_error: string | null;
  alert_count_24h: number;
  mention_count: number;
  pending_changes_count: number;
}

export interface ChangelogEntry {
  id: string;
  monitor_id: string;
  change_type: string;
  change_detail: Record<string, unknown>;
  rationale: string;
  autonomy_level: string;
  status: string;
  applied_by: string;
  analysis_run_id: string | null;
  created_at: string;
}

export interface MentionItem {
  id: string;
  source: string;
  source_id: string;
  author_name: string | null;
  author_handle: string | null;
  content: string | null;
  url: string | null;
  published_at: string | null;
  sentiment_score: number | null;
  sentiment_label: string | null;
  intent: string | null;
  engagement_total: number | null;
  reach_estimate: number | null;
  language: string | null;
  geo_country: string | null;
  media_urls: string[];
  metadata: Record<string, unknown>;
}

export interface MentionQueryParams {
  q?: string;
  source?: string;
  sentiment?: string;
  intent?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: string;
  limit?: number;
  offset?: number;
}

export interface MentionQueryResponse {
  data: MentionItem[];
  total: number;
}

export async function createMonitor(data: {
  name: string;
  keywords: string;
  sources: string[];
  boolean_query?: string;
  competitor_brands?: string[];
}): Promise<MonitorResponse> {
  return apiKeyFetch<MonitorResponse>("/v1/monitors", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listMonitors(): Promise<MonitorSummary[]> {
  return apiKeyFetch<MonitorSummary[]>("/v1/monitors");
}

export async function deleteMonitor(id: string): Promise<void> {
  return apiKeyFetch<void>(`/v1/monitors/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export async function runMonitorNow(id: string): Promise<{ status: string; monitor_id: string }> {
  return apiKeyFetch<{ status: string; monitor_id: string }>(`/v1/monitors/${encodeURIComponent(id)}/run`, {
    method: "POST",
  });
}

export async function saveMentionsToWorkspace(
  monitorId: string,
  collectionId: string,
  mentionIds: string[],
  annotations?: Record<string, string>,
): Promise<{ saved_count: number; collection_id: string }> {
  return apiKeyFetch<{ saved_count: number; collection_id: string }>(
    `/v1/monitors/${encodeURIComponent(monitorId)}/mentions/save-to-workspace`,
    {
      method: "POST",
      body: JSON.stringify({
        collection_id: collectionId,
        mention_ids: mentionIds,
        ...(annotations ? { annotations } : {}),
      }),
    },
  );
}

export async function queryMentions(
  monitorId: string,
  params: MentionQueryParams = {},
): Promise<MentionQueryResponse> {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.source) qs.set("source", params.source);
  if (params.sentiment) qs.set("sentiment", params.sentiment);
  if (params.intent) qs.set("intent", params.intent);
  if (params.date_from) qs.set("date_from", params.date_from);
  if (params.date_to) qs.set("date_to", params.date_to);
  if (params.sort_by) qs.set("sort_by", params.sort_by);
  if (params.sort_order) qs.set("sort_order", params.sort_order);
  if (params.limit) qs.set("limit", String(params.limit));
  if (params.offset) qs.set("offset", String(params.offset));

  const query = qs.toString();
  const path = `/v1/monitors/${encodeURIComponent(monitorId)}/mentions${query ? `?${query}` : ""}`;
  return apiKeyFetch<MentionQueryResponse>(path);
}

// ── Changelog (V2 self-optimizing refinement) ──

export async function fetchChangelog(
  monitorId: string,
  limit = 20,
  offset = 0,
): Promise<{ entries: ChangelogEntry[]; total: number }> {
  return apiKeyFetch<{ entries: ChangelogEntry[]; total: number }>(
    `/v1/monitors/${encodeURIComponent(monitorId)}/changelog?limit=${limit}&offset=${offset}`,
  );
}

export async function approveChangelogEntry(
  monitorId: string,
  entryId: string,
): Promise<ChangelogEntry> {
  return apiKeyFetch<ChangelogEntry>(
    `/v1/monitors/${encodeURIComponent(monitorId)}/changelog/${encodeURIComponent(entryId)}/approve`,
    { method: "POST" },
  );
}

export async function rejectChangelogEntry(
  monitorId: string,
  entryId: string,
): Promise<ChangelogEntry> {
  return apiKeyFetch<ChangelogEntry>(
    `/v1/monitors/${encodeURIComponent(monitorId)}/changelog/${encodeURIComponent(entryId)}/reject`,
    { method: "POST" },
  );
}

// ─── Sessions API ─────────────────────────────────────────────────────────

export interface AgentSession {
  id: string;
  client_name: string;
  source: string;
  session_type: string;
  status: string;
  summary: string | null;
  action_count: number;
  total_credits: number;
  started_at: string;
  completed_at: string | null;
  purpose: string | null;
}

export interface ActionLogEntry {
  id: string;
  session_id: string;
  tool_name: string;
  input_summary: Record<string, unknown> | null;
  output_summary: Record<string, unknown> | null;
  duration_ms: number | null;
  cost_credits: number;
  status: string;
  error_code: string | null;
  created_at: string;
}

export async function listSessions(status?: string): Promise<AgentSession[]> {
  const params = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await apiKeyFetch<{ data: AgentSession[] }>(`/v1/sessions${params}`);
  return res.data ?? [];
}

export async function getSessionActions(sessionId: string): Promise<ActionLogEntry[]> {
  const res = await apiKeyFetch<{ data: ActionLogEntry[] }>(
    `/v1/sessions/${encodeURIComponent(sessionId)}/actions`,
  );
  return res.data ?? [];
}

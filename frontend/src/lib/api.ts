import {
  getBillingSummaryV1BillingSummaryGet,
  getMeV1AuthMeGet,
  logoutV1AuthLogoutPost,
  searchV1SearchPost,
  type AuthMeResponse,
  type BillingSummaryResponse,
  type Platform,
  type SearchRequest,
  type SearchResponse,
} from "./generated";
import type { Auth } from "./generated/client";
import { client } from "./generated/client.gen";
import { ROUTES } from "./routes";
import { supabase } from "./supabase";

const BASE = import.meta.env.VITE_API_URL ?? "";

type GeneratedResult<T> = {
  data?: T;
  error?: unknown;
  response?: Response;
};

export type SearchResult = SearchResponse;
export type AuthProfile = AuthMeResponse;

export type {
  Platform,
  SearchRequest,
};

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

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
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

async function resolveNoContentResult(
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

function assertSearchResponse(value: unknown): asserts value is SearchResponse {
  if (!isRecord(value) || !Array.isArray(value.results)) {
    throw invalidResponse("Invalid search response: results must be an array");
  }
}

function assertBillingSummaryResponse(value: unknown): asserts value is BillingSummaryResponse {
  if (!isRecord(value)) {
    throw invalidResponse("Invalid billing summary response: payload must be an object");
  }

  if (
    !isNumber(value.available) ||
    !isNumber(value.included_remaining) ||
    !isNumber(value.promo_remaining) ||
    !isNumber(value.reserved_total) ||
    !isNumber(value.topup_remaining)
  ) {
    throw invalidResponse("Invalid billing summary response: missing required numeric fields");
  }

  if (
    "billing_model_version" in value &&
    value.billing_model_version !== undefined &&
    value.billing_model_version !== "legacy" &&
    value.billing_model_version !== "credits_v1"
  ) {
    throw invalidResponse(
      "Invalid billing summary response: billing_model_version must be 'legacy' or 'credits_v1'",
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
  // F-c-5-7: import ROUTES.login instead of hardcoding so the constant
  // stays the single source of truth for the login URL.
  window.location.href = ROUTES.login;
  throw new ApiError(401, "session_expired", "Session expired");
}

// ─── Rate Limit Helpers ──────────────────────────────────────────────────

function extractRetryAfter(response: Response): number | null {
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


export async function search(request: SearchRequest): Promise<SearchResult> {
  const result = await searchV1SearchPost({ body: request });
  const response = await resolveJsonResult<unknown>(result, "search");
  assertSearchResponse(response);
  return response;
}

export type BillingSummary = BillingSummaryResponse;

export async function getBillingSummary(): Promise<BillingSummary> {
  const result = await getBillingSummaryV1BillingSummaryGet();
  const response = await resolveJsonResult<unknown>(result, "billing summary");
  assertBillingSummaryResponse(response);
  return response;
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

export async function listSessions(
  status?: string,
  clientName?: string,
): Promise<AgentSession[]> {
  const qs: string[] = [];
  if (status) qs.push(`status=${encodeURIComponent(status)}`);
  // F-c-5-2: backend filter is named `client_name` (not `client`); the
  // PortalRedirect emits ?client=<slug> in the URL, SessionsPage maps that
  // to clientName here so the round-trip actually filters.
  if (clientName) qs.push(`client_name=${encodeURIComponent(clientName)}`);
  const params = qs.length ? `?${qs.join("&")}` : "";
  const res = await apiKeyFetch<{ data: AgentSession[] }>(`/v1/sessions${params}`);
  return res.data ?? [];
}

export async function getSessionActions(sessionId: string): Promise<ActionLogEntry[]> {
  const res = await apiKeyFetch<{ data: ActionLogEntry[] }>(
    `/v1/sessions/${encodeURIComponent(sessionId)}/actions`,
  );
  return res.data ?? [];
}

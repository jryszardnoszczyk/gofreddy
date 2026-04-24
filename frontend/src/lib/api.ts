import {
  analyzeCreatorFraudV1FraudAnalyzePost,
  analyzeCreatorV1AnalyzeCreatorPost,
  analyzeVideoForDeepfakeV1DeepfakeAnalyzePost,
  analyzeVideosAsyncV1AnalyzeVideosAsyncPost,
  analyzeVideosV1AnalyzeVideosPost,
  cancelJobV1AnalysisJobsJobIdDelete,
  captureStoriesNowV1StoriesPlatformUsernameCapturePost,
  createTopupCheckoutV1BillingTopupsCheckoutPost,
  getAnalysisV1AnalysisAnalysisIdGet,
  getBillingSummaryV1BillingSummaryGet,
  getBrandAnalysisV1BrandsAnalysisIdGet,
  getCapturedStoriesV1StoriesPlatformUsernameGet,
  getCreativePatternsV1CreativeAnalysisIdGet,
  getCreatorEvolutionV1CreatorsPlatformUsernameEvolutionGet,
  getCreatorProfileV1CreatorsPlatformUsernameGet,
  getDeepfakeAnalysisV1DeepfakeVideoIdGet,
  getDemographicsV1DemographicsAnalysisIdGet,
  getFraudAnalysisV1FraudAnalysisIdGet,
  getJobStatusV1AnalysisJobsJobIdGet,
  getMeV1AuthMeGet,
  getTrendsV1TrendsGet,
  getUsageV1UsageGet,
  listJobsV1AnalysisJobsGet,
  logoutV1AuthLogoutPost,
  searchV1SearchPost,
  type AnalysisJobResponse,
  type AnalysisStatusResponse,
  type AnalyzeCreatorRequest,
  type AnalyzeCreatorResponse,
  type AnalyzeVideosRequest,
  type AnalyzeVideosResponse,
  type AudienceDemographics,
  type AuthMeResponse,
  type BillingSummaryResponse,
  type BrandAnalysis,
  type CaptureResponse,
  type ChatRequest,
  type CheckoutResponse,
  type CreatorProfileResponse,
  type DeepfakeAnalyzeRequest,
  type DeepfakeAnalysisResponse,
  type EvolutionResponse,
  type FraudAnalyzeRequest,
  type FraudAnalysisResponse,
  type FraudStatusResponse,
  type JobCancellationResponse,
  type JobListResponse,
  type JobStatusResponse,
  type Platform,
  type SearchRequest,
  type SearchResponse,
  type StoryResponse,
  type TrendResponse,
  type UsageResponse,
  type VideoAnalysisResult,
} from "./generated";
import type { Auth } from "./generated/client";
import { client } from "./generated/client.gen";
import { supabase } from "./supabase";

const BASE = import.meta.env.VITE_API_URL ?? "";

const AGENT_V2_ENABLED = import.meta.env.VITE_AGENT_V2 === "true";
const AGENT_CHAT_ENDPOINT = AGENT_V2_ENABLED
  ? "/v2/agent/chat/stream"
  : "/v1/agent/chat/stream";

const STREAM_EVENT_TYPES = new Set([
  "thinking",
  "tool_call",
  "tool_result",
  "text_delta",
  "error",
  "done",
  "message",
  "workspace_update",
  "batch_progress",
  "publish_queue_progress",
  "comment_event",
  "approval_notification",
] as const);

type StreamEventType =
  | "thinking"
  | "tool_call"
  | "tool_result"
  | "text_delta"
  | "error"
  | "done"
  | "message"
  | "workspace_update"
  | "batch_progress"
  | "publish_queue_progress"
  | "comment_event"
  | "approval_notification";

type GeneratedResult<T> = {
  data?: T;
  error?: unknown;
  response?: Response;
};

export type VideoAnalysis = VideoAnalysisResult;
export type AnalyzeResponse = AnalyzeVideosResponse;
export type CreatorAnalysisResponse = AnalyzeCreatorResponse;

export type SearchResult = SearchResponse;
export type TrendData = TrendResponse;
export type FraudAnalysis = FraudAnalysisResponse;
export type FraudAnalysisStatus = FraudStatusResponse;
export type DeepfakeResult = DeepfakeAnalysisResponse;
export type UsageData = UsageResponse;
export type AnalysisJobSubmission = AnalysisJobResponse;
export type AnalysisJobs = JobListResponse;
export type AnalysisJobStatus = JobStatusResponse;
export type AnalysisJobCancellation = JobCancellationResponse;
export type AnalysisDetails = AnalysisStatusResponse;
export type DemographicsData = AudienceDemographics;
export type AuthProfile = AuthMeResponse;
export type CreatorProfile = CreatorProfileResponse;
export type CreatorEvolution = EvolutionResponse;
export type StoryCaptureResult = CaptureResponse;
export type StoryItem = StoryResponse;

export type {
  AnalyzeCreatorRequest,
  AnalyzeVideosRequest,
  BrandAnalysis,
  DeepfakeAnalyzeRequest,
  FraudAnalyzeRequest,
  Platform,
  SearchRequest,
};

export interface AnalyzeVideosAsyncOptions {
  forceRefresh?: boolean;
  idempotencyKey?: string;
}

export interface ListJobsParams {
  statuses?: string[];
  limit?: number;
  offset?: number;
}

export interface JobStatusParams {
  includeResults?: boolean;
  resultsLimit?: number;
}


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

function assertSearchResponse(value: unknown): asserts value is SearchResponse {
  if (!isRecord(value) || !Array.isArray(value.results)) {
    throw invalidResponse("Invalid search response: results must be an array");
  }
}

function assertTrendResponse(value: unknown): asserts value is TrendResponse {
  if (!isRecord(value) || !isRecord(value.snapshot) || !isRecord(value.share_of_voice)) {
    throw invalidResponse(
      "Invalid trends response: snapshot and share_of_voice must be objects",
    );
  }
}

function assertUsageResponse(value: unknown): asserts value is UsageResponse {
  if (!isRecord(value)) {
    throw invalidResponse("Invalid usage response: payload must be an object");
  }

  if (
    typeof value.billing_period_start !== "string" ||
    typeof value.billing_period_end !== "string" ||
    !isNumber(value.rate_limit_per_minute) ||
    typeof value.tier !== "string" ||
    !isNumber(value.usage_percent) ||
    !isNumber(value.videos_limit) ||
    !isNumber(value.videos_remaining) ||
    !isNumber(value.videos_used) ||
    ("subscription_status" in value &&
      value.subscription_status !== null &&
      typeof value.subscription_status !== "string")
  ) {
    throw invalidResponse("Invalid usage response: missing required usage fields");
  }
}

function assertAnalyzeResultsResponse(value: unknown, endpointName: string): void {
  if (!isRecord(value) || !Array.isArray(value.results)) {
    throw invalidResponse(`Invalid ${endpointName} response: results must be an array`);
  }

  value.results.forEach((result, resultIndex) => {
    if (
      !isRecord(result) ||
      !isNumber(result.overall_confidence) ||
      result.overall_confidence < 0 ||
      result.overall_confidence > 1 ||
      !Array.isArray(result.risks_detected)
    ) {
      throw invalidResponse(
        `Invalid ${endpointName} response: result[${resultIndex}] missing typed confidence or risks`,
      );
    }

    result.risks_detected.forEach((risk, riskIndex) => {
      if (
        !isRecord(risk) ||
        typeof risk.risk_type !== "string" ||
        !risk.risk_type.trim() ||
        typeof risk.category !== "string" ||
        !risk.category.trim() ||
        typeof risk.severity !== "string" ||
        !risk.severity.trim() ||
        !isNumber(risk.confidence) ||
        risk.confidence < 0 ||
        risk.confidence > 1 ||
        typeof risk.description !== "string" ||
        typeof risk.evidence !== "string"
      ) {
        throw invalidResponse(
          `Invalid ${endpointName} response: risks_detected[${riskIndex}] is not typed`,
        );
      }

      if (
        ("timestamp_start" in risk && risk.timestamp_start !== null && typeof risk.timestamp_start !== "string") ||
        ("timestamp_end" in risk && risk.timestamp_end !== null && typeof risk.timestamp_end !== "string")
      ) {
        throw invalidResponse(
          `Invalid ${endpointName} response: risks_detected[${riskIndex}] timestamps must be string|null`,
        );
      }
    });
  });
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

function assertBrandAnalysisResponse(value: unknown): asserts value is BrandAnalysis {
  if (
    !isRecord(value) ||
    typeof value.video_id !== "string" ||
    !isNumber(value.overall_confidence)
  ) {
    throw invalidResponse(
      "Invalid brand analysis response: missing video_id or overall_confidence",
    );
  }
}

function normalizeStreamPayload(type: StreamEventType, raw: string): string {
  if (type === "message") return raw;
  if (type === "workspace_update" || type === "batch_progress" || type === "publish_queue_progress" || type === "comment_event" || type === "approval_notification") {
    // Pass through as-is — consumers parse these themselves
    return raw;
  }

  try {
    const parsed = JSON.parse(raw);

    if (type === "text_delta") {
      if (isRecord(parsed) && typeof parsed.text === "string") {
        return JSON.stringify({ text: parsed.text });
      }
      return JSON.stringify({ text: raw });
    }

    if (type === "error") {
      if (isRecord(parsed) && typeof parsed.message === "string") {
        return JSON.stringify({
          message: parsed.message,
          recoverable: Boolean(parsed.recoverable),
        });
      }
      return JSON.stringify({ message: raw || "Unexpected stream error", recoverable: false });
    }

    return JSON.stringify(parsed);
  } catch {
    if (type === "text_delta") {
      return JSON.stringify({ text: raw });
    }

    if (type === "error") {
      return JSON.stringify({ message: raw || "Unexpected stream error", recoverable: false });
    }

    return raw;
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


export async function search(request: SearchRequest): Promise<SearchResult> {
  const result = await searchV1SearchPost({ body: request });
  const response = await resolveJsonResult<unknown>(result, "search");
  assertSearchResponse(response);
  return response;
}

export async function getTrends(platform: Platform): Promise<TrendData> {
  const result = await getTrendsV1TrendsGet({ query: { platform } });
  const response = await resolveJsonResult<unknown>(result, "trends");
  assertTrendResponse(response);
  return response;
}

export async function analyzeFraud(request: FraudAnalyzeRequest): Promise<FraudAnalysis> {
  const result = await analyzeCreatorFraudV1FraudAnalyzePost({ body: request });
  return resolveJsonResult<FraudAnalysis>(result, "fraud analysis");
}

export async function getFraudAnalysis(analysisId: string): Promise<FraudAnalysisStatus> {
  const result = await getFraudAnalysisV1FraudAnalysisIdGet({
    path: { analysis_id: analysisId },
  });
  return resolveJsonResult<FraudAnalysisStatus>(result, "fraud analysis retrieval");
}

export async function analyzeDeepfake(request: DeepfakeAnalyzeRequest): Promise<DeepfakeResult> {
  const result = await analyzeVideoForDeepfakeV1DeepfakeAnalyzePost({ body: request });
  return resolveJsonResult<DeepfakeResult>(result, "deepfake analysis");
}

export async function getDeepfakeAnalysis(videoId: string): Promise<DeepfakeResult> {
  const result = await getDeepfakeAnalysisV1DeepfakeVideoIdGet({
    path: { video_id: videoId },
  });
  return resolveJsonResult<DeepfakeResult>(result, "deepfake retrieval");
}

export async function getCreativePatterns(analysisId: string): Promise<Record<string, unknown>> {
  const result = await getCreativePatternsV1CreativeAnalysisIdGet({
    path: { analysis_id: analysisId },
  });
  return resolveJsonResult<Record<string, unknown>>(result, "creative patterns");
}

export async function getUsage(): Promise<UsageData> {
  const result = await getUsageV1UsageGet();
  const response = await resolveJsonResult<unknown>(result, "usage");
  assertUsageResponse(response);
  return response;
}

export type BillingSummary = BillingSummaryResponse;
export type CheckoutResult = CheckoutResponse;

export async function getBillingSummary(): Promise<BillingSummary> {
  const result = await getBillingSummaryV1BillingSummaryGet();
  const response = await resolveJsonResult<unknown>(result, "billing summary");
  assertBillingSummaryResponse(response);
  return response;
}

export async function createTopupCheckout(packCode: string): Promise<CheckoutResult> {
  const result = await createTopupCheckoutV1BillingTopupsCheckoutPost({
    body: { pack_code: packCode },
  });
  return resolveJsonResult<CheckoutResult>(result, "checkout");
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

export async function analyzeVideos(request: AnalyzeVideosRequest): Promise<AnalyzeResponse> {
  const result = await analyzeVideosV1AnalyzeVideosPost({ body: request });
  const response = await resolveJsonResult<unknown>(result, "analyze videos");
  assertAnalyzeResultsResponse(response, "analyze videos");
  return response as AnalyzeResponse;
}

export async function submitAnalyzeVideosAsync(
  request: AnalyzeVideosRequest,
  options: AnalyzeVideosAsyncOptions = {},
): Promise<AnalysisJobSubmission> {
  const result = await analyzeVideosAsyncV1AnalyzeVideosAsyncPost({
    body: request,
    headers: options.idempotencyKey ? { "Idempotency-Key": options.idempotencyKey } : undefined,
    query: {
      force_refresh: options.forceRefresh,
    },
  });
  return resolveJsonResult<AnalysisJobSubmission>(result, "submit async analysis");
}

export async function listAnalysisJobs(params: ListJobsParams = {}): Promise<AnalysisJobs> {
  const result = await listJobsV1AnalysisJobsGet({
    query: {
      status: params.statuses,
      limit: params.limit,
      offset: params.offset,
    },
  });
  return resolveJsonResult<AnalysisJobs>(result, "list analysis jobs");
}

export async function getAnalysisJobStatus(
  jobId: string,
  params: JobStatusParams = {},
): Promise<AnalysisJobStatus> {
  const result = await getJobStatusV1AnalysisJobsJobIdGet({
    path: { job_id: jobId },
    query: {
      include_results: params.includeResults,
      results_limit: params.resultsLimit,
    },
  });
  return resolveJsonResult<AnalysisJobStatus>(result, "job status");
}

export async function cancelAnalysisJob(jobId: string): Promise<AnalysisJobCancellation> {
  const result = await cancelJobV1AnalysisJobsJobIdDelete({
    path: { job_id: jobId },
  });
  return resolveJsonResult<AnalysisJobCancellation>(result, "cancel analysis job");
}

export async function analyzeCreator(request: AnalyzeCreatorRequest): Promise<CreatorAnalysisResponse> {
  const result = await analyzeCreatorV1AnalyzeCreatorPost({ body: request });
  const response = await resolveJsonResult<unknown>(result, "analyze creator");
  assertAnalyzeResultsResponse(response, "analyze creator");
  return response as CreatorAnalysisResponse;
}

export async function getAnalysis(analysisId: string): Promise<AnalysisDetails> {
  const result = await getAnalysisV1AnalysisAnalysisIdGet({
    path: { analysis_id: analysisId },
  });
  return resolveJsonResult<AnalysisDetails>(result, "analysis retrieval");
}

export async function getDemographics(analysisId: string): Promise<DemographicsData> {
  const result = await getDemographicsV1DemographicsAnalysisIdGet({
    path: { analysis_id: analysisId },
  });
  return resolveJsonResult<DemographicsData>(result, "demographics");
}

export async function getBrandAnalysis(analysisId: string): Promise<BrandAnalysis> {
  const result = await getBrandAnalysisV1BrandsAnalysisIdGet({
    path: { analysis_id: analysisId },
  });
  const response = await resolveJsonResult<unknown>(result, "brand analysis");
  assertBrandAnalysisResponse(response);
  return response;
}

export async function getCreatorProfile(
  platform: Platform,
  username: string,
): Promise<CreatorProfile> {
  const result = await getCreatorProfileV1CreatorsPlatformUsernameGet({
    path: {
      platform,
      username,
    },
  });
  return resolveJsonResult<CreatorProfile>(result, "creator profile");
}

export async function getCreatorEvolution(
  platform: Platform,
  username: string,
  period: "30d" | "90d" | "180d" | "365d" = "90d",
): Promise<CreatorEvolution> {
  const result = await getCreatorEvolutionV1CreatorsPlatformUsernameEvolutionGet({
    path: {
      platform,
      username,
    },
    query: {
      period,
    },
  });
  return resolveJsonResult<CreatorEvolution>(result, "creator evolution");
}

export async function captureStories(
  platform: Platform,
  username: string,
): Promise<StoryCaptureResult> {
  const result = await captureStoriesNowV1StoriesPlatformUsernameCapturePost({
    path: {
      platform,
      username,
    },
  });
  return resolveJsonResult<StoryCaptureResult>(result, "stories capture");
}

export async function getCapturedStories(
  platform: Platform,
  username: string,
): Promise<StoryItem[]> {
  const result = await getCapturedStoriesV1StoriesPlatformUsernameGet({
    path: {
      platform,
      username,
    },
  });
  return resolveJsonResult<StoryItem[]>(result, "stories list");
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

// ─── Library Types ────────────────────────────────────────────────────────

export type RiskLevel = "safe" | "risky" | "critical";

export interface LibraryItem {
  id: string;
  video_id: string;
  title: string | null;
  platform: string;
  risk_level: RiskLevel;
  analyzed_at: string;
  has_brands: boolean;
  has_demographics: boolean;
  has_deepfake: boolean;
  has_creative: boolean;
  has_fraud: boolean;
}

export interface LibraryListResponse {
  items: LibraryItem[];
  has_more: boolean;
  next_cursor: string | null;
}

export interface LibraryParams {
  platform?: string;
  search?: string;
  cursor?: string;
  limit?: number;
}

export async function fetchLibrary(params: LibraryParams = {}): Promise<LibraryListResponse> {
  const qs = new URLSearchParams();
  if (params.platform) qs.set("platform", params.platform);
  if (params.search) qs.set("search", params.search);
  if (params.cursor) qs.set("cursor", params.cursor);
  if (params.limit) qs.set("limit", String(params.limit));

  const query = qs.toString();
  const path = `/v1/library${query ? `?${query}` : ""}`;
  return apiKeyFetch<LibraryListResponse>(path);
}

// ─── Library Grouping Types ──────────────────────────────────────────────

export interface CreatorGroup {
  creator_id: string;
  platform: string;
  username: string;
  video_count: number;
  last_analyzed_at: string;
}

export interface CreatorGroupListResponse {
  groups: CreatorGroup[];
}

export interface SessionGroup {
  conversation_id: string;
  title: string | null;
  item_count: number;
  last_updated_at: string;
}

export interface SessionGroupListResponse {
  groups: SessionGroup[];
}

export async function fetchLibraryByCreator(): Promise<CreatorGroupListResponse> {
  return apiKeyFetch<CreatorGroupListResponse>("/v1/library/by-creator");
}

export async function fetchLibraryBySession(): Promise<SessionGroupListResponse> {
  return apiKeyFetch<SessionGroupListResponse>("/v1/library/by-session");
}

// ─── Conversation Types ───────────────────────────────────────────────────

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  role: "user" | "model" | "assistant";
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

// ─── Workspace Types ──────────────────────────────────────────────────────

export interface WorkspaceCollection {
  id: string;
  conversation_id: string;
  name: string;
  item_count: number;
  active_filters?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  items?: WorkspaceItem[];
}

export interface WorkspaceItem {
  id: string;
  collection_id: string;
  platform: string;
  video_id: string;
  title: string | null;
  creator_handle: string | null;
  views: number | null;
  engagement_rate: number | null;
  follower_count: number | null;
  description: string | null;
  thumbnail_url: string | null;
  created_at: string;
}

export interface WorkspaceToolResult {
  id: string;
  conversation_id: string;
  tool_name: string;
  input_args: Record<string, unknown>;
  result_data: Record<string, unknown>;
  workspace_item_id: string | null;
  created_at: string;
}

// ─── Batch Types ──────────────────────────────────────────────────────────

export interface BatchStatus {
  id: string;
  status: "pending" | "processing" | "completed" | "cancelled" | "failed";
  total_items: number;
  completed_items: number;
  failed_items: number;
  flagged_items?: number;
  created_at: string;
  updated_at: string;
}

export interface BatchProgressEvent {
  batch_id: string;
  status: string;
  completed: number;
  total: number;
  failed: number;
  flagged: number;
  current_item?: string;
  eta?: number;
}

export interface WorkspaceUpdateEvent {
  tool?: string;
  action?: string;
  collection_name?: string;
  collection_id?: string;
}

// ─── Video Project Types ─────────────────────────────────────────────────

export interface VideoProjectPreview {
  status: "idle" | "generating" | "verifying" | "ready" | "failed";
  image_url: string | null;
  storage_key: string | null;
  qa_score: number | null;
  qa_feedback: string | null;
  scene_score: number | null;
  style_score: number | null;
  improvement_suggestion: string | null;
  approved: boolean;
  error: string | null;
}

export interface VideoProjectScene {
  id: string;
  index: number;
  title: string;
  summary: string;
  prompt: string;
  duration_seconds: number;
  transition: "fade" | "cut" | "dissolve" | "wipe";
  caption: string;
  preview: VideoProjectPreview;
}

export interface VideoProjectReference {
  id: string;
  analysis_id: string | null;
  source_video_id: string | null;
  platform: string | null;
  title: string;
  thumbnail_url: string | null;
  creator_handle: string | null;
}

export interface VideoProjectSummary {
  id: string;
  conversation_id: string;
  title: string;
  status: string;
  revision: number;
  updated_at: string;
  created_at: string;
}

export interface VideoProjectSnapshot extends VideoProjectSummary {
  source_analysis_ids: string[];
  anchor_scene_id: string | null;
  references: VideoProjectReference[];
  style_brief_summary: string;
  aspect_ratio: "9:16" | "16:9" | "1:1";
  resolution: "480p" | "720p";
  anchor_scene_index: number | null;
  anchor_preview_image_url: string | null;
  anchor_preview_storage_key: string | null;
  render_job_id: string | null;
  render_job_status: string | null;
  render_is_stale: boolean;
  render_project_revision: number | null;
  final_video_url: string | null;
  final_video_url_expires_at: string | null;
  last_error: string | null;
  scenes: VideoProjectScene[];
}

export interface CreateVideoProjectRequest {
  conversation_id: string;
  title?: string;
  references?: Array<{
    analysis_id?: string | null;
    source_video_id?: string | null;
    platform?: string | null;
    title: string;
    thumbnail_url?: string | null;
    creator_handle?: string | null;
  }>;
  source_analysis_ids?: string[];
}

export interface UpdateVideoProjectRequest {
  expected_revision: number;
  title?: string | null;
  style_brief_summary?: string | null;
  anchor_scene_id?: string | null;
}

export interface UpdateVideoProjectSceneRequest {
  expected_revision: number;
  title?: string | null;
  summary?: string | null;
  prompt?: string | null;
  duration_seconds?: number | null;
  transition?: "fade" | "cut" | "dissolve" | "wipe" | null;
  caption?: string | null;
  preview_approved?: boolean | null;
}

export interface ReorderVideoProjectScenesRequest {
  expected_revision: number;
  scene_ids: string[];
}

export interface VideoProjectRevisionRequest {
  expected_revision: number;
  model?: "gemini" | "grok" | "imagen";
}

// ─── Conversation API ─────────────────────────────────────────────────────

export async function createConversation(): Promise<Conversation> {
  return apiKeyFetch<Conversation>("/v1/conversations", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function listConversations(): Promise<Conversation[]> {
  const res = await apiKeyFetch<{ data: Conversation[] }>("/v1/conversations");
  return res.data ?? [];
}

export async function getConversationMessages(id: string): Promise<ConversationMessage[]> {
  const res = await apiKeyFetch<{ data: ConversationMessage[] }>(
    `/v1/conversations/${id}/messages`
  );
  return res.data ?? [];
}

export async function renameConversation(id: string, title: string): Promise<void> {
  await apiKeyFetch<unknown>(`/v1/conversations/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

export async function deleteConversation(id: string): Promise<void> {
  await apiKeyFetch<unknown>(`/v1/conversations/${id}`, {
    method: "DELETE",
  });
}

// ─── Workspace API ────────────────────────────────────────────────────────

export async function createCollection(data: {
  name: string;
  conversation_id?: string;
}): Promise<{ id: string; name: string; conversation_id: string; created_at: string }> {
  return apiKeyFetch<{ id: string; name: string; conversation_id: string; created_at: string }>(
    "/v1/workspace/collections",
    { method: "POST", body: JSON.stringify(data) },
  );
}

export async function getWorkspaceCollections(conversationId: string): Promise<WorkspaceCollection[]> {
  const res = await apiKeyFetch<{ data: WorkspaceCollection[] }>(
    `/v1/workspace/collections?conversation_id=${conversationId}`
  );
  return res.data ?? [];
}

export async function getWorkspaceToolResults(conversationId: string): Promise<WorkspaceToolResult[]> {
  const res = await apiKeyFetch<{ data: WorkspaceToolResult[] }>(
    `/v1/workspace/tool-results?conversation_id=${conversationId}`
  );
  return res.data ?? [];
}

export async function listVideoProjects(conversationId: string): Promise<VideoProjectSummary[]> {
  return apiKeyFetch<VideoProjectSummary[]>(
    `/v1/video-projects?conversation_id=${encodeURIComponent(conversationId)}`,
  );
}

export async function getVideoProject(projectId: string): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}`);
}

export async function createVideoProject(body: CreateVideoProjectRequest): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>("/v1/video-projects", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateVideoProject(
  projectId: string,
  body: UpdateVideoProjectRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function updateVideoProjectScene(
  projectId: string,
  sceneId: string,
  body: UpdateVideoProjectSceneRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/scenes/${sceneId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function addVideoProjectReferences(
  projectId: string,
  body: { expected_revision: number; references: NonNullable<CreateVideoProjectRequest["references"]> },
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/references`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function previewVideoProjectAnchor(
  projectId: string,
  body: VideoProjectRevisionRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/preview-anchor`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function previewVideoProjectScenes(
  projectId: string,
  body: VideoProjectRevisionRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/preview-scenes`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function renderVideoProject(
  projectId: string,
  body: VideoProjectRevisionRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/render`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function recomposeVideoProject(
  projectId: string,
  body: VideoProjectRevisionRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/recompose`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function reorderVideoProjectScenes(
  projectId: string,
  body: ReorderVideoProjectScenesRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/scenes/reorder`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function regenerateVideoProjectScene(
  projectId: string,
  sceneId: string,
  body: VideoProjectRevisionRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/scenes/${sceneId}/regenerate`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function verifyVideoProjectScene(
  projectId: string,
  sceneId: string,
  body: VideoProjectRevisionRequest,
): Promise<VideoProjectSnapshot> {
  return apiKeyFetch<VideoProjectSnapshot>(`/v1/video-projects/${projectId}/scenes/${sceneId}/verify`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateCollectionFilters(
  collectionId: string,
  conversationId: string,
  filters: Record<string, unknown>,
): Promise<void> {
  await apiKeyFetch<unknown>(
    `/v1/workspace/collections/${collectionId}/filters?conversation_id=${conversationId}`,
    {
      method: "PATCH",
      body: JSON.stringify({ filters }),
    },
  );
}

export interface CollectionItemScore {
  id: string;
  source_id: string;
  platform: string;
  risk_score: number | null;
  analysis_results: Record<string, unknown> | null;
}

export async function getCollectionItemScores(
  collectionId: string,
  conversationId: string,
): Promise<CollectionItemScore[]> {
  const res = await apiKeyFetch<{ data: CollectionItemScore[] }>(
    `/v1/workspace/collections/${collectionId}/items?conversation_id=${conversationId}`,
  );
  return res.data ?? [];
}

// ─── Batch API ────────────────────────────────────────────────────────────

export async function getBatchStatus(batchId: string): Promise<BatchStatus> {
  return apiKeyFetch<BatchStatus>(`/v1/batch/${batchId}`);
}

export async function cancelBatch(batchId: string): Promise<void> {
  await apiKeyFetch<unknown>(`/v1/batch/${batchId}/cancel`, {
    method: "POST",
  });
}

export async function retryFailedBatch(batchId: string): Promise<void> {
  await apiKeyFetch<unknown>(`/v1/batch/${batchId}/retry-failed`, {
    method: "POST",
  });
}

/** Cancel an active agent run on the backend (fire-and-forget). */
export async function cancelAgentRun(runId: string): Promise<void> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  await fetch(`${BASE}/v1/agent/runs/${runId}/cancel`, {
    method: "POST",
    headers,
  }).catch(() => {});
}

// --- Generation ---

export interface GenerationCadreStatus {
  index: number;
  status: string;
  error?: string | null;
  thumbnail_url?: string | null;
}

export interface GenerationJobStatus {
  job_id: string;
  status: string;
  current_cadre: number;
  total_cadres: number;
  video_project_id?: string | null;
  video_url: string | null;
  video_url_expires_at: string | null;
  cost_cents: number;
  cadre_statuses: GenerationCadreStatus[];
  error: string | null;
}

export async function getGenerationJobStatus(jobId: string, signal?: AbortSignal): Promise<GenerationJobStatus> {
  return apiKeyFetch<GenerationJobStatus>(
    `/v1/generation/jobs/${encodeURIComponent(jobId)}`,
    { signal },
  );
}

export async function cancelGenerationJob(jobId: string): Promise<{ job_id: string; status: string; cancellation_requested: boolean }> {
  return apiKeyFetch<{ job_id: string; status: string; cancellation_requested: boolean }>(
    `/v1/generation/jobs/${encodeURIComponent(jobId)}`,
    { method: "DELETE" },
  );
}

export interface GenerationSubmitResponse {
  job_id: string;
  status: string;
  cadre_count: number;
  estimated_cost_cents: number;
}

export async function submitGenerationJob(
  compositionSpec: Record<string, unknown>,
): Promise<GenerationSubmitResponse> {
  return apiKeyFetch<GenerationSubmitResponse>("/v1/generation/jobs", {
    method: "POST",
    body: JSON.stringify({ composition_spec: compositionSpec }),
  });
}

export async function* streamBatchProgress(
  batchId: string,
  signal: AbortSignal,
): AsyncGenerator<BatchProgressEvent> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}/v1/batch/${batchId}/progress`, {
    headers,
    signal,
  });

  if (!res.ok) {
    await handleErrorStatus(res);
    throw new ApiError(res.status, `http_${res.status}`, res.statusText);
  }

  const reader = res.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    let eventType = "message";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        eventType = line.slice(7).trim();
        continue;
      }
      if (line.startsWith("data: ")) {
        try {
          const parsed = JSON.parse(line.slice(6));
          yield parsed as BatchProgressEvent;
          if (eventType === "done") return;
        } catch {
          // skip malformed events
        }
        eventType = "message"; // reset after data line
      }
    }
  }
}

/** SSE stream for agent chat */
export async function* streamChat(
  message: string,
  history: Array<{ role: string; content: string }>,
  signal?: AbortSignal,
  conversationId?: string,
): AsyncGenerator<{ type: StreamEventType; data: string }> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const normalizedHistory: ChatRequest["history"] = history.map((item) => ({
    role: item.role === "assistant" ? "model" : "user",
    parts: [{ text: item.content }],
  }));

  const body: Omit<ChatRequest, 'conversation_id'> & { conversation_id?: string } = {
    message,
    // When conversation_id is set, server uses stored history — sending both is redundant
    history: conversationId ? undefined : (normalizedHistory.length > 0 ? normalizedHistory : undefined),
    conversation_id: conversationId,
  };

  const res = await fetch(`${BASE}${AGENT_CHAT_ENDPOINT}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    await handleErrorStatus(res);

    const body = await res.json().catch(() => null);
    const parsed = extractError(body, res.status, res.statusText);
    throw new ApiError(res.status, parsed.code, parsed.message, parsed.details);
  }

  const reader = res.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = "";
  const EVENT_GAP_TIMEOUT_MS = 60_000; // 4× backend ping interval (15s)

  while (true) {
    const readPromise = reader.read();
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error("SSE_TIMEOUT")), EVENT_GAP_TIMEOUT_MS),
    );

    let result: ReadableStreamReadResult<Uint8Array>;
    try {
      result = await Promise.race([readPromise, timeoutPromise]);
    } catch (err) {
      if (err instanceof Error && err.message === "SSE_TIMEOUT") {
        reader.cancel().catch(() => {});
        throw new ApiError(0, "timeout", "Connection timed out. Please try again.");
      }
      throw err;
    }

    const { done, value } = result;
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    let eventType: StreamEventType | string = "message";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        eventType = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        if (!STREAM_EVENT_TYPES.has(eventType as StreamEventType)) {
          if (import.meta.env.DEV && AGENT_V2_ENABLED) {
            console.warn(`[v2 SSE] Unknown event type: ${eventType}`, line.slice(6));
          }
          eventType = "message";
          continue;
        }

        const type = eventType as StreamEventType;
        const payload = normalizeStreamPayload(type, line.slice(6));

        yield { type, data: payload };
        if (type === "done") {
          reader.cancel().catch(() => {});
          return;
        }
        eventType = "message";
      }
    }
  }

  // Flush remaining buffer on EOF — process any complete events left over
  if (buffer.trim()) {
    const lines = buffer.split("\n");
    let eventType: StreamEventType | string = "message";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        eventType = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        if (!STREAM_EVENT_TYPES.has(eventType as StreamEventType)) {
          if (import.meta.env.DEV && AGENT_V2_ENABLED) {
            console.warn(`[v2 SSE] Unknown event type: ${eventType}`, line.slice(6));
          }
          eventType = "message";
          continue;
        }
        const type = eventType as StreamEventType;
        yield { type, data: normalizeStreamPayload(type, line.slice(6)) };
        eventType = "message";
      }
    }
  }
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

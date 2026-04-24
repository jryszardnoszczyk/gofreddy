import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { useAuth } from "@/components/AuthProvider";
import { Settings, User, LogOut, RefreshCw, CreditCard, Key, Copy, Trash2, Plus, Coins, ArrowUpRight, Cpu, ShieldCheck, Sparkles } from "lucide-react";
import { ROUTES } from "@/lib/routes";
import { Button } from "@/components/shared/Button";
import { Card, CardHeader, CardTitle } from "@/components/shared/Card";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/shared/Badge";
import { AlertBanner } from "@/components/shared/AlertBanner";
import { formatTierLabel } from "@/lib/tier";
import {
  createApiKey,
  listApiKeys,
  revokeApiKey,
  getBillingSummary,
  createTopupCheckout,
  getPreferences,
  updatePreferences,
  ApiError,
  type ApiKeyInfo,
  type BillingSummary,
  type UserPreferences,
} from "@/lib/api";

const PACK_OPTIONS = [
  { code: "starter_10", label: "10 credits", price: "$9.99" },
  { code: "growth_50", label: "50 credits", price: "$39.99" },
  { code: "scale_200", label: "200 credits", price: "$149.99" },
] as const;

function formatModelLabel(model?: UserPreferences["agent_model"] | null): string {
  if (model === "gemini-3.1-pro-preview") return "Gemini Pro";
  return "Gemini Flash";
}

export function SettingsPage() {
  useDocumentTitle("Settings");
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    user,
    signOut,
    profile,
    profileLoading,
    profileError,
    refreshProfile,
    tier,
    subscriptionStatus,
  } = useAuth();

  const profileEmail = profile?.email ?? user?.email ?? "—";
  const statusLabel = subscriptionStatus?.replaceAll("_", " ") ?? "not available";
  const userMonogram = profileEmail !== "—" ? profileEmail.slice(0, 2).toUpperCase() : "CL";

  // API Keys state
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>([]);
  const [keysLoading, setKeysLoading] = useState(false);
  const [keysError, setKeysError] = useState<string | null>(null);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  // Credits state
  const [creditBalance, setCreditBalance] = useState<BillingSummary | null>(null);
  const [creditsLoading, setCreditsLoading] = useState(false);
  const [creditsError, setCreditsError] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [checkoutStatus, setCheckoutStatus] = useState<"success" | "canceled" | null>(null);

  // AI Model state
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [modelLoading, setModelLoading] = useState(false);
  const [modelSaving, setModelSaving] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);
  const activeModelLabel = formatModelLabel(preferences?.agent_model);
  const creditAvailable = creditBalance?.available ?? null;

  const loadKeys = useCallback(async () => {
    setKeysLoading(true);
    setKeysError(null);
    try {
      const keys = await listApiKeys();
      setApiKeys(keys);
    } catch (err) {
      setKeysError(err instanceof ApiError ? err.message : "Failed to load API keys");
    } finally {
      setKeysLoading(false);
    }
  }, []);

  const loadCredits = useCallback(async () => {
    setCreditsLoading(true);
    setCreditsError(null);
    try {
      const balance = await getBillingSummary();
      setCreditBalance(balance);
    } catch (err) {
      // 404 = billing not enabled on this backend; the Credits card is already
      // gated on `creditBalance?.billing_model_version`, so leaving creditBalance
      // null is the correct "not enabled" state, not a user-facing error.
      if (err instanceof ApiError && err.status === 404) {
        return;
      }
      setCreditsError(err instanceof ApiError ? err.message : "Failed to load credit balance");
    } finally {
      setCreditsLoading(false);
    }
  }, []);

  const loadPreferences = useCallback(async () => {
    setModelLoading(true);
    setModelError(null);
    try {
      const prefs = await getPreferences();
      setPreferences(prefs);
    } catch (err) {
      setModelError(err instanceof ApiError ? err.message : "Failed to load preferences");
    } finally {
      setModelLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadKeys();
    void loadCredits();
    void loadPreferences();
  }, [loadKeys, loadCredits, loadPreferences]);

  // Handle checkout return query params
  useEffect(() => {
    const checkout = searchParams.get("checkout");
    if (checkout === "success") {
      setCheckoutStatus("success");
      void loadCredits();
      // Clean up query params
      setSearchParams({}, { replace: true });
    } else if (checkout === "canceled") {
      setCheckoutStatus("canceled");
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, loadCredits]);

  async function handleCreateKey() {
    setCreating(true);
    setKeysError(null);
    setCreatedKey(null);
    try {
      const result = await createApiKey(newKeyName.trim() || undefined);
      setCreatedKey(result.key);
      setNewKeyName("");
      await loadKeys();
    } catch (err) {
      setKeysError(err instanceof ApiError ? err.message : "Failed to create API key");
    } finally {
      setCreating(false);
    }
  }

  async function handleRevokeKey(keyId: string) {
    setRevokingId(keyId);
    setKeysError(null);
    try {
      await revokeApiKey(keyId);
      await loadKeys();
    } catch (err) {
      setKeysError(err instanceof ApiError ? err.message : "Failed to revoke API key");
    } finally {
      setRevokingId(null);
    }
  }

  async function handleBuyCredits(packCode: string) {
    setCheckoutLoading(packCode);
    setCreditsError(null);
    setCheckoutStatus(null);
    try {
      const result = await createTopupCheckout(packCode);
      const url = new URL(result.checkout_url);
      if (!url.hostname.endsWith('.stripe.com')) {
        setCreditsError('Invalid checkout URL');
        setCheckoutLoading(null);
        return;
      }
      window.location.href = result.checkout_url;
    } catch (err) {
      setCreditsError(err instanceof ApiError ? err.message : "Failed to start checkout");
      setCheckoutLoading(null);
    }
  }

  async function handleModelChange(model: UserPreferences["agent_model"]) {
    setModelSaving(true);
    setModelError(null);
    try {
      const updated = await updatePreferences({ agent_model: model });
      setPreferences(updated);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setModelError("Gemini Pro requires a Pro subscription");
      } else {
        setModelError(err instanceof ApiError ? err.message : "Failed to update model");
      }
    } finally {
      setModelSaving(false);
    }
  }

  return (
    <div className="app-page-shell mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        icon={<Settings className="h-4 w-4" />}
        title="Settings"
        description="Your account, usage, billing, and app preferences"
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_340px]">
        <div className="space-y-6">
          <Card className="overflow-hidden">
            <div className="grid gap-5 lg:grid-cols-[minmax(0,1.05fr)_minmax(260px,0.95fr)]">
              <div>
                <CardHeader>
                  <CardTitle>
                    <User className="mr-2 inline h-4 w-4 text-brand-400" />
                    Account
                  </CardTitle>
                </CardHeader>

                <div className="space-y-4">
                  <div className="divide-y divide-border-subtle text-sm text-zinc-500">
                    <div className="flex justify-between py-2.5 first:pt-0">
                      <span>Email</span>
                      <span className="text-zinc-300">{profileEmail}</span>
                    </div>
                    <div className="flex justify-between py-2.5">
                      <span>Provider</span>
                      <span className="text-zinc-300">{user?.app_metadata?.provider ?? "—"}</span>
                    </div>
                    <div className="flex justify-between py-2.5">
                      <span>User ID</span>
                      <span className="font-mono text-xs text-zinc-400">{user?.id ?? "—"}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button variant="ghost" size="sm" onClick={signOut}>
                      <LogOut className="mr-1.5 h-4 w-4" />
                      Sign out
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => void refreshProfile()} loading={profileLoading}>
                      <RefreshCw className="mr-1.5 h-4 w-4" />
                      Refresh profile
                    </Button>
                  </div>
                  {profileError && <p className="text-xs text-warning">{profileError}</p>}
                </div>
              </div>

              <div className="app-panel-soft rounded-[18px] p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="app-mark-shell flex h-14 w-14 items-center justify-center rounded-[16px] text-sm font-semibold tracking-[0.24em] text-zinc-100">
                      {userMonogram}
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">Workspace</p>
                      <p className="mt-1 text-base font-semibold text-zinc-100">Freddy cockpit</p>
                      <p className="text-xs text-zinc-400">{tier === "pro" ? "Premium workspace access" : "Starter workspace access"}</p>
                    </div>
                  </div>
                  <Badge variant={tier === "pro" ? "brand" : "neutral"}>{formatTierLabel(tier)}</Badge>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[14px] bg-surface-raised/75 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">Subscription</p>
                    <p className="mt-2 text-sm font-medium capitalize text-zinc-100">{statusLabel}</p>
                    <p className="mt-1 text-xs text-zinc-400">Current workspace status</p>
                  </div>
                  <div className="rounded-[14px] bg-surface-raised/75 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">Model</p>
                    <p className="mt-2 text-sm font-medium text-zinc-100">{activeModelLabel}</p>
                    <p className="mt-1 text-xs text-zinc-400">Default assistant engine</p>
                  </div>
                  <div className="rounded-[14px] bg-surface-raised/75 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">Credits</p>
                    <p className="mt-2 text-sm font-medium text-zinc-100">
                      {creditAvailable != null ? creditAvailable.toLocaleString() : "Not enabled"}
                    </p>
                    <p className="mt-1 text-xs text-zinc-400">Available generation balance</p>
                  </div>
                  <div className="rounded-[14px] bg-surface-raised/75 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">Protection</p>
                    <p className="mt-2 flex items-center gap-2 text-sm font-medium text-zinc-100">
                      <ShieldCheck className="h-4 w-4 text-zinc-300" />
                      Session secured
                    </p>
                    <p className="mt-1 text-xs text-zinc-400">API keys and account controls</p>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>
                <Cpu className="mr-2 inline h-4 w-4 text-brand-400" />
                AI Model
              </CardTitle>
            </CardHeader>

            <div className="space-y-3">
              {modelError && <AlertBanner message={modelError} className="max-w-full" />}

              {modelLoading ? (
                <p className="text-xs text-zinc-500">Loading model preference...</p>
              ) : (
                <div className="space-y-2">
                  <button
                    type="button"
                    onClick={() => void handleModelChange("gemini-3-flash-preview")}
                    disabled={modelSaving}
                    className={`w-full rounded-[14px] border p-4 text-left transition-all ${
                      preferences?.agent_model === "gemini-3-flash-preview" || !preferences
                        ? "border-white/10 bg-surface-raised"
                        : "border-border-subtle hover:border-white/10 hover:bg-white/4"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-zinc-200">Gemini Flash</p>
                        <p className="text-xs text-zinc-500">Fast responses, optimized for speed</p>
                      </div>
                      {(preferences?.agent_model === "gemini-3-flash-preview" || !preferences) && (
                        <Badge variant="brand">Active</Badge>
                      )}
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => void handleModelChange("gemini-3.1-pro-preview")}
                    disabled={modelSaving || tier !== "pro"}
                    className={`w-full rounded-[14px] border p-4 text-left transition-all ${
                      preferences?.agent_model === "gemini-3.1-pro-preview"
                        ? "border-white/10 bg-surface-raised"
                        : tier !== "pro"
                          ? "cursor-not-allowed border-border-subtle opacity-50"
                          : "border-border-subtle hover:border-white/10 hover:bg-white/4"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-zinc-200">
                          Gemini Pro
                          {tier !== "pro" && (
                            <Badge variant="neutral" className="ml-2">Pro tier required</Badge>
                          )}
                        </p>
                        <p className="text-xs text-zinc-500">Most capable model, deeper reasoning</p>
                      </div>
                      {preferences?.agent_model === "gemini-3.1-pro-preview" && (
                        <Badge variant="brand">Active</Badge>
                      )}
                    </div>
                  </button>

                  {tier !== "pro" && (
                    <Link
                      to={ROUTES.pricing}
                      className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300"
                    >
                      Upgrade to unlock Gemini Pro
                      <ArrowUpRight className="h-3 w-3" />
                    </Link>
                  )}
                </div>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>
                <Key className="mr-2 inline h-4 w-4 text-brand-400" />
                API Keys
              </CardTitle>
            </CardHeader>

            <div className="space-y-4">
              {keysError && <AlertBanner message={keysError} className="max-w-full" />}

              {createdKey && (
                <div className="rounded-[16px] border border-safe/30 bg-safe/5 p-4">
                  <p className="mb-1 text-xs font-medium text-safe">New key created. Copy it now because it will not be shown again.</p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 break-all rounded-[10px] bg-black/20 px-2 py-1 font-mono text-xs text-zinc-200">
                      {createdKey}
                    </code>
                    <button
                      type="button"
                      onClick={() => void navigator.clipboard.writeText(createdKey)}
                      className="shrink-0 rounded-[10px] p-2 text-zinc-400 hover:bg-white/6 hover:text-zinc-200"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}

              <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
                <input
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="Key name (optional)"
                  className="app-panel-soft h-11 rounded-[14px] px-4 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-white/12 focus:outline-none focus:ring-2 focus:ring-white/8"
                />
                <Button size="sm" onClick={handleCreateKey} loading={creating} className="h-11 rounded-[14px] px-4">
                  <Plus className="mr-1 h-3.5 w-3.5" />
                  Create Key
                </Button>
              </div>

              {keysLoading ? (
                <p className="text-xs text-zinc-500">Loading keys...</p>
              ) : apiKeys.length === 0 ? (
                <p className="text-xs text-zinc-500">No API keys created yet.</p>
              ) : (
                <div className="divide-y divide-border-subtle text-sm">
                  {apiKeys.map((k) => (
                    <div key={k.id} className="flex items-center justify-between gap-3 py-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <code className="text-xs text-zinc-200">{k.key_prefix}...</code>
                          {k.name && <span className="text-xs text-zinc-500">{k.name}</span>}
                          <Badge variant={k.is_active ? "safe" : "neutral"}>
                            {k.is_active ? "Active" : "Revoked"}
                          </Badge>
                        </div>
                        <div className="mt-0.5 text-[11px] text-zinc-500">
                          Created {new Date(k.created_at).toLocaleDateString()}
                          {k.last_used_at && ` | Last used ${new Date(k.last_used_at).toLocaleDateString()}`}
                        </div>
                      </div>
                      {k.is_active && (
                        <button
                          type="button"
                          onClick={() => void handleRevokeKey(k.id)}
                          disabled={revokingId === k.id}
                          className="shrink-0 rounded-[10px] p-2 text-zinc-500 hover:bg-danger/10 hover:text-danger disabled:opacity-50"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6 xl:sticky xl:top-8 xl:self-start">
          <Card className="overflow-hidden">
            <CardHeader>
              <CardTitle>
                <CreditCard className="mr-2 inline h-4 w-4 text-brand-400" />
                Subscription
              </CardTitle>
            </CardHeader>

            <div className="space-y-4 text-sm text-zinc-500">
              <div className="rounded-[16px] bg-surface-raised/75 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">Current tier</p>
                    <p className="mt-1 text-lg font-semibold text-zinc-100">{formatTierLabel(tier)}</p>
                  </div>
                  <Badge variant={tier === "pro" ? "brand" : "neutral"} className="capitalize">{statusLabel}</Badge>
                </div>
                <p className="mt-3 text-xs text-zinc-400">
                  {tier === "pro"
                    ? "You have full access to premium models, longer history, and studio workflows."
                    : "Upgrade to unlock the premium model, full analysis history, and a richer studio workflow."}
                </p>
                {tier === "free" && (
                  <Link
                    to={ROUTES.pricing}
                    className="mt-4 inline-flex items-center gap-1.5 rounded-[12px] border border-white/10 bg-zinc-100 px-4 py-2.5 text-xs font-medium text-zinc-950 transition-all hover:bg-white"
                  >
                    Upgrade to Pro
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <div className="rounded-[16px] bg-surface-raised/75 p-4">
                  <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">Default model</p>
                  <p className="mt-2 text-sm font-medium text-zinc-100">{activeModelLabel}</p>
                  <p className="mt-1 text-xs text-zinc-400">Saved across your workspace</p>
                </div>
                <div className="rounded-[16px] bg-surface-raised/75 p-4">
                  <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">App version</p>
                  <p className="mt-2 text-sm font-medium text-zinc-100">1.0.0</p>
                  <p className="mt-1 text-xs text-zinc-400">Current dashboard release</p>
                </div>
              </div>
            </div>
          </Card>

          {creditBalance?.billing_model_version && (
            <Card>
              <CardHeader>
                <CardTitle>
                  <Coins className="mr-2 inline h-4 w-4 text-brand-400" />
                  Credits
                </CardTitle>
              </CardHeader>

              <div className="space-y-4">
                {checkoutStatus === "success" && (
                  <div className="rounded-[14px] border border-safe/30 bg-safe/5 p-3">
                    <p className="text-xs font-medium text-safe">
                      Payment received. Your balance will update shortly.
                    </p>
                    <button
                      type="button"
                      onClick={() => { setCheckoutStatus(null); void loadCredits(); }}
                      className="mt-1 text-xs text-safe underline hover:no-underline"
                    >
                      Refresh balance
                    </button>
                  </div>
                )}

                {checkoutStatus === "canceled" && (
                  <div className="rounded-[14px] border border-warning/30 bg-warning/5 p-3">
                    <p className="text-xs font-medium text-warning">
                      Checkout was canceled. No charges were made.
                    </p>
                  </div>
                )}

                {creditsError && <AlertBanner message={creditsError} className="max-w-full" />}

                {creditsLoading ? (
                  <p className="text-xs text-zinc-500">Loading credit balance...</p>
                ) : creditBalance ? (
                  <>
                    <div className="rounded-[16px] bg-surface-raised/75 p-4">
                      <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">Available now</p>
                      <p className="mt-2 text-2xl font-semibold text-zinc-100">{creditBalance.available.toLocaleString()}</p>
                      <p className="mt-1 text-xs text-zinc-400">Spendable generation credits</p>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Promo</span>
                        <span className="text-zinc-300">{creditBalance.promo_remaining.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Included</span>
                        <span className="text-zinc-300">{creditBalance.included_remaining.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Top-up</span>
                        <span className="text-zinc-300">{creditBalance.topup_remaining.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Reserved</span>
                        <span className="text-zinc-300">{creditBalance.reserved_total.toLocaleString()}</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="text-xs text-zinc-500">No credit balance available.</p>
                )}

                <div className="space-y-2 pt-1">
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-zinc-500">Buy credits</p>
                  <div className="grid gap-2">
                    {PACK_OPTIONS.map((pack) => (
                      <button
                        key={pack.code}
                        type="button"
                        onClick={() => void handleBuyCredits(pack.code)}
                        disabled={checkoutLoading !== null}
                        className="app-panel-soft flex items-center justify-between rounded-[14px] px-4 py-3 text-left transition-colors hover:bg-white/6 disabled:opacity-50"
                      >
                        <div>
                          <p className="text-sm font-medium text-zinc-100">{pack.label}</p>
                          <p className="text-xs text-zinc-500">One-time top-up pack</p>
                        </div>
                        <span className="text-sm font-medium text-zinc-300">
                          {checkoutLoading === pack.code ? "Loading..." : pack.price}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>
                <Sparkles className="mr-2 inline h-4 w-4 text-brand-400" />
                About
              </CardTitle>
            </CardHeader>
            <div className="space-y-3 text-sm text-zinc-500">
              <div className="rounded-[16px] bg-surface-raised/75 p-4">
                <p className="text-sm font-medium text-zinc-100">Conversation cockpit</p>
                <p className="mt-1 text-xs text-zinc-400">
                  Manage your access, default model, and generation balance from one place.
                </p>
              </div>
              <div className="rounded-[16px] bg-surface-raised/75 p-4">
                <p className="flex items-center gap-2 text-sm font-medium text-zinc-100">
                  <ShieldCheck className="h-4 w-4 text-zinc-300" />
                  Workspace controls
                </p>
                <p className="mt-1 text-xs text-zinc-400">
                  API keys, subscription state, and billing details stay available here without leaving the dashboard.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

import { ROUTES } from "./routes";

const PRO_TIERS = new Set(["pro", "enterprise"]);

export function normalizeTier(tier: string | null | undefined): string | null {
  if (!tier) return null;
  const normalized = tier.trim().toLowerCase();
  return normalized.length > 0 ? normalized : null;
}

export function hasProAccess(tier: string | null | undefined): boolean {
  const normalized = normalizeTier(tier);
  return normalized !== null && PRO_TIERS.has(normalized);
}

export function getTierDefaultRoute(_tier: string | null | undefined): string {
  return ROUTES.dashboard;
}

export function formatTierLabel(tier: string | null | undefined): string {
  const normalized = normalizeTier(tier);
  if (!normalized) return "Unknown";
  if (normalized === "free") return "Free";
  if (normalized === "pro") return "Pro";
  if (normalized === "enterprise") return "Enterprise";
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

import { Link } from "react-router-dom";
import { Lock, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/cn";
import { ROUTES } from "@/lib/routes";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";

export function TierRequiredBanner({
  message,
  requiredTier,
  currentTier,
  feature,
  className,
}: {
  message?: string;
  requiredTier?: string | null;
  currentTier?: string | null;
  feature?: string | null;
  className?: string;
}) {
  const buttonBase =
    "inline-flex h-8 items-center justify-center gap-1.5 rounded-lg px-3 text-xs font-medium transition-all duration-150";

  return (
    <Card className={className}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-zinc-100">
            <Lock className="h-4 w-4 text-warning" />
            <span className="text-sm font-semibold">Upgrade required</span>
            {requiredTier && <Badge variant="warning">{requiredTier}</Badge>}
          </div>
          <p className="text-sm text-zinc-500">
            {message ?? "Your current tier does not include this capability."}
          </p>
          <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-600">
            {feature && <span>Feature: {feature.replaceAll("_", " ")}</span>}
            {currentTier && <span>Current tier: {currentTier}</span>}
          </div>
        </div>
        <div className="flex gap-2">
          <Link
            to={ROUTES.dashboardSettings}
            className={cn(
              buttonBase,
              "text-zinc-400 hover:bg-surface-overlay hover:text-zinc-200",
            )}
          >
            View Settings
          </Link>
          <Link
            to={ROUTES.pricing}
            className={cn(
              buttonBase,
              "bg-brand-500 text-white shadow-sm shadow-brand-500/25 hover:bg-brand-400",
            )}
          >
            Upgrade
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </Card>
  );
}

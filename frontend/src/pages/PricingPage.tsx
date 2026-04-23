import { Link } from "react-router-dom";
import { ArrowLeft, Check, Sparkles } from "lucide-react";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { useAuth } from "@/components/AuthProvider";
import { ROUTES } from "@/lib/routes";
import { Card, CardHeader, CardTitle } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";
import { formatTierLabel } from "@/lib/tier";

const PRO_BENEFITS = [
  "Gemini Pro — most capable model, deeper reasoning",
  "Full analysis history across your workspace",
  "Richer studio workflow for sessions and playbooks",
] as const;

export function PricingPage() {
  useDocumentTitle("Upgrade to Pro");
  const { tier } = useAuth();
  const isPro = tier === "pro";

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle className="text-base">
            <Sparkles className="mr-2 inline h-4 w-4 text-brand-400" />
            {isPro ? "You're on Pro" : "Upgrade to Pro"}
          </CardTitle>
          <Badge variant={isPro ? "brand" : "neutral"} className="capitalize">
            {formatTierLabel(tier)}
          </Badge>
        </CardHeader>

        <div className="space-y-5 text-sm text-zinc-400">
          <p>
            {isPro
              ? "You have full access to premium models, longer history, and studio workflows."
              : "Pro unlocks the premium model, full analysis history, and a richer studio workflow."}
          </p>

          <ul className="space-y-2">
            {PRO_BENEFITS.map((benefit) => (
              <li key={benefit} className="flex items-start gap-2 text-zinc-300">
                <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-safe" />
                <span>{benefit}</span>
              </li>
            ))}
          </ul>

          {!isPro && (
            <p className="rounded-[12px] bg-surface-raised/75 p-4 text-xs text-zinc-400">
              Self-serve upgrades aren't available yet. Reach out to the Freddy team
              to enable Pro on your workspace.
            </p>
          )}

          <Link
            to={ROUTES.dashboardSettings}
            className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300"
          >
            <ArrowLeft className="h-3 w-3" />
            Back to Settings
          </Link>
        </div>
      </Card>
    </div>
  );
}

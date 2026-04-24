import { Link } from "react-router-dom";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { useAuth } from "@/components/AuthProvider";
import { ROUTES } from "@/lib/routes";
import { Card, CardHeader, CardTitle } from "@/components/shared/Card";

export function PricingPage() {
  useDocumentTitle("Pricing");
  const { session } = useAuth();
  const backHref = session ? ROUTES.dashboardSettings : ROUTES.login;
  const backLabel = session ? "Back to Settings" : "Sign in";

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-center text-lg">Pricing</CardTitle>
        </CardHeader>
        <div className="space-y-3 px-6 pb-6 text-sm text-zinc-400">
          <p>Plan details are coming soon. Contact support to upgrade your tier.</p>
          <Link
            to={backHref}
            className="inline-flex h-9 w-full items-center justify-center rounded-[12px] text-sm font-medium text-zinc-400 transition-all duration-150 hover:bg-white/5 hover:text-zinc-100"
          >
            {backLabel}
          </Link>
        </div>
      </Card>
    </div>
  );
}

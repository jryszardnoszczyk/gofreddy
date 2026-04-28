import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/components/AuthProvider";
import { ROUTES } from "@/lib/routes";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/shared/Button";

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const { session, loading, profileLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [timedOut, setTimedOut] = useState(false);

  // Step 1: Check URL for OAuth error params (query params only)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const errorParam = params.get("error");
    if (errorParam) {
      const KNOWN_ERRORS: Record<string, string> = {
        access_denied: "Access was denied. Please try again.",
        server_error: "The authentication server encountered an error.",
        temporarily_unavailable: "Authentication is temporarily unavailable.",
      };
      setError(KNOWN_ERRORS[errorParam] ?? "Authentication failed. Please try again.");
    }
  }, []);

  // Step 2: 5s timeout for session resolution
  useEffect(() => {
    if (error) return;
    const timer = setTimeout(() => setTimedOut(true), 5000);
    return () => clearTimeout(timer);
  }, [error]);

  // Step 3: Navigate when session + profile settle.
  // F-c-5-9: short-circuit when the AuthProvider has settled (loading=false,
  // profileLoading=false, session=null, no OAuth callback hash/query, no
  // error param). Without this we'd sit on "Completing sign-in..." for the
  // full 5-second timeout window even though there's nothing to wait for.
  useEffect(() => {
    if (error || loading || profileLoading) return;
    if (session) {
      navigate(ROUTES.dashboard, { replace: true });
      return;
    }
    // No session and AuthProvider is settled: nothing to wait for.
    const hasOAuthHash =
      typeof window !== "undefined" && /access_token=|error=/.test(window.location.hash);
    if (!hasOAuthHash) {
      setError("No active sign-in to complete. Please sign in again.");
    }
  }, [session, loading, profileLoading, error, navigate]);

  // Step 4: Handle timeout
  useEffect(() => {
    if (timedOut && !session) {
      setError("Sign-in timed out. Please try again.");
    }
  }, [timedOut, session]);

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background gap-4 px-4">
        <AlertCircle className="h-10 w-10 text-danger" />
        <p className="text-sm text-zinc-400 max-w-sm text-center">{error}</p>
        <Button onClick={() => navigate(ROUTES.login, { replace: true })}>
          Back to Sign In
        </Button>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <p className="text-zinc-500">Completing sign-in...</p>
    </div>
  );
}

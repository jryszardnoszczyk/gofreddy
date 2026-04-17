import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/components/AuthProvider";
import { ROUTES } from "@/lib/routes";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/shared/Button";

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const { session, loading, tier, profileLoading } = useAuth();
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

  // Step 3: Navigate when session + profile settle
  useEffect(() => {
    if (error || loading || profileLoading) return;
    if (session) {
      navigate(ROUTES.dashboard, { replace: true });
    }
  }, [session, loading, profileLoading, tier, error, navigate]);

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

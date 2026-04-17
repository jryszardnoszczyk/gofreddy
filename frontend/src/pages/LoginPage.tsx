import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { useAuth } from "@/components/AuthProvider";
import { supabase } from "@/lib/supabase";
import { ROUTES } from "@/lib/routes";
import { Button } from "@/components/shared/Button";
import { Card, CardHeader, CardTitle } from "@/components/shared/Card";

export function LoginPage() {
  useDocumentTitle("Sign In");
  const { session, loading, tier } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSignUp, setIsSignUp] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [signUpSuccess, setSignUpSuccess] = useState(false);

  useEffect(() => {
    if (!loading && session) {
      navigate(ROUTES.dashboard, { replace: true });
    }
  }, [session, loading, tier, navigate]);

  async function handleOAuthLogin(provider: "google" | "github") {
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (error) {
      setError(error.message);
    }
  }

  async function handleForgotPassword() {
    if (!email.trim()) {
      setError("Enter your email address first.");
      return;
    }
    setResetLoading(true);
    setError(null);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/callback`,
      });
      if (error) {
        console.warn("Password reset request failed:", error.message);
      }
      // Always show success to prevent email enumeration
      setResetSent(true);
    } finally {
      setResetLoading(false);
    }
  }

  async function handleEmailLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      if (isSignUp) {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) {
          setError(error.message);
        } else if (data.user && !data.session) {
          setSignUpSuccess(true);
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) {
          setError(error.message);
        }
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-zinc-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-center text-lg">
            Sign in to Freddy
          </CardTitle>
        </CardHeader>
        <div className="space-y-3 px-6 pb-6">
          <form onSubmit={handleEmailLogin} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
              required
              minLength={6}
            />
            {!isSignUp && (
              <button
                type="button"
                onClick={handleForgotPassword}
                disabled={resetLoading}
                className="self-end text-xs text-zinc-500 hover:text-zinc-300"
              >
                {resetLoading ? "Sending..." : "Forgot password?"}
              </button>
            )}
            {resetSent && (
              <div className="rounded-lg border border-safe/30 bg-safe/5 p-3 text-xs text-safe">
                Check your email for a password reset link.
              </div>
            )}
            {signUpSuccess && (
              <div className="rounded-lg border border-safe/30 bg-safe/5 p-3 text-xs text-safe">
                Account created! Check your email to confirm your account.
              </div>
            )}
            {error && (
              <p className="text-sm text-red-400">{error}</p>
            )}
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting
                ? (isSignUp ? "Creating account..." : "Signing in...")
                : (isSignUp ? "Sign Up" : "Sign In")}
            </Button>
          </form>
          <button
            type="button"
            onClick={() => { setIsSignUp(!isSignUp); setError(null); }}
            className="w-full text-center text-xs text-zinc-500 hover:text-zinc-300"
          >
            {isSignUp
              ? "Already have an account? Sign in"
              : "No account? Sign up"}
          </button>
          <div className="relative my-2">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-700" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-zinc-900 px-2 text-zinc-500">or</span>
            </div>
          </div>
          <Button
            className="w-full"
            variant="ghost"
            onClick={() => handleOAuthLogin("google")}
          >
            Continue with Google
          </Button>
          <Button
            className="w-full"
            variant="ghost"
            onClick={() => handleOAuthLogin("github")}
          >
            Continue with GitHub
          </Button>
        </div>
      </Card>
    </div>
  );
}

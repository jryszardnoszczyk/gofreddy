import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Session, User } from "@supabase/supabase-js";
import { getAuthProfile, logoutApiSession, ApiError, type AuthProfile } from "@/lib/api";
import { supabase } from "@/lib/supabase";
import { hasProAccess } from "@/lib/tier";

interface AuthContextValue {
  session: Session | null;
  user: User | null;
  loading: boolean;
  profile: AuthProfile | null;
  profileLoading: boolean;
  profileError: string | null;
  tier: string | null;
  subscriptionStatus: string | null;
  canUseProFeatures: boolean;
  refreshProfile: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  session: null,
  user: null,
  loading: true,
  profile: null,
  profileLoading: false,
  profileError: null,
  tier: null,
  subscriptionStatus: null,
  canUseProFeatures: false,
  refreshProfile: async () => {},
  signOut: async () => {},
});

const E2E_BYPASS_ENABLED =
  import.meta.env.VITE_E2E_BYPASS_AUTH === "1" &&
  import.meta.env.DEV === true;
const E2E_BYPASS_ACCESS_TOKEN = import.meta.env.VITE_E2E_BYPASS_ACCESS_TOKEN;
const E2E_BYPASS_USER_ID = import.meta.env.VITE_E2E_BYPASS_USER_ID;
const E2E_BYPASS_EMAIL = import.meta.env.VITE_E2E_BYPASS_EMAIL;

function getE2EBypassSession(): Session | null {
  if (!E2E_BYPASS_ENABLED || typeof window === "undefined") {
    return null;
  }

  // Double-guard: only allow bypass on localhost origins
  const hostname = window.location.hostname;
  const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
  if (!isLocalhost) {
    return null;
  }

  const params = new URLSearchParams(window.location.search);
  if (params.get("__e2e_auth") !== "1") {
    return null;
  }

  const nowIso = new Date().toISOString();
  return {
    access_token: E2E_BYPASS_ACCESS_TOKEN || "e2e-bypass-token",
    token_type: "bearer",
    expires_in: 3600,
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    refresh_token: "e2e-bypass-refresh-token",
    user: {
      id: E2E_BYPASS_USER_ID || "e2e-bypass-user",
      aud: "authenticated",
      role: "authenticated",
      email: E2E_BYPASS_EMAIL || "e2e@example.com",
      email_confirmed_at: nowIso,
      phone: "",
      confirmed_at: nowIso,
      last_sign_in_at: nowIso,
      app_metadata: { provider: "e2e" },
      user_metadata: {},
      identities: [],
      created_at: nowIso,
      updated_at: nowIso,
      is_anonymous: false,
    },
  } as Session;
}

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<AuthProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  const refreshProfile = useCallback(async () => {
    if (!session) {
      setProfile(null);
      setProfileError(null);
      setProfileLoading(false);
      return;
    }

    setProfileLoading(true);
    setProfileError(null);

    try {
      const data = await getAuthProfile();
      setProfile(data);
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        // Token rejected — session is invalid, sign out cleanly
        await supabase.auth.signOut();
      } else {
        setProfileError(error instanceof Error ? error.message : "Failed to load account profile");
      }
    } finally {
      setProfileLoading(false);
    }
  }, [session]);

  useEffect(() => {
    const bypassSession = getE2EBypassSession();
    if (bypassSession) {
      setSession(bypassSession);
      setLoading(false);
      return;
    }

    // Get initial session
    supabase.auth.getSession().then(({ data: { session: s } }) => {
      setSession(s);
      setLoading(false);
    });

    // Listen for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function syncProfile() {
      if (!session) {
        if (!cancelled) {
          setProfile(null);
          setProfileError(null);
          setProfileLoading(false);
        }
        return;
      }

      // E2E bypass: use a synthetic Pro profile instead of hitting the API
      const isBypassSession =
        E2E_BYPASS_ENABLED &&
        typeof session.access_token === "string" &&
        session.access_token.length > 0 &&
        session.access_token === (E2E_BYPASS_ACCESS_TOKEN || "e2e-bypass-token");
      if (isBypassSession) {
        if (!cancelled) {
          setProfile({
            user_id: E2E_BYPASS_USER_ID || "e2e-bypass-user",
            email: E2E_BYPASS_EMAIL || "e2e@example.com",
            tier: "pro",
            subscription_status: "active",
          });
          setProfileLoading(false);
        }
        return;
      }

      if (!cancelled) {
        setProfileLoading(true);
        setProfileError(null);
      }

      try {
        const data = await getAuthProfile();
        if (!cancelled) {
          setProfile(data);
        }
      } catch (error) {
        if (cancelled) return;

        if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
          // Token rejected — session is invalid, sign out cleanly
          await supabase.auth.signOut();
        } else {
          setProfileError(error instanceof Error ? error.message : "Failed to load account profile");
        }
      } finally {
        if (!cancelled) {
          setProfileLoading(false);
        }
      }
    }

    void syncProfile();

    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  const signOut = async () => {
    // Clear user-scoped localStorage before session is lost
    if (session?.user?.id) {
      const prefix = `${session.user.id}.`;
      const keysToRemove = Object.keys(window.localStorage)
        .filter(k => k.startsWith(prefix));
      keysToRemove.forEach(k => window.localStorage.removeItem(k));
    }

    try {
      await logoutApiSession();
    } catch (error) {
      // Logout should not fail closed; clear local session regardless.
      console.warn("logout_api_failed", error);
    }

    await supabase.auth.signOut();
    setSession(null);
    setProfile(null);
    setProfileError(null);
    setProfileLoading(false);
  };

  const tier = profile ? (profile.tier ?? "free") : null;
  const subscriptionStatus = profile?.subscription_status ?? null;

  return (
    <AuthContext.Provider
      value={{
        session,
        user: session?.user ?? null,
        loading,
        profile,
        profileLoading,
        profileError,
        tier,
        subscriptionStatus,
        canUseProFeatures: hasProAccess(tier),
        refreshProfile,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

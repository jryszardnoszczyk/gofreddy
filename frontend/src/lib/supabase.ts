import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const hasSupabaseConfig = Boolean(supabaseUrl && supabaseAnonKey);

const missingConfigMessage =
  "Supabase auth is unavailable. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to enable auth.";

if (!hasSupabaseConfig) {
  console.warn(
    "Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY — auth will not work",
  );
}

function createAuthUnavailableError(): Error {
  return new Error(missingConfigMessage);
}

function createFallbackSupabaseClient(): SupabaseClient {
  const subscription = { unsubscribe: () => undefined };

  return {
    auth: {
      async getSession() {
        return {
          data: { session: null },
          error: createAuthUnavailableError(),
        };
      },
      onAuthStateChange() {
        return { data: { subscription } };
      },
      async signInWithOAuth() {
        return {
          data: { provider: null, url: null },
          error: createAuthUnavailableError(),
        };
      },
      async signUp() {
        return {
          data: { user: null, session: null },
          error: createAuthUnavailableError(),
        };
      },
      async signInWithPassword() {
        return {
          data: { user: null, session: null },
          error: createAuthUnavailableError(),
        };
      },
      async resetPasswordForEmail() {
        return { data: {}, error: null };
      },
      async signOut() {
        return { error: null };
      },
    },
  } as unknown as SupabaseClient;
}

export const supabase = hasSupabaseConfig
  ? createClient(supabaseUrl!, supabaseAnonKey!)
  : createFallbackSupabaseClient();

export const isSupabaseConfigured = hasSupabaseConfig;

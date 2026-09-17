/**
 * Learner identity. Supabase anonymous sign-in on first visit (DECISIONS.md
 * D06); the access token is what the API client sends as a Bearer header.
 * The browser's Supabase client is used for auth only, never for tables.
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { isMockMode } from "@/lib/api/client";

let client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (client) return client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    throw new Error("NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are required outside mock mode");
  }
  client = createClient(url, anonKey, { auth: { persistSession: true, autoRefreshToken: true } });
  return client;
}

/** Returns an access token, creating an anonymous session if there is none. */
export async function getAccessToken(): Promise<string | null> {
  if (isMockMode()) return "mock-token";
  const supabase = getSupabase();
  const { data } = await supabase.auth.getSession();
  if (data.session) return data.session.access_token;
  const { data: anon, error } = await supabase.auth.signInAnonymously();
  if (error) throw error;
  return anon.session?.access_token ?? null;
}

/** IANA timezone of this browser, sent to the API so streaks use local days. */
export function browserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

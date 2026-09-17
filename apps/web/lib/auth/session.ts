/**
 * Learner identity (DECISIONS.md D33). On first visit the API issues an
 * anonymous token; the browser keeps it in localStorage and sends it as a
 * Bearer header. No third-party auth client. When the stored token is
 * missing or expired, a new session is created, which means a new learner:
 * account linking is the later feature that makes identity durable.
 */
import { isMockMode } from "@/lib/api/client";

const STORAGE_KEY = "rizalai.session";
const EXPIRY_MARGIN_MS = 60_000;

interface StoredSession {
  access_token: string;
  user_id: string;
  expires_at: string;
}

let memory: StoredSession | null = null;
let inflight: Promise<StoredSession> | null = null;

function apiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

/** IANA timezone of this browser, sent to the API so streaks use local days. */
export function browserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

function read(): StoredSession | null {
  if (memory) return memory;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredSession) : null;
  } catch {
    return null;
  }
}

function write(session: StoredSession): void {
  memory = session;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } catch {
    /* private mode or blocked storage: the in-memory copy carries this page */
  }
}

function isLive(session: StoredSession | null): session is StoredSession {
  if (!session) return false;
  const expires = Date.parse(session.expires_at);
  return Number.isFinite(expires) && expires - EXPIRY_MARGIN_MS > Date.now();
}

async function createSession(): Promise<StoredSession> {
  const res = await fetch(`${apiUrl()}/session/anonymous`, {
    method: "POST",
    headers: { Accept: "application/json", "X-Timezone": browserTimezone() },
  });
  if (!res.ok) throw new Error(`Could not start a session (${res.status})`);
  const session = (await res.json()) as StoredSession;
  write(session);
  return session;
}

/** Returns an access token, creating an anonymous session if there is none. */
export async function getAccessToken(): Promise<string | null> {
  if (isMockMode()) return "mock-token";
  const current = read();
  if (isLive(current)) {
    memory = current;
    return current.access_token;
  }
  inflight ??= createSession().finally(() => {
    inflight = null;
  });
  return (await inflight).access_token;
}

/** Forget the current session (used by tests and a future sign-out). */
export function clearSession(): void {
  memory = null;
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

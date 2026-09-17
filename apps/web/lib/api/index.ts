import { createHttpClient, createMockClient, isMockMode, type ApiClient } from "./client";
import { getAccessToken } from "@/lib/auth/session";

let instance: ApiClient | null = null;

/** Process-wide client. Mock mode needs no backend and no credentials. */
export function getApiClient(): ApiClient {
  if (instance) return instance;
  instance = isMockMode()
    ? createMockClient(120)
    : createHttpClient(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000", getAccessToken);
  return instance;
}

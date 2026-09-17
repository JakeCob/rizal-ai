/**
 * Behaviors:
 * - in mock mode there is always a token and Supabase is never touched
 * - outside mock mode, missing Supabase env is a clear error
 * - the browser timezone is an IANA name, falling back to UTC
 */
import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("getAccessToken", () => {
  it("returns a mock token in mock mode", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_MODE", "mock");
    const { getAccessToken } = await import("./session");
    expect(await getAccessToken()).toBe("mock-token");
  });

  it("fails clearly without Supabase env outside mock mode", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_MODE", "");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "");
    const { getAccessToken } = await import("./session");
    await expect(getAccessToken()).rejects.toThrow(/NEXT_PUBLIC_SUPABASE_URL/);
  });
});

describe("browserTimezone", () => {
  it("returns an IANA zone or UTC", async () => {
    const { browserTimezone } = await import("./session");
    expect(browserTimezone()).toMatch(/^[A-Za-z_]+(\/[A-Za-z_]+)*$|^UTC$/);
  });
});

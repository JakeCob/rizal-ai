/**
 * Behaviors (DECISIONS.md D33): learner identity is an anonymous token the
 * API issues on first visit.
 * - with no stored token, the client POSTs /session/anonymous once, stores
 *   the token, and reuses it on later calls
 * - an expired stored token is replaced
 * - mock mode never touches the network
 * - storage failures fall back to an in-memory token for this page
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const fetchSpy = vi.fn();

function tokenExpiring(inSeconds: number) {
  const exp = Math.floor(Date.now() / 1000) + inSeconds;
  return { access_token: `tok-${exp}`, user_id: "u1", expires_at: new Date(exp * 1000).toISOString() };
}

beforeEach(() => {
  vi.resetModules();
  vi.stubGlobal("fetch", fetchSpy);
  localStorage.clear();
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  fetchSpy.mockReset();
});

describe("getAccessToken", () => {
  it("creates an anonymous session once and reuses it", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_MODE", "");
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.test");
    const session = tokenExpiring(3600);
    fetchSpy.mockResolvedValue({ ok: true, status: 201, json: async () => session });
    const { getAccessToken } = await import("./session");

    expect(await getAccessToken()).toBe(session.access_token);
    expect(await getAccessToken()).toBe(session.access_token);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(fetchSpy.mock.calls[0][0]).toBe("http://api.test/session/anonymous");
    expect(fetchSpy.mock.calls[0][1].method).toBe("POST");
    expect(JSON.parse(localStorage.getItem("rizalai.session")!).access_token).toBe(session.access_token);
  });

  it("replaces an expired stored token", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_MODE", "");
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.test");
    localStorage.setItem("rizalai.session", JSON.stringify(tokenExpiring(-10)));
    const fresh = tokenExpiring(3600);
    fetchSpy.mockResolvedValue({ ok: true, status: 201, json: async () => fresh });
    const { getAccessToken } = await import("./session");
    expect(await getAccessToken()).toBe(fresh.access_token);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("returns a mock token in mock mode without fetching", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_MODE", "mock");
    const { getAccessToken } = await import("./session");
    expect(await getAccessToken()).toBe("mock-token");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("throws a clear error when the session endpoint fails", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_MODE", "");
    fetchSpy.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) });
    const { getAccessToken } = await import("./session");
    await expect(getAccessToken()).rejects.toThrow(/session/);
  });
});

describe("browserTimezone", () => {
  it("returns an IANA zone or UTC", async () => {
    const { browserTimezone } = await import("./session");
    expect(browserTimezone()).toMatch(/^[A-Za-z_]+(\/[A-Za-z_]+)*$|^UTC$/);
  });
});

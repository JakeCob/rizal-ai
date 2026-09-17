/**
 * Behaviors:
 * - the http client sends the bearer token and parses JSON
 * - a non-2xx response becomes an ApiError with the status
 * - a missing token sends no Authorization header
 * - the mock client serves the fixtures and 404s unknown lessons
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, createHttpClient, createMockClient, isMockMode } from "./client";
import { LESSON_ID, MOCK_LESSON, MOCK_TREE, MOCK_USER } from "./fixtures";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

function fetchReturning(status: number, body: unknown) {
  const spy = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", spy);
  return spy;
}

describe("createHttpClient", () => {
  it("sends the bearer token and returns parsed JSON", async () => {
    const spy = fetchReturning(200, MOCK_TREE);
    const client = createHttpClient("http://api.test", async () => "tok");
    const tree = await client.getTree();
    expect(tree).toEqual(MOCK_TREE);
    expect(spy).toHaveBeenCalledWith("http://api.test/tree", {
      headers: { Accept: "application/json", Authorization: "Bearer tok" },
    });
  });

  it("omits Authorization when there is no token", async () => {
    const spy = fetchReturning(200, MOCK_USER);
    const client = createHttpClient("http://api.test", async () => null);
    await client.getMe();
    expect(spy.mock.calls[0][1]).toEqual({ headers: { Accept: "application/json" } });
  });

  it("throws ApiError with the status on failure", async () => {
    fetchReturning(404, { detail: "lesson not found" });
    const client = createHttpClient("http://api.test", async () => "tok");
    await expect(client.getLesson("nope")).rejects.toMatchObject({ name: "ApiError", status: 404 });
    await expect(client.getLesson("nope")).rejects.toBeInstanceOf(ApiError);
  });

  it("builds the lesson path from the id", async () => {
    const spy = fetchReturning(200, MOCK_LESSON);
    const client = createHttpClient("http://api.test", async () => "tok");
    await client.getLesson(LESSON_ID);
    expect(spy.mock.calls[0][0]).toBe(`http://api.test/lessons/${LESSON_ID}`);
  });
});

describe("createMockClient", () => {
  it("serves the fixtures", async () => {
    const client = createMockClient(0);
    expect(await client.getTree()).toBe(MOCK_TREE);
    expect(await client.getLesson(LESSON_ID)).toBe(MOCK_LESSON);
    expect(await client.getMe()).toBe(MOCK_USER);
  });

  it("404s an unknown lesson", async () => {
    const client = createMockClient(0);
    await expect(client.getLesson("unknown")).rejects.toMatchObject({ status: 404 });
  });
});

describe("isMockMode", () => {
  it("reads NEXT_PUBLIC_API_MODE", () => {
    vi.stubEnv("NEXT_PUBLIC_API_MODE", "mock");
    expect(isMockMode()).toBe(true);
    vi.stubEnv("NEXT_PUBLIC_API_MODE", "");
    expect(isMockMode()).toBe(false);
  });
});

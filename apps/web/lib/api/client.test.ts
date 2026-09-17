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
    expect(spy.mock.calls[0][0]).toBe("http://api.test/tree");
    expect(spy.mock.calls[0][1].headers).toMatchObject({ Accept: "application/json", Authorization: "Bearer tok" });
  });

  it("omits Authorization when there is no token", async () => {
    const spy = fetchReturning(200, MOCK_USER);
    const client = createHttpClient("http://api.test", async () => null);
    await client.getMe();
    expect(spy.mock.calls[0][1].headers).not.toHaveProperty("Authorization");
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
    expect(await client.getTree()).toEqual(MOCK_TREE);
    expect(await client.getLesson(LESSON_ID)).toBe(MOCK_LESSON);
    expect(await client.getMe()).toEqual(MOCK_USER);
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

describe("progress and reflection methods", () => {
  it("posts attempts and completion, and gets the reflection and review due", async () => {
    const spy = fetchReturning(200, { ok: true });
    const client = createHttpClient("http://api.test", async () => "tok");
    await client.postAttempt({ exercise_id: "e1", correct: true, response: { tokens: ["a"] }, duration_ms: 5 });
    expect(spy.mock.calls[0][0]).toBe("http://api.test/attempts");
    expect(spy.mock.calls[0][1].method).toBe("POST");
    expect(JSON.parse(spy.mock.calls[0][1].body)).toMatchObject({ exercise_id: "e1", response: { tokens: ["a"] } });
    expect(spy.mock.calls[0][1].headers["Content-Type"]).toBe("application/json");

    await client.completeLesson("L1");
    expect(spy.mock.calls[1][0]).toBe("http://api.test/lessons/L1/complete");
    expect(spy.mock.calls[1][1].method).toBe("POST");

    await client.getReflection("L1");
    expect(spy.mock.calls[2][0]).toBe("http://api.test/lessons/L1/reflection");

    await client.getReviewDue();
    expect(spy.mock.calls[3][0]).toBe("http://api.test/review/due");

    await client.postReviewAnswer({ exercise_id: "e1", response: { optionIndex: 0 }, duration_ms: 0 });
    expect(spy.mock.calls[4][0]).toBe("http://api.test/review/answer");
  });

  it("sends the browser timezone header", async () => {
    const spy = fetchReturning(200, MOCK_USER);
    const client = createHttpClient("http://api.test", async () => "tok");
    await client.getMe();
    expect(spy.mock.calls[0][1].headers["X-Timezone"]).toMatch(/\w/);
  });
});

describe("createMockClient progress state", () => {
  it("grades attempts, spends hearts, completes with XP, marks the tree done, and serves review items", async () => {
    const client = createMockClient(0);
    const first = MOCK_LESSON.exercises[0];
    const wrong = await client.postAttempt({ exercise_id: first.id, correct: true, response: { tokens: ["gabi"] }, duration_ms: 1 });
    expect(wrong).toEqual({ correct: false, hearts: 4 });
    await expect(client.postAttempt({ exercise_id: "nope", correct: true, response: {}, duration_ms: 1 })).rejects.toMatchObject({ status: 404 });

    for (const e of MOCK_LESSON.exercises) {
      const ex = e.exercise;
      const response = ex.type === "comprehension_mc" ? { optionIndex: ex.correct_index } : { tokens: ex.answer_tokens };
      const out = await client.postAttempt({ exercise_id: e.id, correct: true, response, duration_ms: 1 });
      expect(out.correct).toBe(true);
    }
    const done = await client.completeLesson(LESSON_ID);
    expect(done.xp_earned).toBe(60);
    expect(done.total_xp).toBe(60);
    expect(done.streak_count).toBe(1);
    expect((await client.getMe()).total_xp).toBe(60);
    expect((await client.getTree()).units[0].lessons[0].status).toBe("done");
    await expect(client.completeLesson(LESSON_ID)).rejects.toMatchObject({ status: 409 });
    await expect(client.completeLesson("other")).rejects.toMatchObject({ status: 404 });

    const due = await client.getReviewDue();
    expect(due.items).toHaveLength(6);
    const answer = await client.postReviewAnswer({ exercise_id: first.id, response: { tokens: ["gabi"] }, duration_ms: 1 });
    expect(answer.correct).toBe(false);
    expect(answer.hearts).toBe(5);
    await expect(client.postReviewAnswer({ exercise_id: "nope", response: {}, duration_ms: 1 })).rejects.toMatchObject({ status: 404 });
    await expect(client.getReflection("other")).rejects.toMatchObject({ status: 404 });
    expect((await client.getReflection(LESSON_ID)).status).toBe("published");
  });

  it("returns no review items before the lesson is done", async () => {
    const client = createMockClient(0);
    expect((await client.getReviewDue()).items).toEqual([]);
  });
});

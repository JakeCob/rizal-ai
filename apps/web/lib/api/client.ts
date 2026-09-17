/**
 * The only way the web app talks to the backend. A thin typed fetch client
 * over FastAPI (DECISIONS.md D14). In mock mode it serves fixtures and keeps
 * a little in-memory state so a lesson can be played end to end with no
 * backend, which is what unit tests and the Playwright smoke use.
 */
import type {
  AttemptIn,
  AttemptOut,
  CompleteOut,
  LessonOut,
  ReflectionOut,
  ReviewAnswerIn,
  ReviewAnswerOut,
  ReviewDueOut,
  Tree,
  UserOut,
} from "@/lib/types.generated";
import { grade } from "@/lib/runner/grade";
import { MOCK_LESSON, MOCK_TREE, MOCK_USER } from "./fixtures";
import { MOCK_REFLECTION } from "./fixtures.reflection";

export interface ApiClient {
  getTree(): Promise<Tree>;
  getLesson(id: string): Promise<LessonOut>;
  getMe(): Promise<UserOut>;
  getReflection(lessonId: string): Promise<ReflectionOut>;
  postAttempt(body: AttemptIn): Promise<AttemptOut>;
  completeLesson(lessonId: string): Promise<CompleteOut>;
  getReviewDue(): Promise<ReviewDueOut>;
  postReviewAnswer(body: ReviewAnswerIn): Promise<ReviewAnswerOut>;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type TokenSource = () => Promise<string | null>;

function browserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export function createHttpClient(baseUrl: string, getToken: TokenSource): ApiClient {
  async function request<T>(path: string, init?: { method?: "GET" | "POST"; body?: unknown }): Promise<T> {
    const token = await getToken();
    const headers: Record<string, string> = { Accept: "application/json", "X-Timezone": browserTimezone() };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (init?.body !== undefined) headers["Content-Type"] = "application/json";
    const res = await fetch(`${baseUrl}${path}`, {
      method: init?.method ?? "GET",
      headers,
      body: init?.body === undefined ? undefined : JSON.stringify(init.body),
    });
    if (!res.ok) throw new ApiError(res.status, `${path} failed with ${res.status}`);
    return (await res.json()) as T;
  }
  return {
    getTree: () => request<Tree>("/tree"),
    getLesson: (id) => request<LessonOut>(`/lessons/${id}`),
    getMe: () => request<UserOut>("/me"),
    getReflection: (id) => request<ReflectionOut>(`/lessons/${id}/reflection`),
    postAttempt: (body) => request<AttemptOut>("/attempts", { method: "POST", body }),
    completeLesson: (id) => request<CompleteOut>(`/lessons/${id}/complete`, { method: "POST", body: {} }),
    getReviewDue: () => request<ReviewDueOut>("/review/due"),
    postReviewAnswer: (body) => request<ReviewAnswerOut>("/review/answer", { method: "POST", body }),
  };
}

export function createMockClient(delayMs = 0): ApiClient {
  const later = <T>(value: T) => new Promise<T>((resolve) => setTimeout(() => resolve(value), delayMs));
  const state = { user: { ...MOCK_USER }, latest: new Map<string, boolean>(), done: false };
  const exerciseById = new Map(MOCK_LESSON.exercises.map((e) => [e.id, e]));

  return {
    getTree: () =>
      later(
        state.done
          ? {
              units: MOCK_TREE.units.map((u) => ({
                ...u,
                lessons: u.lessons.map((l) => (l.id === MOCK_LESSON.id ? { ...l, status: "done" as const } : l)),
              })),
            }
          : MOCK_TREE,
      ),
    getLesson: (id) =>
      id === MOCK_LESSON.id ? later(MOCK_LESSON) : Promise.reject(new ApiError(404, "lesson not found")),
    getMe: () => later({ ...state.user }),
    getReflection: (id) =>
      id === MOCK_LESSON.id ? later(MOCK_REFLECTION) : Promise.reject(new ApiError(404, "lesson not found")),
    postAttempt: (body) => {
      const item = exerciseById.get(body.exercise_id);
      if (!item) return Promise.reject(new ApiError(404, "exercise not found"));
      const correct = grade(item.exercise, body.response as Parameters<typeof grade>[1]);
      state.latest.set(body.exercise_id, correct);
      if (!correct) state.user.hearts = Math.max(0, state.user.hearts - 1);
      return later({ correct, hearts: state.user.hearts });
    },
    completeLesson: (id) => {
      if (id !== MOCK_LESSON.id) return Promise.reject(new ApiError(404, "lesson not found"));
      if (state.latest.size === 0) return Promise.reject(new ApiError(409, "no attempts"));
      const results = MOCK_LESSON.exercises.map((e) => {
        const correct = state.latest.get(e.id) ?? false;
        return { exercise_id: e.id, correct, xp: correct ? e.exercise.xp : 0 };
      });
      const xp = results.reduce((sum, r) => sum + r.xp, 0);
      state.user.total_xp += xp;
      state.user.streak_count = Math.max(1, state.user.streak_count);
      state.done = true;
      state.latest.clear();
      return later({
        lesson_id: id,
        xp_earned: xp,
        total_xp: state.user.total_xp,
        streak_count: state.user.streak_count,
        hearts: state.user.hearts,
        results,
      });
    },
    getReviewDue: () =>
      later({
        items: state.done
          ? MOCK_LESSON.exercises.map((e) => ({
              exercise: e,
              due_at: new Date().toISOString(),
              state: "learning",
              reps: 1,
            }))
          : [],
      }),
    postReviewAnswer: (body) => {
      const item = exerciseById.get(body.exercise_id);
      if (!item) return Promise.reject(new ApiError(404, "exercise not found"));
      const correct = grade(item.exercise, body.response as Parameters<typeof grade>[1]);
      state.user.hearts = Math.min(5, state.user.hearts + 1);
      return later({
        correct,
        hearts: state.user.hearts,
        session_answered: 1,
        next_due_at: new Date(Date.now() + 600_000).toISOString(),
        state: "learning",
      });
    },
  };
}

export function isMockMode(): boolean {
  return process.env.NEXT_PUBLIC_API_MODE === "mock";
}

/**
 * The only way the web app talks to the backend. A thin typed fetch client
 * over FastAPI (DECISIONS.md D14). In mock mode it serves fixtures so the UI
 * runs with no backend, which is what unit tests and the Playwright smoke use.
 */
import type { LessonOut, Tree, UserOut } from "@/lib/types.generated";
import { MOCK_LESSON, MOCK_TREE, MOCK_USER } from "./fixtures";

export interface ApiClient {
  getTree(): Promise<Tree>;
  getLesson(id: string): Promise<LessonOut>;
  getMe(): Promise<UserOut>;
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

export function createHttpClient(baseUrl: string, getToken: TokenSource): ApiClient {
  async function request<T>(path: string): Promise<T> {
    const token = await getToken();
    const headers: Record<string, string> = { Accept: "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${baseUrl}${path}`, { headers });
    if (!res.ok) throw new ApiError(res.status, `${path} failed with ${res.status}`);
    return (await res.json()) as T;
  }
  return {
    getTree: () => request<Tree>("/tree"),
    getLesson: (id) => request<LessonOut>(`/lessons/${id}`),
    getMe: () => request<UserOut>("/me"),
  };
}

export function createMockClient(delayMs = 0): ApiClient {
  const later = <T>(value: T) => new Promise<T>((resolve) => setTimeout(() => resolve(value), delayMs));
  return {
    getTree: () => later(MOCK_TREE),
    getLesson: (id) =>
      id === MOCK_LESSON.id ? later(MOCK_LESSON) : Promise.reject(new ApiError(404, "lesson not found")),
    getMe: () => later(MOCK_USER),
  };
}

export function isMockMode(): boolean {
  return process.env.NEXT_PUBLIC_API_MODE === "mock";
}

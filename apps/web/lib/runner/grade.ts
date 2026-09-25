/**
 * Local grading. The answer key ships with the lesson so a check never waits
 * on the network (DECISIONS.md D15). The server re-grades at completion.
 * A token answer is correct when the picked tokens equal answer_tokens or any
 * accepted order, ignoring letter case (D34), the mirror of grade_response in
 * apps/api/src/rizalai/progress/rules.py. Like the API, malformed or empty
 * candidates are skipped and a malformed tap grades wrong; it never throws.
 */
import type { Exercise } from "@/lib/types.generated";

export type ExerciseResponse = { tokens: string[] } | { optionIndex: number };

export function grade(exercise: Exercise, response: ExerciseResponse): boolean {
  if (exercise.type === "comprehension_mc") {
    return "optionIndex" in response && response.optionIndex === exercise.correct_index;
  }
  if (!("tokens" in response)) return false;
  const picked = lowered(response.tokens);
  if (picked === null) return false;
  const orders: unknown = exercise.accepted_orders;
  const candidates: unknown[] = [exercise.answer_tokens, ...(Array.isArray(orders) ? orders : [])];
  return candidates.some((candidate) => {
    const expected = lowered(candidate);
    return expected !== null && expected.length > 0 && sameSequence(expected, picked);
  });
}

/** Lowercased tokens, or null when the value is not an array of strings (stored data is not re-validated). */
function lowered(value: unknown): string[] | null {
  if (!Array.isArray(value) || !value.every((t) => typeof t === "string")) return null;
  return value.map((t: string) => t.toLowerCase());
}

/** Equal length and equal tokens in order; both sides are already lowercased. */
function sameSequence(expected: readonly string[], picked: readonly string[]): boolean {
  return expected.length === picked.length && expected.every((t, i) => t === picked[i]);
}

/** The answer as shown on a wrong-answer feedback sheet. */
export function correctAnswerText(exercise: Exercise): string {
  if (exercise.type === "comprehension_mc") return exercise.options[exercise.correct_index];
  return exercise.answer_tokens.join(" ");
}

export function isEmptyResponse(response: ExerciseResponse | null): boolean {
  if (response === null) return true;
  if ("tokens" in response) return response.tokens.length === 0;
  return false;
}

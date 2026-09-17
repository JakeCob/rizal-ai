/**
 * Local grading. The answer key ships with the lesson so a check never waits
 * on the network (DECISIONS.md D15). The server re-grades at completion.
 */
import type { Exercise } from "@/lib/types.generated";

export type ExerciseResponse = { tokens: string[] } | { optionIndex: number };

export function grade(exercise: Exercise, response: ExerciseResponse): boolean {
  if (exercise.type === "comprehension_mc") {
    return "optionIndex" in response && response.optionIndex === exercise.correct_index;
  }
  if (!("tokens" in response)) return false;
  const expected: readonly string[] = exercise.answer_tokens;
  return expected.length === response.tokens.length && expected.every((t, i) => t === response.tokens[i]);
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

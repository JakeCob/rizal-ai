/**
 * Behaviors of the runner state machine, independent of React:
 * - starts on the first vignette beat
 * - a beat with exercise_after runs that exercise before the next beat
 * - after the last beat, remaining exercises run in order, skipping any
 *   already run
 * - checking a correct answer awards xp and enters feedback
 * - checking a wrong answer spends a heart and enters feedback
 * - zero hearts ends the session as "out_of_hearts"
 * - after the last exercise, continue enters "complete" with the xp total
 */
import { describe, expect, it } from "vitest";
import { initialState, reduce, type RunnerState } from "./reducer";
import { MOCK_LESSON } from "@/lib/api/fixtures";

function run(state: RunnerState, ...actions: Parameters<typeof reduce>[1][]): RunnerState {
  return actions.reduce((s, a) => reduce(s, a), state);
}

const correctFor = (state: RunnerState) => {
  const ex = MOCK_LESSON.exercises[state.exerciseIndex!].exercise;
  return ex.type === "comprehension_mc"
    ? { type: "CHOOSE_OPTION" as const, index: ex.correct_index }
    : { type: "SET_TOKENS" as const, tokens: ex.answer_tokens };
};

describe("runner reducer", () => {
  it("starts on the first beat with full hearts and zero xp", () => {
    const s = initialState(MOCK_LESSON, { hearts: 5 });
    expect(s.phase).toBe("vignette");
    expect(s.beatIndex).toBe(0);
    expect(s.hearts).toBe(5);
    expect(s.xp).toBe(0);
  });

  it("runs the exercise attached to a beat before the next beat", () => {
    let s = initialState(MOCK_LESSON, { hearts: 5 });
    s = run(s, { type: "NEXT_BEAT" }); // now on b2, which has exercise_after ex1
    expect(s.beatIndex).toBe(1);
    s = run(s, { type: "NEXT_BEAT" });
    expect(s.phase).toBe("exercise");
    expect(MOCK_LESSON.exercises[s.exerciseIndex!].exercise.key).toBe("ex1");
    s = run(s, correctFor(s), { type: "CHECK" }, { type: "CONTINUE" });
    expect(s.phase).toBe("vignette");
    expect(s.beatIndex).toBe(2);
  });

  it("after the last beat, runs remaining exercises in order and skips ex1", () => {
    let s = initialState(MOCK_LESSON, { hearts: 5 });
    s = run(s, { type: "NEXT_BEAT" }, { type: "NEXT_BEAT" }); // ex1
    s = run(s, correctFor(s), { type: "CHECK" }, { type: "CONTINUE" });
    s = run(s, { type: "NEXT_BEAT" }, { type: "NEXT_BEAT" }); // past b4
    expect(s.phase).toBe("exercise");
    const keys: string[] = [];
    while (s.phase === "exercise") {
      keys.push(MOCK_LESSON.exercises[s.exerciseIndex!].exercise.key);
      s = run(s, correctFor(s), { type: "CHECK" }, { type: "CONTINUE" });
    }
    expect(keys).toEqual(["ex2", "ex3", "ex4", "ex5", "ex6"]);
    expect(s.phase).toBe("complete");
    expect(s.xp).toBe(60);
  });

  it("a correct check awards xp and enters feedback", () => {
    let s = initialState(MOCK_LESSON, { hearts: 5 });
    s = run(s, { type: "NEXT_BEAT" }, { type: "NEXT_BEAT" });
    s = run(s, correctFor(s), { type: "CHECK" });
    expect(s.phase).toBe("feedback");
    expect(s.lastResult).toEqual({ correct: true, exerciseId: MOCK_LESSON.exercises[0].id });
    expect(s.xp).toBe(10);
    expect(s.hearts).toBe(5);
  });

  it("a wrong check spends a heart and awards nothing", () => {
    let s = initialState(MOCK_LESSON, { hearts: 5 });
    s = run(s, { type: "NEXT_BEAT" }, { type: "NEXT_BEAT" });
    s = run(s, { type: "SET_TOKENS", tokens: ["gabi"] }, { type: "CHECK" });
    expect(s.phase).toBe("feedback");
    expect(s.lastResult?.correct).toBe(false);
    expect(s.hearts).toBe(4);
    expect(s.xp).toBe(0);
  });

  it("running out of hearts ends the session", () => {
    let s = initialState(MOCK_LESSON, { hearts: 1 });
    s = run(s, { type: "NEXT_BEAT" }, { type: "NEXT_BEAT" });
    s = run(s, { type: "SET_TOKENS", tokens: ["gabi"] }, { type: "CHECK" }, { type: "CONTINUE" });
    expect(s.phase).toBe("out_of_hearts");
  });

  it("CHECK without a response is a no-op", () => {
    let s = initialState(MOCK_LESSON, { hearts: 5 });
    s = run(s, { type: "NEXT_BEAT" }, { type: "NEXT_BEAT" });
    const before = s;
    s = run(s, { type: "CHECK" });
    expect(s).toBe(before);
  });

  it("records every result for the completion summary", () => {
    let s = initialState(MOCK_LESSON, { hearts: 5 });
    s = run(s, { type: "NEXT_BEAT" }, { type: "NEXT_BEAT" });
    s = run(s, { type: "SET_TOKENS", tokens: ["gabi"] }, { type: "CHECK" }, { type: "CONTINUE" });
    s = run(s, { type: "NEXT_BEAT" }, { type: "NEXT_BEAT" });
    while (s.phase === "exercise") {
      s = run(s, correctFor(s), { type: "CHECK" }, { type: "CONTINUE" });
    }
    expect(s.results).toHaveLength(6);
    expect(s.results.filter((r) => r.correct)).toHaveLength(5);
    expect(s.xp).toBe(50);
  });
});

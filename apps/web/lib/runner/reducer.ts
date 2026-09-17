/**
 * The runner state machine. Pure, so it is tested without React and the
 * component is a thin shell around it.
 *
 * Flow: vignette beats in order. A beat with exercise_after runs that
 * exercise before the next beat. After the last beat, every exercise not yet
 * run plays in order. Wrong answers spend hearts; zero hearts ends the
 * session. Nothing here talks to the network.
 */
import type { LessonOut } from "@/lib/types.generated";
import { grade, isEmptyResponse, type ExerciseResponse } from "./grade";

export type Phase = "vignette" | "exercise" | "feedback" | "complete" | "out_of_hearts";

export interface Result {
  exerciseId: string;
  correct: boolean;
}

export interface RunnerState {
  lesson: LessonOut;
  phase: Phase;
  beatIndex: number;
  exerciseIndex: number | null;
  /** Beat to resume after an exercise attached to a beat; null when in the tail. */
  resumeBeat: number | null;
  ranKeys: string[];
  hearts: number;
  xp: number;
  response: ExerciseResponse | null;
  results: Result[];
  lastResult: Result | null;
}

export type RunnerAction =
  | { type: "NEXT_BEAT" }
  | { type: "SET_TOKENS"; tokens: string[] }
  | { type: "CHOOSE_OPTION"; index: number }
  | { type: "CHECK" }
  | { type: "CONTINUE" };

export function initialState(lesson: LessonOut, opts: { hearts: number }): RunnerState {
  const hasVignette = lesson.vignette.length > 0;
  const base: RunnerState = {
    lesson,
    phase: "vignette",
    beatIndex: 0,
    exerciseIndex: null,
    resumeBeat: null,
    ranKeys: [],
    hearts: opts.hearts,
    xp: 0,
    response: null,
    results: [],
    lastResult: null,
  };
  return hasVignette ? base : enterTail(base);
}

function exerciseIndexForKey(state: RunnerState, key: string): number | null {
  const idx = state.lesson.exercises.findIndex((e) => e.exercise.key === key);
  return idx === -1 ? null : idx;
}

function nextUnrunIndex(state: RunnerState): number | null {
  const idx = state.lesson.exercises.findIndex((e) => !state.ranKeys.includes(e.exercise.key));
  return idx === -1 ? null : idx;
}

function enterExercise(state: RunnerState, exerciseIndex: number, resumeBeat: number | null): RunnerState {
  return { ...state, phase: "exercise", exerciseIndex, resumeBeat, response: null };
}

/** Start the remaining exercises, or finish if none are left. */
function enterTail(state: RunnerState): RunnerState {
  const next = nextUnrunIndex(state);
  if (next === null) return { ...state, phase: "complete", exerciseIndex: null, resumeBeat: null };
  return enterExercise(state, next, null);
}

function nextBeat(state: RunnerState): RunnerState {
  const beat = state.lesson.vignette[state.beatIndex];
  const attached = beat?.exercise_after ?? null;
  if (attached && !state.ranKeys.includes(attached)) {
    const idx = exerciseIndexForKey(state, attached);
    if (idx !== null) return enterExercise(state, idx, state.beatIndex + 1);
  }
  if (state.beatIndex + 1 < state.lesson.vignette.length) {
    return { ...state, beatIndex: state.beatIndex + 1 };
  }
  return enterTail(state);
}

function check(state: RunnerState): RunnerState {
  if (state.exerciseIndex === null || isEmptyResponse(state.response)) return state;
  const item = state.lesson.exercises[state.exerciseIndex];
  const correct = grade(item.exercise, state.response as ExerciseResponse);
  const result: Result = { exerciseId: item.id, correct };
  return {
    ...state,
    phase: "feedback",
    xp: correct ? state.xp + item.exercise.xp : state.xp,
    hearts: correct ? state.hearts : Math.max(0, state.hearts - 1),
    results: [...state.results, result],
    lastResult: result,
  };
}

function afterFeedback(state: RunnerState): RunnerState {
  if (state.hearts === 0) return { ...state, phase: "out_of_hearts" };
  const item = state.exerciseIndex === null ? null : state.lesson.exercises[state.exerciseIndex];
  const ranKeys = item ? [...state.ranKeys, item.exercise.key] : state.ranKeys;
  const next: RunnerState = { ...state, ranKeys, exerciseIndex: null, response: null };
  if (state.resumeBeat !== null) {
    if (state.resumeBeat < state.lesson.vignette.length) {
      return { ...next, phase: "vignette", beatIndex: state.resumeBeat, resumeBeat: null };
    }
    return enterTail({ ...next, resumeBeat: null });
  }
  return enterTail(next);
}

export function reduce(state: RunnerState, action: RunnerAction): RunnerState {
  switch (action.type) {
    case "NEXT_BEAT":
      return state.phase === "vignette" ? nextBeat(state) : state;
    case "SET_TOKENS":
      return state.phase === "exercise" ? { ...state, response: { tokens: action.tokens } } : state;
    case "CHOOSE_OPTION":
      return state.phase === "exercise" ? { ...state, response: { optionIndex: action.index } } : state;
    case "CHECK":
      return state.phase === "exercise" ? check(state) : state;
    case "CONTINUE":
      return state.phase === "feedback" ? afterFeedback(state) : state;
    default:
      return state;
  }
}

export function progressFraction(state: RunnerState): number {
  const total = state.lesson.exercises.length;
  if (total === 0) return state.phase === "complete" ? 1 : 0;
  return state.results.length / total;
}

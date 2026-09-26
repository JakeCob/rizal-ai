"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { Flame, Heart, X } from "lucide-react";
import { ReflectionCard } from "@/components/card/ReflectionCard";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { getApiClient } from "@/lib/api";
import type { ApiClient } from "@/lib/api/client";
import { correctAnswerText, grade, isEmptyResponse, type ExerciseResponse } from "@/lib/runner/grade";
import { initialState, progressFraction, reduce } from "@/lib/runner/reducer";
import type { CompleteOut, LessonOut, ReflectionOut } from "@/lib/types.generated";
import { ExerciseView, scrollWindowToTop } from "./ExerciseView";
import { VignettePlayer } from "./VignettePlayer";

/**
 * The exercise runner. The whole lesson is in memory, so every transition is
 * local state (DECISIONS.md D14). Network happens at three edges only: the
 * reflection is prefetched on mount, each Check posts an attempt without
 * waiting, and the last exercise triggers one completion call (D15).
 */
export function Runner({
  lesson,
  hearts,
  api,
  onCompleted,
}: {
  lesson: LessonOut;
  hearts: number;
  api?: ApiClient;
  onCompleted?: (result: CompleteOut) => void;
}) {
  const client = useMemo(() => api ?? getApiClient(), [api]);
  const [state, dispatch] = useReducer(reduce, { lesson, hearts }, (init) => initialState(init.lesson, { hearts: init.hearts }));
  const [reflection, setReflection] = useState<ReflectionOut | null>(null);
  const [completion, setCompletion] = useState<CompleteOut | null>(null);
  const [completionFailed, setCompletionFailed] = useState(false);
  const exerciseStartedAt = useRef<number>(Date.now());
  const completedOnce = useRef(false);

  useEffect(() => {
    let cancelled = false;
    client
      .getReflection(lesson.id)
      .then((r) => !cancelled && setReflection(r))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [client, lesson.id]);

  useEffect(() => {
    exerciseStartedAt.current = Date.now();
  }, [state.exerciseIndex]);

  useEffect(() => {
    if (state.phase !== "complete" || completedOnce.current) return;
    completedOnce.current = true;
    client
      .completeLesson(lesson.id)
      .then((result) => {
        setCompletion(result);
        onCompleted?.(result);
      })
      .catch(() => setCompletionFailed(true));
  }, [state.phase, client, lesson.id, onCompleted]);

  const onResponse = useCallback((response: ExerciseResponse) => {
    if ("tokens" in response) dispatch({ type: "SET_TOKENS", tokens: response.tokens });
    else dispatch({ type: "CHOOSE_OPTION", index: response.optionIndex });
  }, []);

  const current = state.exerciseIndex === null ? null : lesson.exercises[state.exerciseIndex];
  const canCheck = !isEmptyResponse(state.response);

  const check = () => {
    if (!current || isEmptyResponse(state.response) || state.response === null) return;
    const correct = grade(current.exercise, state.response);
    client
      .postAttempt({
        exercise_id: current.id,
        correct,
        response: state.response,
        duration_ms: Math.max(0, Date.now() - exerciseStartedAt.current),
      })
      .catch(() => undefined);
    dispatch({ type: "CHECK" });
  };

  if (state.phase === "complete") {
    return (
      <EndScreen
        title="Lesson complete"
        xp={completion?.xp_earned ?? state.xp}
        streak={completion?.streak_count ?? null}
        correct={state.results.filter((r) => r.correct).length}
        total={state.results.length}
        note={completionFailed ? "Progress could not be saved. Check your connection and finish again." : null}
        reflection={reflection}
      />
    );
  }
  if (state.phase === "out_of_hearts") {
    return (
      <EndScreen
        title="Out of hearts"
        xp={state.xp}
        streak={null}
        correct={state.results.filter((r) => r.correct).length}
        total={state.results.length}
        note="Practice a few review items to refill your hearts."
        practice
        reflection={null}
      />
    );
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex h-14 items-center gap-3 px-4">
        <Link href="/" aria-label="Close lesson" className="flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground">
          <X aria-hidden />
        </Link>
        <Progress value={progressFraction(state) * 100} aria-label="Lesson progress" className="h-4 flex-1" />
        <span aria-label="Hearts" className="flex items-center gap-1 font-extrabold text-danger">
          <Heart aria-hidden className="h-5 w-5 fill-current" />
          {state.hearts}
        </span>
      </header>

      <main className="flex-1 overflow-y-auto px-4 pb-40 pt-2">
        {state.phase === "vignette" && (
          <VignettePlayer beats={lesson.vignette} revealed={state.beatIndex} vocab={lesson.target_vocab} />
        )}
        {(state.phase === "exercise" || state.phase === "feedback") && current && (
          <ExerciseView key={current.id} exercise={current.exercise} disabled={state.phase === "feedback"} onResponse={onResponse} />
        )}
      </main>

      {/* From md up the column is a framed card that ends 2rem above the
          viewport (app/layout.tsx), so the footer ends there too (plan 009). */}
      <footer className="fixed inset-x-0 bottom-0 z-20 mx-auto w-full max-w-md md:bottom-8 md:overflow-hidden md:rounded-b-3xl">
        {state.phase === "feedback" && current && state.lastResult && (
          <div
            role="status"
            data-result={state.lastResult.correct ? "correct" : "wrong"}
            className={cn(
              "animate-in slide-in-from-bottom-4 fade-in duration-300 rounded-t-3xl px-5 pt-5",
              state.lastResult.correct ? "bg-success/15 text-success-foreground" : "bg-danger/15 text-danger-foreground",
            )}
          >
            {state.lastResult.correct ? (
              <p className="text-lg font-extrabold">Tama! +{current.exercise.xp} XP</p>
            ) : (
              <>
                <p className="text-lg font-extrabold">Not quite</p>
                <p className="mt-1 text-sm">
                  Correct answer: <span className="font-bold">{correctAnswerText(current.exercise)}</span>
                </p>
                {current.exercise.type === "comprehension_mc" && current.exercise.explanation && (
                  <p className="mt-1 text-sm text-muted-foreground">{current.exercise.explanation}</p>
                )}
              </>
            )}
            <div className="py-4">
              <BigButton onClick={() => dispatch({ type: "CONTINUE" })} tone={state.lastResult.correct ? "success" : "danger"}>
                Continue
              </BigButton>
            </div>
          </div>
        )}
        {state.phase === "vignette" && (
          <div className="bg-background/95 px-5 py-4 backdrop-blur">
            <BigButton onClick={() => dispatch({ type: "NEXT_BEAT" })}>Continue</BigButton>
          </div>
        )}
        {state.phase === "exercise" && (
          <div className="bg-background/95 px-5 py-4 backdrop-blur">
            <BigButton onClick={check} disabled={!canCheck}>
              Check
            </BigButton>
          </div>
        )}
      </footer>
    </div>
  );
}

function BigButton({
  children,
  onClick,
  disabled = false,
  tone = "primary",
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  tone?: "primary" | "success" | "danger";
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "h-13 w-full rounded-2xl text-base font-extrabold uppercase tracking-wide transition-transform",
        "active:translate-y-1 active:shadow-none disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none",
        "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/50",
        tone === "primary" && "bg-primary text-primary-foreground shadow-[0_4px_0_0_var(--primary-lip)]",
        tone === "success" && "bg-success text-white shadow-[0_4px_0_0_var(--success-lip)]",
        tone === "danger" && "bg-danger text-white shadow-[0_4px_0_0_var(--danger-lip)]",
      )}
    >
      {children}
    </button>
  );
}

function EndScreen({
  title,
  xp,
  streak,
  correct,
  total,
  note,
  practice = false,
  reflection,
}: {
  title: string;
  xp: number;
  streak: number | null;
  correct: number;
  total: number;
  note: string | null;
  practice?: boolean;
  reflection: ReflectionOut | null;
}) {
  // Both end screens (complete and out of hearts) open at the top.
  useEffect(() => {
    scrollWindowToTop();
  }, []);

  return (
    <div className="flex min-h-dvh flex-col gap-6 px-5 pb-10 pt-10">
      <div className="flex flex-col items-center gap-3 text-center">
        <h1 className="text-3xl font-extrabold">{title}</h1>
        <p className="text-5xl font-extrabold text-accent-foreground">{xp} XP</p>
        <p className="text-muted-foreground">
          {correct} of {total} correct
        </p>
        {streak !== null && (
          <p className="flex items-center gap-1 font-bold text-accent-foreground">
            <Flame aria-hidden className="h-5 w-5" />
            {streak} day streak
          </p>
        )}
        {note && <p className="text-sm text-danger-foreground">{note}</p>}
      </div>

      {reflection && <ReflectionCard data={reflection} />}

      <Link
        href={practice ? "/practice" : "/"}
        className="flex h-13 w-full items-center justify-center rounded-2xl bg-primary text-base font-extrabold uppercase tracking-wide text-primary-foreground shadow-[0_4px_0_0_var(--primary-lip)] active:translate-y-1 active:shadow-none"
      >
        {practice ? "Practice to refill" : "Back to the path"}
      </Link>
    </div>
  );
}

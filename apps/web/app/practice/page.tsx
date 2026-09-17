"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart, X } from "lucide-react";
import { ExerciseView } from "@/components/runner/ExerciseView";
import { getApiClient } from "@/lib/api";
import { correctAnswerText, isEmptyResponse, type ExerciseResponse } from "@/lib/runner/grade";
import { cn } from "@/lib/utils";
import type { ReviewAnswerOut } from "@/lib/types.generated";

/**
 * Practice session over due review items (SPEC.md 6.6). Every tenth answer
 * refills hearts server-side, which is the practice-to-refill flow. Grading
 * happens on the server here because review answers reschedule the item;
 * the round trip is acceptable outside the lesson runner.
 */
export default function PracticePage() {
  const api = getApiClient();
  const queryClient = useQueryClient();
  const due = useQuery({ queryKey: ["review", "due"], queryFn: () => api.getReviewDue() });
  const [index, setIndex] = useState(0);
  const [response, setResponse] = useState<ExerciseResponse | null>(null);
  const [result, setResult] = useState<ReviewAnswerOut | null>(null);
  const [busy, setBusy] = useState(false);
  const startedAt = useRef(Date.now());

  useEffect(() => {
    startedAt.current = Date.now();
    setResponse(null);
    setResult(null);
  }, [index]);

  const items = due.data?.items ?? [];
  const item = items[index];

  if (due.isPending) return <p className="p-6 text-center text-muted-foreground">Loading review items</p>;
  if (!item) {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-6 text-center">
        <h1 className="text-2xl font-extrabold">{items.length === 0 ? "Nothing due right now" : "Practice done"}</h1>
        <p className="text-muted-foreground">Come back later, or replay a lesson from the path.</p>
        <Link href="/" className="mt-2 flex h-13 w-full items-center justify-center rounded-2xl bg-primary font-extrabold uppercase text-primary-foreground">
          Back to the path
        </Link>
      </div>
    );
  }

  const submit = async () => {
    if (!response || isEmptyResponse(response) || busy) return;
    setBusy(true);
    try {
      const out = await api.postReviewAnswer({
        exercise_id: item.exercise.id,
        response,
        duration_ms: Math.max(0, Date.now() - startedAt.current),
      });
      setResult(out);
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex h-14 items-center gap-3 px-4">
        <Link href="/" aria-label="Close practice" className="flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground">
          <X aria-hidden />
        </Link>
        <p className="flex-1 text-center text-sm font-bold text-muted-foreground">
          Review {index + 1} of {items.length}
        </p>
        <span aria-label="Hearts" className="flex items-center gap-1 font-extrabold text-danger">
          <Heart aria-hidden className="h-5 w-5 fill-current" />
          {result?.hearts ?? "–"}
        </span>
      </header>

      <main className="flex-1 px-4 pb-40 pt-2">
        <ExerciseView key={item.exercise.id} exercise={item.exercise.exercise} disabled={result !== null} onResponse={setResponse} />
      </main>

      <footer className="fixed inset-x-0 bottom-0 z-20 mx-auto w-full max-w-md">
        {result ? (
          <div
            role="status"
            data-result={result.correct ? "correct" : "wrong"}
            className={cn("rounded-t-3xl px-5 pt-5", result.correct ? "bg-success/15" : "bg-danger/15")}
          >
            <p className="text-lg font-extrabold">{result.correct ? "Tama!" : "Not quite"}</p>
            {!result.correct && (
              <p className="mt-1 text-sm">
                Correct answer: <span className="font-bold">{correctAnswerText(item.exercise.exercise)}</span>
              </p>
            )}
            <div className="py-4">
              <button
                type="button"
                onClick={() => setIndex((i) => i + 1)}
                className="h-13 w-full rounded-2xl bg-primary font-extrabold uppercase tracking-wide text-primary-foreground shadow-[0_4px_0_0_var(--primary-lip)] active:translate-y-1 active:shadow-none"
              >
                Continue
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-background/95 px-5 py-4 backdrop-blur">
            <button
              type="button"
              onClick={submit}
              disabled={!response || isEmptyResponse(response) || busy}
              className="h-13 w-full rounded-2xl bg-primary font-extrabold uppercase tracking-wide text-primary-foreground shadow-[0_4px_0_0_var(--primary-lip)] active:translate-y-1 active:shadow-none disabled:opacity-40 disabled:shadow-none"
            >
              Check
            </button>
          </div>
        )}
      </footer>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Exercise } from "@/lib/types.generated";
import type { ExerciseResponse } from "@/lib/runner/grade";
import { TileBank } from "./TileBank";
import { useShortcuts } from "./useShortcuts";

const INSTRUCTION: Record<Exercise["type"], string> = {
  sentence_assembly: "Build the Tagalog sentence",
  translate_line: "Translate this line",
  listen_tap: "Tap what you hear",
  comprehension_mc: "About the passage",
};

/**
 * Start a screen at the top of the window. Called from mount effects only
 * (each exercise is keyed, so it mounts per exercise), never on the way back
 * to the vignette, where it would undo the beat's scrollIntoView. "auto"
 * rather than "instant": no CSS scroll-behavior is set, so auto is already
 * instant, and older WebKit only knows auto and smooth. jsdom has no scroll.
 */
export function scrollWindowToTop() {
  if (typeof window === "undefined" || typeof window.scrollTo !== "function") return;
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
}

export function ExerciseView({
  exercise,
  disabled,
  onResponse,
}: {
  exercise: Exercise;
  disabled: boolean;
  onResponse: (response: ExerciseResponse) => void;
}) {
  useEffect(() => {
    scrollWindowToTop();
  }, []);

  return (
    <div className="flex flex-col gap-5 md:my-auto md:gap-7">
      <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">{INSTRUCTION[exercise.type]}</p>
      <Body exercise={exercise} disabled={disabled} onResponse={onResponse} />
    </div>
  );
}

function Body({
  exercise,
  disabled,
  onResponse,
}: {
  exercise: Exercise;
  disabled: boolean;
  onResponse: (response: ExerciseResponse) => void;
}) {
  switch (exercise.type) {
    case "sentence_assembly":
      return (
        <>
          <Prompt text={exercise.prompt_en} />
          <Tokens key={exercise.key} bank={exercise.bank} disabled={disabled} onResponse={onResponse} />
        </>
      );
    case "translate_line":
      return (
        <>
          <Prompt text={exercise.prompt} lang={exercise.direction === "tl_to_en" ? "tl" : "en"} />
          <Tokens key={exercise.key} bank={exercise.bank} disabled={disabled} onResponse={onResponse} />
        </>
      );
    case "listen_tap":
      return (
        <>
          <AudioButton url={exercise.audio_url ?? null} />
          <Tokens key={exercise.key} bank={exercise.bank} disabled={disabled} onResponse={onResponse} />
        </>
      );
    case "comprehension_mc":
      return (
        <>
          <Prompt text={exercise.question} />
          <Options key={exercise.key} options={exercise.options} disabled={disabled} onResponse={onResponse} />
        </>
      );
  }
}

function Prompt({ text, lang }: { text: string; lang?: "tl" | "en" }) {
  return (
    <p lang={lang} className="text-xl font-bold leading-snug lg:text-2xl">
      {text}
    </p>
  );
}

function AudioButton({ url }: { url: string | null }) {
  // Audio is pre-rendered at seed time (D12). Until plan 002 renders it,
  // audio_url is null and the control is shown disabled.
  return (
    <button
      type="button"
      aria-label="Play audio"
      disabled={!url}
      onClick={() => url && new Audio(url).play()}
      className={cn(
        "flex h-20 w-20 items-center justify-center self-center rounded-3xl bg-primary text-primary-foreground md:h-24 md:w-24",
        "shadow-[0_5px_0_0_var(--primary-lip)] active:translate-y-[5px] active:shadow-none disabled:opacity-40",
      )}
    >
      <Volume2 aria-hidden className="h-9 w-9" />
    </button>
  );
}

function Tokens({
  bank,
  disabled,
  onResponse,
}: {
  bank: readonly string[];
  disabled: boolean;
  onResponse: (response: ExerciseResponse) => void;
}) {
  const [picked, setPicked] = useState<number[]>([]);
  const change = (next: number[]) => {
    setPicked(next);
    onResponse({ tokens: next.map((i) => bank[i]) });
  };
  // Digit N picks the Nth bank tile by position (placeholders keep the slots,
  // so numbers do not shift); Backspace removes the last picked tile.
  useShortcuts({
    onPick: (i) => {
      if (disabled || i >= bank.length || picked.includes(i)) return;
      change([...picked, i]);
    },
    onUnpick: () => {
      if (disabled || picked.length === 0) return;
      change(picked.slice(0, -1));
    },
  });
  return <TileBank bank={bank} picked={picked} onChange={change} disabled={disabled} />;
}

function Options({
  options,
  disabled,
  onResponse,
}: {
  options: readonly string[];
  disabled: boolean;
  onResponse: (response: ExerciseResponse) => void;
}) {
  const [chosen, setChosen] = useState<number | null>(null);
  const items = useMemo(() => options.map((label, index) => ({ label, index })), [options]);
  const choose = (index: number) => {
    setChosen(index);
    onResponse({ optionIndex: index });
  };
  // Digit N chooses option N; focus stays where it is.
  useShortcuts({
    onPick: (i) => {
      if (disabled || i >= options.length) return;
      choose(i);
    },
  });
  return (
    <div role="radiogroup" aria-label="Options" className="flex flex-col gap-3">
      {items.map(({ label, index }) => (
        <button
          key={index}
          type="button"
          role="radio"
          aria-checked={chosen === index}
          disabled={disabled}
          onClick={() => choose(index)}
          className={cn(
            "min-h-12 rounded-xl border-2 border-border bg-card px-4 py-3 text-left text-base font-semibold md:min-h-14 lg:text-lg",
            "shadow-[0_3px_0_0_var(--border)] active:translate-y-[3px] active:shadow-none",
            "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/50",
            chosen === index && "border-primary bg-primary/10 shadow-[0_3px_0_0_var(--primary-lip)]",
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

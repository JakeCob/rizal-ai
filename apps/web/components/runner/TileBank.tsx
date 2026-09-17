"use client";

import { cn } from "@/lib/utils";

/**
 * Word tiles. Tap a bank tile to append it to the answer, tap an answer tile
 * to return it. Tiles are tracked by bank position so duplicate words work.
 * Tap targets are at least 44px tall.
 */
export function TileBank({
  bank,
  picked,
  onChange,
  disabled = false,
}: {
  bank: readonly string[];
  /** Indexes into bank, in answer order. */
  picked: number[];
  onChange: (picked: number[]) => void;
  disabled?: boolean;
}) {
  const pick = (i: number) => !disabled && onChange([...picked, i]);
  const unpick = (pos: number) => !disabled && onChange(picked.filter((_, p) => p !== pos));

  return (
    <div className="flex flex-col gap-4">
      <div
        role="group"
        aria-label="Your answer"
        className="flex min-h-[3.5rem] flex-wrap gap-2 border-b-2 border-dashed border-border pb-2"
      >
        {picked.map((bankIndex, pos) => (
          <Tile key={`${bankIndex}-${pos}`} label={bank[bankIndex]} onClick={() => unpick(pos)} disabled={disabled} />
        ))}
      </div>
      <div role="group" aria-label="Word bank" className="flex flex-wrap gap-2">
        {bank.map((word, i) => {
          const used = picked.includes(i);
          return used ? (
            <span key={i} aria-hidden className="h-11 rounded-xl border-2 border-transparent bg-muted px-3 opacity-40">
              <span className="invisible">{word}</span>
            </span>
          ) : (
            <Tile key={i} label={word} onClick={() => pick(i)} disabled={disabled} />
          );
        })}
      </div>
    </div>
  );
}

function Tile({ label, onClick, disabled }: { label: string; onClick: () => void; disabled: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "h-11 rounded-xl border-2 border-border bg-card px-3 text-base font-semibold",
        "shadow-[0_3px_0_0_var(--border)] active:translate-y-[3px] active:shadow-none",
        "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/50",
        disabled && "opacity-70",
      )}
    >
      {label}
    </button>
  );
}

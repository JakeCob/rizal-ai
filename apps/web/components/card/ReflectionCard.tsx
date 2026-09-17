"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import type { LayerOut, QuotedSpan, ReflectionOut } from "@/lib/types.generated";

/**
 * The "In Rizal's voice" card (DECISIONS.md D01, D02, D03). Three labeled
 * passage layers show the originals verbatim. The generated reflection sits
 * in its own block, clearly marked as generated, and only the quoted spans
 * inside it carry Rizal's byline, each linked to the passage it came from.
 */
export function ReflectionCard({ data }: { data: ReflectionOut }) {
  return (
    <div className="flex flex-col gap-4">
      <section aria-label="The passage" className="rounded-2xl border-2 border-border bg-card p-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">The passage</h2>
        <div className="mt-2 flex flex-col gap-2">
          {data.layers.map((layer) => (
            <Layer key={layer.language} layer={layer} />
          ))}
        </div>
      </section>

      {data.status === "published" && data.reflection ? (
        <Reflection tl={data.reflection.tl} en={data.reflection.en} spans={data.reflection.quoted_spans} />
      ) : (
        <p className="px-1 text-sm text-muted-foreground">Rizal&apos;s reflection is not available for this lesson yet.</p>
      )}
    </div>
  );
}

function Layer({ layer }: { layer: LayerOut }) {
  const serif = layer.language !== "en";
  return (
    <Collapsible>
      <CollapsibleTrigger
        render={
          <button
            type="button"
            className="flex min-h-11 w-full items-center justify-between gap-2 rounded-xl px-3 py-2 text-left text-sm font-bold hover:bg-muted"
          />
        }
      >
        <span>{layer.label}</span>
        <ChevronDown aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="flex flex-col gap-3 px-3 pb-3 pt-1">
          {layer.passages.map((p) => (
            <p
              key={p.id}
              lang={layer.language}
              className={cn("text-[15px] leading-relaxed", serif && "font-serif")}
              data-passage-id={p.id}
            >
              {p.text}
            </p>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

function Reflection({ tl, en, spans }: { tl: string; en: string; spans: QuotedSpan[] }) {
  const [lang, setLang] = useState<"tl" | "en">("tl");
  const text = lang === "tl" ? tl : en;
  return (
    <section aria-label="In Rizal's voice" className="rounded-2xl border-2 border-primary/30 bg-primary/5 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-extrabold">In Rizal&apos;s voice</h2>
          <p className="text-xs text-muted-foreground">
            Generated from the cited passages. Only the highlighted words are Rizal&apos;s own.
          </p>
        </div>
        <div role="tablist" aria-label="Reflection language" className="flex shrink-0 rounded-xl bg-muted p-1">
          {(["tl", "en"] as const).map((code) => (
            <button
              key={code}
              type="button"
              role="tab"
              aria-selected={lang === code}
              onClick={() => setLang(code)}
              className={cn(
                "h-9 rounded-lg px-3 text-xs font-bold uppercase tracking-wide",
                lang === code ? "bg-card shadow-sm" : "text-muted-foreground",
              )}
            >
              {code === "tl" ? "Tagalog" : "English"}
            </button>
          ))}
        </div>
      </div>
      <p lang={lang} className="mt-3 text-[17px] leading-relaxed">
        {highlight(text, spans)}
      </p>
    </section>
  );
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Wrap every occurrence of a quoted span in a mark carrying its passage id. */
function highlight(text: string, spans: QuotedSpan[]): React.ReactNode[] {
  if (spans.length === 0) return [text];
  const pattern = new RegExp(`(${spans.map((s) => escapeRegExp(s.text)).join("|")})`, "g");
  const byText = new Map(spans.map((s) => [s.text, s.passage_id]));
  return text.split(pattern).map((part, i) => {
    const passageId = byText.get(part);
    return passageId ? (
      <mark
        key={i}
        role="mark"
        data-passage-id={passageId}
        className="rounded bg-accent/60 px-0.5 font-serif italic text-accent-foreground"
      >
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    );
  });
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { Flame, Heart, Star } from "lucide-react";
import { NextLessonCard } from "@/components/tree/NextLessonCard";
import { ProgressPanel } from "@/components/tree/ProgressPanel";
import { SkillTree } from "@/components/tree/SkillTree";
import { UnitNav } from "@/components/tree/UnitNav";
import { getApiClient } from "@/lib/api";
import { nextLesson } from "@/lib/tree/summary";

/**
 * The path. Below 768px it is the phone column. From 768px (D38) a units nav
 * sits beside the path, and from 1024px a progress column joins them; both
 * read the same tree and me queries, so the extra columns cost no request.
 * data-layout="wide" asks the layout frame for the wider width.
 */
export default function TreePage() {
  const api = getApiClient();
  const tree = useQuery({ queryKey: ["tree"], queryFn: () => api.getTree() });
  const me = useQuery({ queryKey: ["me"], queryFn: () => api.getMe() });

  return (
    <div
      data-layout="wide"
      className="flex flex-col px-4 md:grid md:grid-cols-[13rem_minmax(0,1fr)] md:gap-x-6 md:px-6 lg:grid-cols-[14rem_minmax(0,1fr)_18rem] lg:gap-x-8 lg:px-8"
    >
      <header className="flex h-14 items-center justify-between md:col-span-full">
        <h1 className="text-xl font-extrabold tracking-tight">RizalAI</h1>
        <div className="flex items-center gap-4 text-sm font-extrabold lg:hidden" aria-live="polite">
          <span className="flex items-center gap-1 text-accent-foreground" aria-label="Streak">
            <Flame aria-hidden className="h-5 w-5" />
            {me.data?.streak_count ?? "–"}
          </span>
          <span className="flex items-center gap-1 text-accent-foreground" aria-label="Total XP">
            <Star aria-hidden className="h-5 w-5" />
            {me.data?.total_xp ?? "–"}
          </span>
          <span className="flex items-center gap-1 text-danger" aria-label="Hearts">
            <Heart aria-hidden className="h-5 w-5 fill-current" />
            {me.data?.hearts ?? "–"}
          </span>
        </div>
      </header>

      <div className="hidden md:sticky md:top-8 md:block md:self-start">{tree.data && <UnitNav units={tree.data.units} />}</div>

      <main>
        {tree.isPending && <TreeSkeleton />}
        {tree.isError && (
          <p role="alert" className="mt-8 text-center text-danger">
            Could not load the path. Check that the API is running.
          </p>
        )}
        {tree.data && <SkillTree tree={tree.data} />}
      </main>

      <aside aria-label="Your progress" className="hidden lg:sticky lg:top-8 lg:flex lg:flex-col lg:gap-4 lg:self-start">
        <ProgressPanel user={me.data} />
        {tree.data && <NextLessonCard next={nextLesson(tree.data)} />}
      </aside>
    </div>
  );
}

function TreeSkeleton() {
  return (
    <div className="mt-4 flex flex-col items-center gap-6" aria-busy="true" aria-label="Loading path">
      <div className="-mx-4 h-16 w-[calc(100%+2rem)] animate-pulse rounded-none bg-muted" />
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="h-[72px] w-[72px] animate-pulse rounded-3xl bg-muted" />
      ))}
    </div>
  );
}

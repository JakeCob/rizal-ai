"use client";

import { useQuery } from "@tanstack/react-query";
import { Flame, Heart, Star } from "lucide-react";
import { SkillTree } from "@/components/tree/SkillTree";
import { getApiClient } from "@/lib/api";

export default function TreePage() {
  const api = getApiClient();
  const tree = useQuery({ queryKey: ["tree"], queryFn: () => api.getTree() });
  const me = useQuery({ queryKey: ["me"], queryFn: () => api.getMe() });

  return (
    <div className="flex flex-col px-4">
      <header className="flex h-14 items-center justify-between">
        <h1 className="text-xl font-extrabold tracking-tight">RizalAI</h1>
        <div className="flex items-center gap-4 text-sm font-extrabold" aria-live="polite">
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

      {tree.isPending && <TreeSkeleton />}
      {tree.isError && (
        <p role="alert" className="mt-8 text-center text-danger">
          Could not load the path. Check that the API is running.
        </p>
      )}
      {tree.data && <SkillTree tree={tree.data} />}
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

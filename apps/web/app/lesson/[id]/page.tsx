"use client";

import { useCallback } from "react";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Runner } from "@/components/runner/Runner";
import { getApiClient } from "@/lib/api";

export default function LessonPage() {
  const { id } = useParams<{ id: string }>();
  const api = getApiClient();
  const queryClient = useQueryClient();
  const lesson = useQuery({ queryKey: ["lesson", id], queryFn: () => api.getLesson(id) });
  const me = useQuery({ queryKey: ["me"], queryFn: () => api.getMe() });
  const onCompleted = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ["me"] });
    void queryClient.invalidateQueries({ queryKey: ["tree"] });
  }, [queryClient]);

  if (lesson.isError) {
    return (
      <p role="alert" className="p-6 text-center text-danger">
        Could not load this lesson.
      </p>
    );
  }
  if (!lesson.data || !me.data) {
    return (
      <div className="flex flex-col gap-4 p-4" aria-busy="true" aria-label="Loading lesson">
        <div className="h-4 w-full animate-pulse rounded-full bg-muted" />
        <div className="mt-6 h-6 w-3/4 animate-pulse rounded bg-muted" />
        <div className="h-6 w-1/2 animate-pulse rounded bg-muted" />
      </div>
    );
  }
  return <Runner lesson={lesson.data} hearts={me.data.hearts} api={api} onCompleted={onCompleted} />;
}

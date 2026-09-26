import { Flame, Heart, Star } from "lucide-react";
import type { UserOut } from "@/lib/types.generated";

/**
 * The learner's stats in the desktop progress column (plan 010). A definition
 * list, not aria-labels: the header keeps the Streak, Total XP and Hearts
 * labels, and duplicating them would make those names ambiguous. From lg the
 * header's live stats are hidden, so this list is the polite live region.
 */
export function ProgressPanel({ user }: { user: UserOut | undefined }) {
  const streak = user ? `${user.streak_count} ${user.streak_count === 1 ? "day" : "days"}` : "–";
  return (
    <section className="rounded-2xl border-2 border-border bg-card p-4">
      <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Your progress</h2>
      <dl aria-live="polite" className="mt-3 grid grid-cols-[auto_1fr] items-center gap-x-3 gap-y-3">
        <Stat icon={<Flame aria-hidden className="h-5 w-5 text-gold" />} term="Streak" value={streak} />
        <Stat icon={<Star aria-hidden className="h-5 w-5 text-gold" />} term="Total XP" value={user?.total_xp ?? "–"} />
        <Stat icon={<Heart aria-hidden className="h-5 w-5 fill-current text-danger" />} term="Hearts" value={user?.hearts ?? "–"} />
      </dl>
    </section>
  );
}

function Stat({ icon, term, value }: { icon: React.ReactNode; term: string; value: string | number }) {
  return (
    <>
      <dt className="flex items-center gap-2 text-sm font-bold text-muted-foreground">
        {icon}
        {term}
      </dt>
      <dd className="text-right text-lg font-extrabold">{value}</dd>
    </>
  );
}

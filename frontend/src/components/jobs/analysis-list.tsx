"use client";

import type { Job, Recommendation } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ScoreBadge } from "./match-badges";

type GroupKey = Recommendation | "pending";
const ORDER: GroupKey[] = ["auto_apply_eligible", "review", "pending", "skip", "reject"];
const LABEL: Record<GroupKey, string> = {
  auto_apply_eligible: "Auto-apply eligible",
  review: "Review queue",
  pending: "Not analysed",
  skip: "Skipped",
  reject: "Rejected",
};

export function AnalysisList({ jobs, selectedId, onSelect }: { jobs: Job[]; selectedId: number | null; onSelect: (id: number) => void }) {
  const groups = ORDER.map((key) => ({
    key,
    items: jobs
      .filter((j) => (j.match_details?.recommendation ?? "pending") === key)
      .sort((a, b) => (b.match_score ?? -1) - (a.match_score ?? -1)),
  })).filter((g) => g.items.length);

  return (
    <div className="space-y-5">
      {groups.map((g) => (
        <div key={g.key} className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{LABEL[g.key]} ({g.items.length})</p>
          {g.items.map((j) => (
            <button
              key={j.id}
              onClick={() => onSelect(j.id)}
              className={cn(
                "w-full cursor-pointer rounded-lg border bg-card p-3 text-left transition-colors hover:bg-muted",
                j.id === selectedId && "border-primary ring-1 ring-primary",
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{j.title}</p>
                  <p className="truncate text-xs text-muted-foreground">{j.company ?? "—"} · {j.location ?? "—"}</p>
                </div>
                <ScoreBadge score={j.match_score} />
              </div>
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

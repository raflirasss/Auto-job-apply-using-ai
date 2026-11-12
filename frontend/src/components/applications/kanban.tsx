"use client";

import type { ApplicationStatus, Job } from "@/lib/types";
import { cn } from "@/lib/utils";
import { STATUS_LABELS } from "@/components/jobs/match-badges";
import { ScoreBadge } from "@/components/jobs/match-badges";

export const COLUMNS: { key: string; label: string; statuses: ApplicationStatus[] }[] = [
  { key: "new", label: "New", statuses: ["discovered", "analyzed"] },
  { key: "qualified", label: "Qualified", statuses: ["qualified", "ready_to_apply"] },
  { key: "action", label: "Pending action", statuses: ["pending_action"] },
  { key: "applied", label: "Applied", statuses: ["applied"] },
  { key: "progress", label: "Assessment / Interview", statuses: ["assessment", "interview"] },
  { key: "closed", label: "Closed", statuses: ["accepted", "rejected", "failed"] },
];

export function Kanban({ jobs, selectedId, onSelect }: { jobs: Job[]; selectedId: number | null; onSelect: (id: number) => void }) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {COLUMNS.map((col) => {
        const items = jobs.filter((j) => j.application && col.statuses.includes(j.application.status));
        return (
          <div key={col.key} className="w-64 shrink-0 space-y-2 rounded-xl bg-muted/50 p-2">
            <p className="px-1 text-xs font-medium text-muted-foreground">{col.label} ({items.length})</p>
            {items.map((j) => (
              <button key={j.id} onClick={() => onSelect(j.id)}
                className={cn("w-full cursor-pointer rounded-lg border bg-card p-2.5 text-left text-sm shadow-xs transition-colors hover:bg-muted",
                  j.id === selectedId && "border-primary ring-1 ring-primary")}>
                <p className="truncate font-medium">{j.title}</p>
                <p className="truncate text-xs text-muted-foreground">{j.company ?? "—"}</p>
                <div className="mt-1.5 flex items-center justify-between gap-1">
                  <span className="text-xs text-muted-foreground">{STATUS_LABELS[j.application!.status]}</span>
                  <ScoreBadge score={j.match_score} />
                </div>
              </button>
            ))}
          </div>
        );
      })}
    </div>
  );
}

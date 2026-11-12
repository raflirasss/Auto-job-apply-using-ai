"use client";

import type { Job } from "@/lib/types";
import { cn, formatDateTime, formatIDR } from "@/lib/utils";
import { ScoreBadge, StatusBadge } from "@/components/jobs/match-badges";

export function ApplicationsTable({ jobs, selectedId, onSelect }: { jobs: Job[]; selectedId: number | null; onSelect: (id: number) => void }) {
  return (
    <div className="overflow-x-auto rounded-xl border bg-card">
      <table className="w-full text-sm">
        <thead className="border-b text-left text-xs text-muted-foreground">
          <tr>
            {["Job", "Company", "Location", "Salary / month", "Score", "Status", "Discovered", "Applied"].map((h) => (
              <th key={h} className="whitespace-nowrap px-3 py-2 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y">
          {jobs.map((j) => (
            <tr key={j.id} onClick={() => onSelect(j.id)}
              className={cn("cursor-pointer transition-colors hover:bg-muted/60", j.id === selectedId && "bg-accent/60")}>
              <td className="max-w-56 truncate px-3 py-2 font-medium">{j.title}</td>
              <td className="max-w-40 truncate px-3 py-2">{j.company ?? "—"}</td>
              <td className="max-w-36 truncate px-3 py-2">{j.location ?? "—"}</td>
              <td className="whitespace-nowrap px-3 py-2">{j.salary_disclosed ? formatIDR(j.salary_min_monthly ?? j.salary_max_monthly) : "Undisclosed"}</td>
              <td className="px-3 py-2"><ScoreBadge score={j.match_score} /></td>
              <td className="px-3 py-2">{j.application && <StatusBadge status={j.application.status} />}</td>
              <td className="whitespace-nowrap px-3 py-2 text-muted-foreground">{formatDateTime(j.discovered_at)}</td>
              <td className="whitespace-nowrap px-3 py-2 text-muted-foreground">{j.application?.applied_at ? formatDateTime(j.application.applied_at) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

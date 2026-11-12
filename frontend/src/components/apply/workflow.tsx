"use client";

import { useCallback, useState } from "react";
import type { Job } from "@/lib/types";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { MatchBreakdown } from "@/components/jobs/match-breakdown";
import { AIExplanation } from "@/components/jobs/ai-explanation";
import { DocumentsPanel } from "./documents-panel";
import { ApplyPanel } from "./apply-panel";
import { StatusPanel } from "./status-panel";

const TABS = [
  { id: "analysis", label: "Analysis" },
  { id: "documents", label: "Documents" },
  { id: "apply", label: "Apply" },
  { id: "status", label: "Status" },
] as const;
type Tab = (typeof TABS)[number]["id"];

/** Analysis -> documents -> apply -> status for one job. */
export function JobWorkflow({ job, onUpdated, initialTab = "analysis" }: { job: Job; onUpdated: (j: Job) => void; initialTab?: Tab }) {
  const [tab, setTab] = useState<Tab>(initialTab);
  const refresh = useCallback(() => {
    api.job(job.id).then((r) => onUpdated(r.job)).catch(() => undefined);
  }, [job.id, onUpdated]);

  return (
    <div className="space-y-4">
      <div role="tablist" className="inline-flex rounded-lg border bg-muted p-1">
        {TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)}
            className={cn("cursor-pointer rounded-md px-3 py-1 text-sm", tab === t.id ? "bg-card font-medium shadow-sm" : "text-muted-foreground")}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === "analysis" && (job.match_details ? (
        <div className="space-y-6">
          <MatchBreakdown result={job.match_details} />
          <div className="border-t pt-4"><AIExplanation job={job} onUpdated={onUpdated} /></div>
        </div>
      ) : <p className="text-sm text-muted-foreground">Not analysed yet.</p>)}
      {tab === "documents" && <DocumentsPanel job={job} onGenerated={refresh} />}
      {tab === "apply" && <ApplyPanel job={job} onChanged={refresh} />}
      {tab === "status" && <StatusPanel key={job.application?.status} job={job} onUpdated={onUpdated} />}
    </div>
  );
}

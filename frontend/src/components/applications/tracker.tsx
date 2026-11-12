"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Columns3, KanbanSquare, Rows3, X } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import type { ApplicationStatus, Job } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, EmptyState, LoadingBlock, PageHeader } from "@/components/ui/feedback";
import { Input, Select } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { STATUS_LABELS } from "@/components/jobs/match-badges";
import { JobWorkflow } from "@/components/apply/workflow";
import { ApplicationsTable } from "./table";
import { Kanban } from "./kanban";

export function Tracker() {
  const jobs = useAsync(() => api.jobs(500));
  const router = useRouter();
  const params = useSearchParams();
  const selectedId = Number(params.get("job")) || null;
  const [view, setView] = useState<"table" | "kanban">("table");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"" | ApplicationStatus>("");

  const { setData } = jobs;
  const replaceJob = useCallback(
    (u: Job) => setData((d) => (d ? { ...d, jobs: d.jobs.map((j) => (j.id === u.id ? u : j)) } : d)),
    [setData],
  );
  const select = (id: number | null) => router.replace(id ? `/applications?job=${id}` : "/applications", { scroll: false });

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (jobs.data?.jobs ?? []).filter((j) =>
      (!status || j.application?.status === status) &&
      (!q || [j.title, j.company, j.location].some((v) => v?.toLowerCase().includes(q))));
  }, [jobs.data, query, status]);
  const selected = jobs.data?.jobs.find((j) => j.id === selectedId) ?? null;

  return (
    <>
      <PageHeader title="Application Tracker" description="Every imported job and its application state."
        actions={<div className="inline-flex rounded-lg border bg-muted p-1">
          {([["table", Rows3, "Table"], ["kanban", KanbanSquare, "Kanban"]] as const).map(([v, Icon, label]) => (
            <button key={v} onClick={() => setView(v)} aria-pressed={view === v}
              className={cn("flex cursor-pointer items-center gap-1.5 rounded-md px-3 py-1 text-sm", view === v ? "bg-card font-medium shadow-sm" : "text-muted-foreground")}>
              <Icon className="size-4" /> {label}
            </button>
          ))}
        </div>} />
      <div className="mb-4 flex flex-wrap gap-2">
        <Input className="max-w-xs" placeholder="Search title, company, location" value={query} onChange={(e) => setQuery(e.target.value)} />
        <Select className="max-w-52" value={status} onChange={(e) => setStatus(e.target.value as "" | ApplicationStatus)}>
          <option value="">All statuses</option>
          {(Object.keys(STATUS_LABELS) as ApplicationStatus[]).map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </Select>
      </div>
      {jobs.error && <Alert tone="error">{jobs.error}</Alert>}
      {jobs.loading && !jobs.data && <LoadingBlock />}
      {jobs.data && jobs.data.jobs.length === 0 && (
        <EmptyState icon={Columns3} title="No applications yet" description="Listings found by your sources appear here automatically.">
          <Button asChild variant="outline"><Link href="/jobs">Go to Job Discovery</Link></Button>
        </EmptyState>
      )}
      {jobs.data && jobs.data.jobs.length > 0 && (
        filtered.length === 0 ? <p className="text-sm text-muted-foreground">No applications match the filters.</p>
          : view === "table" ? <ApplicationsTable jobs={filtered} selectedId={selectedId} onSelect={select} />
          : <Kanban jobs={filtered} selectedId={selectedId} onSelect={select} />
      )}
      {selected && (
        <Card className="mt-6">
          <CardHeader className="flex-row items-start justify-between">
            <div>
              <CardTitle className="text-base">{selected.title}</CardTitle>
              <CardDescription>{selected.company ?? "Company not given"} Â· {selected.location ?? "Location not given"}</CardDescription>
            </div>
            <Button variant="ghost" size="icon" aria-label="Close" onClick={() => select(null)}><X /></Button>
          </CardHeader>
          <CardContent><JobWorkflow key={selected.id} job={selected} onUpdated={replaceJob} initialTab="status" /></CardContent>
        </Card>
      )}
    </>
  );
}

"use client";

import { RefreshCw } from "lucide-react";
import type { Job } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { JobWorkflow } from "@/components/apply/workflow";
import { RecommendationBadge, StatusBadge } from "./match-badges";

export function AnalysisDetail({ job, busy, onAnalyze, onUpdated }: {
  job: Job;
  busy: boolean;
  onAnalyze: () => void;
  onUpdated: (j: Job) => void;
}) {
  return (
    <Card className="lg:sticky lg:top-6">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">{job.title}</CardTitle>
            <CardDescription>{job.company ?? "Company not given"} · {job.location ?? "Location not given"}</CardDescription>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {job.match_details && <RecommendationBadge value={job.match_details.recommendation} />}
            {job.application && <StatusBadge status={job.application.status} />}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <JobWorkflow key={job.id} job={job} onUpdated={onUpdated} />
        <Button variant="outline" size="sm" disabled={busy} onClick={onAnalyze}>
          {busy ? <Spinner /> : <RefreshCw />} {job.match_details ? "Re-analyse" : "Analyse"}
        </Button>
      </CardContent>
    </Card>
  );
}

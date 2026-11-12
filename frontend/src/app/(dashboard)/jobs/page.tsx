"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { ExternalLink, Import, Search, Sparkles } from "lucide-react";
import { RecommendationBadge, ScoreBadge, StatusBadge } from "@/components/jobs/match-badges";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import { formatDateTime, formatIDR } from "@/lib/utils";
import type { Job } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, EmptyState, LoadingBlock, PageHeader } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ImportJobForm } from "@/components/jobs/import-job-form";
import { DiscoveryPanel } from "@/components/sources/discovery-panel";

function salaryText(job: Job) {
  if (!job.salary_disclosed) return "Salary not disclosed";
  if (job.salary_min_monthly !== null && job.salary_max_monthly !== null) {
    return `${formatIDR(job.salary_min_monthly)} – ${formatIDR(job.salary_max_monthly)} / month`;
  }
  return `${formatIDR(job.salary_min_monthly ?? job.salary_max_monthly)} / month`;
}

const SOURCE_LABEL: Record<string, string> = { rss: "Google Alerts", telegram: "Telegram", lever: "Lever", greenhouse: "Greenhouse", manual: "Manual" };

export default function JobsPage() {
  const jobs = useAsync(() => api.jobs());
  const [open, setOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const { reload } = jobs;
  const onDiscovered = useCallback(() => void reload(), [reload]);

  return (
    <>
      <PageHeader
        title="Job Discovery"
        description="Listings collected from Google Alerts, Telegram channels and company career boards."
        actions={<Button variant="outline" onClick={() => { setOpen((v) => !v); setNotice(null); }}><Import /> Add manually</Button>}
      />
      <DiscoveryPanel onFinished={onDiscovered} />
      {notice && <Alert tone="success" className="mb-6">{notice}</Alert>}
      {open && (
        <ImportJobForm
          onCancel={() => setOpen(false)}
          onImported={(r) => {
            setOpen(false);
            setNotice(r.duplicate ? `Already imported: "${r.job.title}". Updated the existing entry instead of creating a duplicate.` : `Imported "${r.job.title}".`);
            void jobs.reload();
          }}
        />
      )}

      {jobs.error && <Alert tone="error">{jobs.error}</Alert>}
      {jobs.loading && !jobs.data && <LoadingBlock />}
      {jobs.data?.jobs.length === 0 && (
        <EmptyState icon={Search} title="No listings yet" description="Enable a source and click 'Check sources now'. No sample or fake jobs are shown." />
      )}
      {jobs.data && jobs.data.jobs.length > 0 && (
        <div className="space-y-3">
          {jobs.data.jobs.map((job) => (
            <Card key={job.id}>
              <CardContent className="flex flex-wrap items-start justify-between gap-4 p-5">
                <div className="min-w-0 space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-semibold">{job.title}</h2>
                    <Badge variant="outline">{SOURCE_LABEL[job.source] ?? job.source}</Badge>
                    {job.apply_email && <Badge variant="default">apply by email</Badge>}
                    {job.work_arrangement && <Badge variant={job.work_arrangement === "remote" ? "warning" : "outline"}>{job.work_arrangement}</Badge>}
                    {job.employment_type && <Badge variant="outline">{job.employment_type.replace("_", " ")}</Badge>}
                    <Badge variant={job.salary_disclosed ? "success" : "warning"}>{job.salary_disclosed ? "salary disclosed" : "salary undisclosed"}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{job.company ?? "Company not given"} · {job.location ?? "Location not given"}</p>
                  <p className="text-sm">{salaryText(job)}</p>
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <ScoreBadge score={job.match_score} />
                    {job.match_details && <RecommendationBadge value={job.match_details.recommendation} />}
                    {job.application && <StatusBadge status={job.application.status} />}
                  </div>
                  <p className="text-xs text-muted-foreground">Found {formatDateTime(job.discovered_at)}{job.source_note ? ` · ${job.source_note}` : ""}</p>
                </div>
                <div className="flex flex-col gap-2">
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/analysis?job=${job.id}`}><Sparkles /> {job.match_details ? "View analysis" : "Analyse"}</Link>
                  </Button>
                  {job.application_url && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={job.application_url} target="_blank" rel="noopener noreferrer"><ExternalLink /> Open listing</a>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}

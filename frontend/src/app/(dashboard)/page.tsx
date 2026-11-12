"use client";

import Link from "next/link";
import { Activity, Briefcase, CalendarCheck, CheckCircle2, Clock, Percent, Send, UserCheck, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import { formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, EmptyState, LoadingBlock, PageHeader } from "@/components/ui/feedback";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

function Stat({ label, value, icon: Icon }: { label: string; value: string | number; icon: React.ElementType }) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
        </div>
        <div className="rounded-lg bg-accent p-2 text-accent-foreground">
          <Icon className="size-4" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function OverviewPage() {
  const overview = useAsync(() => api.overview());
  const profile = useAsync(() => api.getProfile());

  const p = profile.data?.profile;
  const critical = p?.data.missing_information.filter((m) => m.critical) ?? [];

  return (
    <>
      <PageHeader title="Overview" description="Live statistics from the application database." />

      {profile.data && !p && (
        <Alert tone="warning" title="No candidate profile yet" className="mb-6">
          Import your CV in <Link className="underline" href="/settings">Settings → Candidate profile</Link> before the agent can match jobs.
        </Alert>
      )}
      {p && !p.is_confirmed && (
        <Alert tone="warning" title="Candidate profile awaiting review" className="mb-6">
          {critical.length > 0
            ? `${critical.length} critical question(s) must be answered before the profile can be confirmed. `
            : "Review the extracted data and confirm it. "}
          <Link className="underline" href="/settings">Open profile</Link>
        </Alert>
      )}

      {overview.error && <Alert tone="error" title="Could not load statistics">{overview.error}</Alert>}
      {overview.loading && !overview.data && <LoadingBlock />}

      {overview.data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Stat label="Jobs discovered" value={overview.data.jobs_discovered} icon={Briefcase} />
            <Stat label="Qualified" value={overview.data.qualified} icon={UserCheck} />
            <Stat label="Applications submitted" value={overview.data.applications_submitted} icon={Send} />
            <Stat label="Pending" value={overview.data.pending} icon={Clock} />
            <Stat label="Interviews" value={overview.data.interviews} icon={CalendarCheck} />
            <Stat label="Rejections (employer)" value={overview.data.rejections} icon={XCircle} />
            <Stat
              label="Success rate"
              value={overview.data.success_rate === null ? "—" : `${overview.data.success_rate}%`}
              icon={Percent}
            />
            <Stat label="Profile" value={p ? (p.is_confirmed ? "Confirmed" : "Draft") : "Missing"} icon={CheckCircle2} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recent agent activity</CardTitle>
              <CardDescription>Latest events recorded by the system.</CardDescription>
            </CardHeader>
            <CardContent>
              {overview.data.recent_activity.length === 0 ? (
                <EmptyState icon={Activity} title="No activity yet" description="Events appear here as you import your CV, change settings and, from Phase 2 onward, when the agent runs." />
              ) : (
                <ul className="divide-y">
                  {overview.data.recent_activity.map((e) => (
                    <li key={e.id} className="flex items-start justify-between gap-4 py-2.5 text-sm">
                      <div className="flex items-start gap-2">
                        <Badge variant={e.level === "error" ? "destructive" : e.level === "warning" ? "warning" : "outline"}>{e.category}</Badge>
                        <span>{e.message}</span>
                      </div>
                      <span className="shrink-0 text-xs text-muted-foreground">{formatDateTime(e.created_at)}</span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-3 flex justify-end">
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/agent">View all logs</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}

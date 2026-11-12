"use client";

import Link from "next/link";
import { Download, FileText } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import type { DocumentItem } from "@/lib/types-ext";
import { formatDateTime } from "@/lib/utils";
import { Alert, EmptyState, LoadingBlock } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";

const KIND: Record<DocumentItem["kind"], string> = { resume: "CV", cover_letter: "Cover letter", email: "Email", answers: "Answers" };

type Group = { key: string; job: DocumentItem["job"]; version: number; created: string; docs: DocumentItem[] };

function group(docs: DocumentItem[]): Group[] {
  const map = new Map<string, Group>();
  for (const d of docs) {
    const key = `${d.application_id}-${d.version}`;
    const g = map.get(key) ?? { key, job: d.job, version: d.version, created: d.created_at, docs: [] };
    g.docs.push(d);
    map.set(key, g);
  }
  return [...map.values()].sort((a, b) => b.created.localeCompare(a.created));
}

export function GeneratedDocuments() {
  const docs = useAsync(() => api.documents());
  if (docs.error) return <Alert tone="error">{docs.error}</Alert>;
  if (!docs.data) return <LoadingBlock />;
  const groups = group(docs.data.documents);
  if (!groups.length) {
    return <EmptyState icon={FileText} title="No generated documents" description="Open an application (AI Analysis or Applications) and use its Documents tab." />;
  }
  return (
    <ul className="divide-y">
      {groups.map((g) => (
        <li key={g.key} className="space-y-2 py-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="text-sm font-medium">
              {g.job ? <Link className="hover:underline" href={`/applications?job=${g.job.job_id}`}>{g.job.title}</Link> : "Unlinked"}
              {g.job?.company && <span className="font-normal text-muted-foreground"> · {g.job.company}</span>}
              <span className="ml-2 text-xs font-normal text-muted-foreground">v{g.version}</span>
            </p>
            <span className="text-xs text-muted-foreground">{formatDateTime(g.created)}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {g.docs.map((d) => (
              <Button key={d.id} variant="outline" size="sm" asChild>
                <a href={`/api/documents/${d.id}/download`}><Download /> {KIND[d.kind]} .{d.format}</a>
              </Button>
            ))}
          </div>
        </li>
      ))}
    </ul>
  );
}

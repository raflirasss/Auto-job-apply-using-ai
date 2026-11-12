"use client";

import { Download, FileText } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import { formatBytes, formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, EmptyState, LoadingBlock, PageHeader } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { GeneratedDocuments } from "@/components/documents/generated-documents";

export default function DocumentsPage() {
  const cvs = useAsync(() => api.listCVs());
  const profile = useAsync(() => api.getProfile());
  const activeId = profile.data?.profile?.source_cv_id;

  return (
    <>
      <PageHeader title="Documents" description="Original CVs and generated application documents." />
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Original CV files</CardTitle>
            <CardDescription>Stored read-only by content hash. Imports never overwrite an existing file.</CardDescription>
          </CardHeader>
          <CardContent>
            {cvs.error && <Alert tone="error">{cvs.error}</Alert>}
            {cvs.loading && !cvs.data && <LoadingBlock />}
            {cvs.data?.files.length === 0 && (
              <EmptyState icon={FileText} title="No CV uploaded" description="Upload your CV from Settings → Candidate profile." />
            )}
            {cvs.data && cvs.data.files.length > 0 && (
              <ul className="divide-y">
                {cvs.data.files.map((f) => (
                  <li key={f.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                    <div className="flex items-center gap-3">
                      <FileText className="size-5 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">
                          {f.original_filename} {f.id === activeId && <Badge className="ml-1">Active</Badge>}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatBytes(f.size_bytes)} · {f.page_count ?? "?"} page(s) · uploaded {formatDateTime(f.uploaded_at)} · sha256 {f.sha256.slice(0, 12)}
                        </p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a href={`/api/candidate/cv/${f.id}/download`}>
                        <Download /> Download
                      </a>
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tailored CVs &amp; cover letters</CardTitle>
            <CardDescription>Per-application versions (PDF/DOCX, email, form answers). Generate them from an application&apos;s Documents tab.</CardDescription>
          </CardHeader>
          <CardContent><GeneratedDocuments /></CardContent>
        </Card>
      </div>
    </>
  );
}

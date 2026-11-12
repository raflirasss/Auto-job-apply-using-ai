"use client";

import { useState } from "react";
import { Download, FileText } from "lucide-react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import type { GenerateResult } from "@/lib/types-ext";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Select } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const KIND: Record<string, string> = { resume: "CV", cover_letter: "Cover letter", email: "Email", answers: "Form answers" };

export function DocumentsPanel({ job, onGenerated }: { job: Job; onGenerated: () => void }) {
  const [template, setTemplate] = useState("classic");
  const [language, setLanguage] = useState<"" | "en" | "id">("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateResult | null>(null);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.generateDocuments(job.id, template, language || undefined));
      onGenerated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Built only from your confirmed profile: job keywords reorder and highlight your real skills and bullets; nothing is added. Each generation is a new version; older versions stay available in Documents.
      </p>
      <div className="flex flex-wrap items-end gap-2">
        <label className="text-xs text-muted-foreground">Template
          <Select className="mt-1 w-36" value={template} onChange={(e) => setTemplate(e.target.value)}>
            <option value="classic">Classic</option><option value="modern">Modern</option>
          </Select>
        </label>
        <label className="text-xs text-muted-foreground">Language
          <Select className="mt-1 w-44" value={language} onChange={(e) => setLanguage(e.target.value as "" | "en" | "id")}>
            <option value="">Same as profile</option><option value="en">English</option><option value="id">Bahasa Indonesia</option>
          </Select>
        </label>
        <Button size="sm" disabled={busy} onClick={generate}>{busy ? <Spinner /> : <FileText />} Generate documents</Button>
      </div>
      {error && <Alert tone="error">{error}</Alert>}
      {result && (
        <div className="space-y-2 rounded-lg border p-3 text-sm">
          <p className="font-medium">Version {result.version} ({result.language.toUpperCase()}, {result.template})</p>
          {result.language !== result.listing_language && (
            <p className="text-xs text-muted-foreground">The listing is in {result.listing_language === "id" ? "Indonesian" : "English"}; your profile text is quoted unchanged (never machine-translated).</p>
          )}
          <div className="flex flex-wrap gap-1.5">
            {result.documents.map((d) => (
              <Button key={d.id} variant="outline" size="sm" asChild>
                <a href={`/api/documents/${d.id}/download`}><Download /> {KIND[d.kind]} .{d.format}</a>
              </Button>
            ))}
          </div>
          {result.keywords_used.length > 0 && <p className="text-xs">Listing keywords present in your documents: {result.keywords_used.join(", ")}</p>}
          {result.missing_answers.length > 0 && (
            <div className="flex flex-wrap items-center gap-1 text-xs">Answers needing your input:
              {result.missing_answers.map((m) => <Badge key={m} variant="warning">{m}</Badge>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

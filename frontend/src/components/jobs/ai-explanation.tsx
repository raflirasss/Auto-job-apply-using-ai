"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";

export function AIExplanation({ job, onUpdated }: { job: Job; onUpdated: (j: Job) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const r = job.match_details;
  if (!r) return null;

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      onUpdated((await api.analyzeJob(job.id, true)).job);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Optional. The AI only writes an explanation of the engine result; it cannot change the score, filters or recommendation. Name, email, phone, website and domicile are not sent.
      </p>
      {r.ai_explanation && (
        <div className="rounded-lg border bg-muted/40 p-3 text-sm whitespace-pre-line">
          {r.ai_explanation}
          {r.ai_model && <p className="mt-2 text-xs text-muted-foreground">Model: {r.ai_model}</p>}
        </div>
      )}
      {r.ai_error && <Alert tone="error" title="AI explanation unavailable">{r.ai_error}</Alert>}
      {error && <Alert tone="error">{error}</Alert>}
      <Button variant="outline" size="sm" disabled={busy} onClick={generate}>
        {busy ? <Spinner /> : <Sparkles />} {r.ai_explanation ? "Regenerate explanation" : "Generate AI explanation"}
      </Button>
    </div>
  );
}

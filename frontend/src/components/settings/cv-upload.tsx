"use client";

import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { api } from "@/lib/api";
import type { CVImportResult } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Alert, Spinner } from "@/components/ui/feedback";

export function CVUpload({ hasProfile, onImported }: { hasProfile: boolean; onImported: (r: CVImportResult) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CVImportResult | null>(null);

  async function onFile(file: File) {
    if (hasProfile && !window.confirm("Importing a CV replaces the current profile with a new unconfirmed draft. Previous versions stay in history, and the original CV file is kept. Continue?")) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await api.uploadCV(file);
      setResult(r);
      onImported(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  return (
    <div className="space-y-3">
      <input
        ref={input}
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
      />
      <Button variant={hasProfile ? "outline" : "default"} onClick={() => input.current?.click()} disabled={busy}>
        {busy ? <Spinner /> : <Upload />} {hasProfile ? "Re-import CV" : "Upload CV (PDF or DOCX)"}
      </Button>
      {error && <Alert tone="error" title="Import failed">{error}</Alert>}
      {result && (
        <Alert tone="success" title={result.duplicate_file ? "CV re-parsed (identical file already stored)" : "CV imported"}>
          Review every field below. Nothing is used for applications until you confirm the profile.
          {result.extraction_warnings.length > 0 && (
            <ul className="mt-2 list-disc pl-4">
              {result.extraction_warnings.map((w) => <li key={w}>{w}</li>)}
            </ul>
          )}
        </Alert>
      )}
    </div>
  );
}

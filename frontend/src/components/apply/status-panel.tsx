"use client";

import { useState } from "react";
import { Save } from "lucide-react";
import { api } from "@/lib/api";
import type { ApplicationStatus, Job } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Field, Input, Select, Textarea } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { STATUS_LABELS, StatusBadge } from "@/components/jobs/match-badges";

const MANUAL: ApplicationStatus[] = ["discovered", "analyzed", "qualified", "ready_to_apply", "pending_action", "applied",
  "assessment", "interview", "accepted", "rejected", "failed"];

export function StatusPanel({ job, onUpdated }: { job: Job; onUpdated: (j: Job) => void }) {
  const app = job.application;
  const [status, setStatus] = useState<ApplicationStatus>(app?.status ?? "discovered");
  const [note, setNote] = useState(app?.notes ?? "");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (!app) return null;

  async function save() {
    setBusy(true);
    setError(null);
    try {
      onUpdated((await api.setApplicationStatus(job.id, status, note, confirmation || undefined)).job);
      setConfirmation("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  const needsConfirmation = status === "applied" && app.status !== "applied";
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-sm">Current: <StatusBadge status={app.status} />
        {app.applied_at && <span className="text-xs text-muted-foreground">applied {formatDateTime(app.applied_at)}</span>}
      </div>
      {app.submission_confirmation && <p className="text-xs text-muted-foreground">Confirmation: {app.submission_confirmation}</p>}
      {app.pending_action && <Alert tone="warning" title="Action needed"><span className="whitespace-pre-line">{app.pending_action}</span></Alert>}
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Set status">
          <Select value={status} onChange={(e) => setStatus(e.target.value as ApplicationStatus)}>
            {MANUAL.map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
          </Select>
        </Field>
        {needsConfirmation && (
          <Field label="Submission confirmation (required)" hint="e.g. confirmation email date / reference">
            <Input value={confirmation} onChange={(e) => setConfirmation(e.target.value)} />
          </Field>
        )}
        <Field label="Notes" className="sm:col-span-2"><Textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} /></Field>
      </div>
      {error && <Alert tone="error">{error}</Alert>}
      <Button size="sm" disabled={busy || (needsConfirmation && !confirmation.trim())} onClick={save}>
        {busy ? <Spinner /> : <Save />} Update status
      </Button>
    </div>
  );
}

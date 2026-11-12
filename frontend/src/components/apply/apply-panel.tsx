"use client";

import { useEffect, useState } from "react";
import { Bot, ExternalLink, Image as ImageIcon, Mail, MousePointerClick } from "lucide-react";
import type { ApplyMode } from "@/lib/types-ext";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { useAsync } from "@/lib/use-async";
import { formatDateTime } from "@/lib/utils";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const OUTCOME: Record<string, "success" | "warning" | "destructive" | "outline"> = {
  submitted: "success", awaiting_user: "warning", stopped: "warning", failed: "destructive", running: "outline",
};

export function ApplyPanel({ job, onChanged }: { job: Job; onChanged: () => void }) {
  const status = useAsync(() => api.applyStatus(job.id));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "info" | "error"; text: string } | null>(null);
  const running = status.data?.attempts.some((a) => a.outcome === "running") || status.data?.browser_busy;

  // Poll while a browser run is active so the result shows up without a manual refresh.
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => { void status.reload(); onChanged(); }, 4000);
    return () => clearInterval(t);
  }, [running, status, onChanged]);

  async function start(mode: ApplyMode) {
    setBusy(true);
    setMessage(null);
    try {
      const r = await api.apply(job.id, mode);
      setMessage({ tone: "info", text: mode === "email" ? `Application email sent. ${r.note}` : r.note });
      await status.reload();
      if (mode === "email") onChanged();
    } catch (e) {
      setMessage({ tone: "error", text: e instanceof Error ? e.message : "Could not start" });
    } finally {
      setBusy(false);
    }
  }

  const s = status.data;
  return (
    <div className="space-y-3">
      {s && <p className="text-xs text-muted-foreground">{s.policy_note}</p>}
      <div className="flex flex-wrap gap-2">
        {job.application_url && (
          <Button variant="outline" size="sm" asChild>
            <a href={job.application_url} target="_blank" rel="noopener noreferrer"><ExternalLink /> Open listing yourself</a>
          </Button>
        )}
        {s?.allowed_modes.includes("email") && (
          <Button size="sm" disabled={busy || !!s.blocked_reason.email} title={s.blocked_reason.email ?? ""}
            onClick={() => window.confirm(`Send your CV and cover letter to ${s.apply_email}?`) && start("email")}>
            {busy ? <Spinner /> : <Mail />} Apply by email
          </Button>
        )}
        {s?.allowed_modes.includes("assisted") && (
          <Button size="sm" disabled={busy || !!running || !!s.blocked_reason.assisted} title={s.blocked_reason.assisted ?? ""} onClick={() => start("assisted")}>
            {busy ? <Spinner /> : <MousePointerClick />} Assisted apply
          </Button>
        )}
        {s?.allowed_modes.includes("auto") && (
          <Button size="sm" variant="secondary" disabled={busy || !!running || !!s.blocked_reason.auto} title={s.blocked_reason.auto ?? ""} onClick={() => start("auto")}>
            <Bot /> Auto apply
          </Button>
        )}
      </div>
      {s && s.allowed_modes.length > 0 && s.allowed_modes.every((m) => s.blocked_reason[m]) && (
        <p className="text-xs text-warning">Not ready: {s.blocked_reason[s.allowed_modes[0]]}</p>
      )}
      {running && <p className="flex items-center gap-2 text-xs text-muted-foreground"><Spinner /> Browser automation running…</p>}
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      {s && s.attempts.length > 0 && (
        <ul className="space-y-2">
          {s.attempts.map((a) => (
            <li key={a.id} className="rounded-lg border p-2.5 text-xs">
              <div className="flex flex-wrap items-center gap-1.5">
                <Badge variant={OUTCOME[a.outcome]}>{a.outcome.replace("_", " ")}</Badge>
                <Badge variant="outline">{a.mode}</Badge>
                {a.stop_reason && <span className="text-muted-foreground">{a.stop_reason}</span>}
                <span className="ml-auto text-muted-foreground">{formatDateTime(a.started_at)}</span>
              </div>
              {a.detail && <p className="mt-1">{a.detail}</p>}
              {a.fields_filled.length > 0 && <p className="mt-1 text-muted-foreground">Filled: {a.fields_filled.join(", ")}</p>}
              {a.fields_unresolved.length > 0 && (
                <ul className="mt-1 list-disc pl-4 text-warning">{a.fields_unresolved.map((u) => <li key={u}>{u}</li>)}</ul>
              )}
              {a.has_screenshot && (
                <a className="mt-1 inline-flex items-center gap-1 underline" href={`/api/apply-attempts/${a.id}/screenshot`} target="_blank" rel="noreferrer">
                  <ImageIcon className="size-3" /> Screenshot
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

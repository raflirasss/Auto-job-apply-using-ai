"use client";

import { useEffect, useState } from "react";
import { Pause, Play, PlayCircle, Search } from "lucide-react";
import { api } from "@/lib/api";
import type { AgentStatus } from "@/lib/types-ext";
import { formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function AgentControls({ status, onChange }: { status: AgentStatus; onChange: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const running = !!status.active_run;

  useEffect(() => {
    if (!running) return;
    const t = setInterval(onChange, 3000);
    return () => clearInterval(t);
  }, [running, onChange]);

  async function act(name: string, fn: () => Promise<unknown>, ok: string) {
    setBusy(name);
    setMessage(null);
    try {
      await fn();
      setMessage({ tone: "success", text: ok });
      onChange();
    } catch (e) {
      setMessage({ tone: "error", text: e instanceof Error ? e.message : "Failed" });
    } finally {
      setBusy(null);
    }
  }

  const state = !status.enabled ? { label: "Stopped", v: "outline" as const }
    : status.paused ? { label: "Paused", v: "warning" as const } : { label: "Active", v: "success" as const };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">Agent <Badge variant={state.v}>{state.label}</Badge>
          {running && <Badge variant="default"><Spinner className="size-3" /> run #{status.active_run!.id} in progress</Badge>}
        </CardTitle>
        <CardDescription>
          Daily at {status.run_time} ({status.timezone}).{" "}
          {status.next_run_time ? `Next run: ${formatDateTime(status.next_run_time)}.` : "No run scheduled."}
          {!status.scheduler_running && " Scheduler process is not running (ENABLE_SCHEDULER=false)."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {!status.enabled && (
            <Button disabled={busy !== null} onClick={() => act("start", () => api.agentAction("start"), "Agent started.")}>
              {busy === "start" ? <Spinner /> : <Play />} Start agent
            </Button>
          )}
          {status.enabled && !status.paused && (
            <Button variant="outline" disabled={busy !== null} onClick={() => act("pause", () => api.agentAction("pause"), "Agent paused.")}>
              {busy === "pause" ? <Spinner /> : <Pause />} Pause
            </Button>
          )}
          {status.enabled && status.paused && (
            <Button disabled={busy !== null} onClick={() => act("resume", () => api.agentAction("resume"), "Agent resumed.")}>
              {busy === "resume" ? <Spinner /> : <PlayCircle />} Resume
            </Button>
          )}
          <Button variant="outline" disabled={busy !== null || running} onClick={() => act("run", () => api.agentRunNow(), "Run started.")}>
            {busy === "run" ? <Spinner /> : <Search />} Run now
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Each run: analyse new imported listings, apply hard filters, generate documents for eligible jobs, run permitted application workflows within the daily limit, and send a summary.
          Applications go by email (from your mailbox) or through the employer&apos;s own form; anything unverified stops and waits for you.
        </p>
        {message && <Alert tone={message.tone}>{message.text}</Alert>}
      </CardContent>
    </Card>
  );
}

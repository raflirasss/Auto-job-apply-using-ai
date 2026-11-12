"use client";

import { useState } from "react";
import { Save } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import type { SchedulerConfig } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, LoadingBlock, Spinner } from "@/components/ui/feedback";
import { Field, Input, Switch } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { AISettings } from "./ai-settings";
import { errText, MsgText, type Msg } from "./check-group";

function SchedulerSettings() {
  const req = useAsync(() => api.getScheduler());
  const [draft, setDraft] = useState<SchedulerConfig | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<Msg>(null);
  const s = draft ?? req.data;
  if (req.loading && !req.data) return <LoadingBlock />;
  if (!s) return <Alert tone="error">{req.error}</Alert>;

  async function save() {
    if (!s) return;
    setBusy(true);
    try {
      req.setData(await api.saveScheduler(s));
      setDraft(null);
      setMsg({ tone: "success", text: "Scheduler settings saved." });
    } catch (e) {
      setMsg({ tone: "error", text: errText(e) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scheduler</CardTitle>
        <CardDescription>Stored now; the APScheduler runner is activated in Phase 6.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Daily run time (Asia/Jakarta)"><Input type="time" value={s.run_time} onChange={(e) => setDraft({ ...s, run_time: e.target.value })} /></Field>
          <Field label="Max retries"><Input type="number" min={0} max={10} value={s.max_retries} onChange={(e) => setDraft({ ...s, max_retries: Number(e.target.value) })} /></Field>
          <div className="flex items-center gap-3 self-end pb-2">
            <Switch checked={s.enabled} label="Scheduler enabled" onChange={(v) => setDraft({ ...s, enabled: v })} />
            <span className="text-sm">Enabled</span>
          </div>
        </div>
        <div className="flex items-center justify-end gap-2">
          <MsgText msg={msg} />
          <Button disabled={!draft || busy} onClick={save}>{busy ? <Spinner /> : <Save />} Save scheduler</Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function SystemSettings() {
  return (
    <div className="space-y-6">
      <AISettings />
      <SchedulerSettings />
    </div>
  );
}

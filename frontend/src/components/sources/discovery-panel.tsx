"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { RefreshCw, Settings } from "lucide-react";
import { api } from "@/lib/api";
import type { SourcesStatus } from "@/lib/types-ext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const LABEL: Record<string, string> = { rss: "Google Alerts / RSS", telegram: "Telegram", ats: "Company boards" };

export function DiscoveryPanel({ onFinished }: { onFinished: () => void }) {
  const [status, setStatus] = useState<SourcesStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const wasRunning = useRef(false);

  useEffect(() => {
    let alive = true;
    const load = () => api.sources().then((s) => {
      if (!alive) return;
      setStatus(s);
      if (wasRunning.current && !s.discovery_running) onFinished();
      wasRunning.current = s.discovery_running;
    }).catch((e) => alive && setError(e instanceof Error ? e.message : "Failed"));
    void load();
    const t = setInterval(load, 3000);
    return () => { alive = false; clearInterval(t); };
  }, [onFinished]);

  async function run() {
    setStarting(true);
    setError(null);
    try {
      await api.runDiscovery();
      wasRunning.current = true;
      setStatus((s) => (s ? { ...s, discovery_running: true } : s));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setStarting(false);
    }
  }

  const cfg = status?.config;
  const enabled = cfg ? [cfg.rss.enabled && "rss", cfg.telegram.enabled && "telegram", cfg.ats.enabled && "ats"].filter(Boolean) as string[] : [];
  const running = status?.discovery_running;

  return (
    <Card className="mb-6">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3">
        <div>
          <CardTitle>Job sources</CardTitle>
          <CardDescription>
            {enabled.length ? `Enabled: ${enabled.map((s) => LABEL[s]).join(", ")}.` : "No source enabled yet."} New listings are fetched automatically by the agent.
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" asChild><Link href="/settings"><Settings /> Configure</Link></Button>
          <Button size="sm" disabled={!enabled.length || running || starting} onClick={run}>
            {running || starting ? <Spinner /> : <RefreshCw />} {running ? "Checking…" : "Check sources now"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {!enabled.length && status && (
          <Alert tone="info">Open <strong>Settings → Sources &amp; email</strong> to add Google Alerts feeds, Telegram channels or company boards.</Alert>
        )}
        {status && Object.entries(status.last_report).filter(([k]) => k !== "_busy").map(([name, rep]) => (
          <div key={name} className="rounded-lg border p-2.5 text-xs">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-medium">{LABEL[name] ?? name}</span>
              <Badge variant="outline">{rep.fetched} fetched</Badge>
              <Badge variant={rep.created ? "success" : "outline"}>{rep.created} new</Badge>
              {rep.updated > 0 && <Badge variant="outline">{rep.updated} updated</Badge>}
              {rep.failed > 0 && <Badge variant="destructive">{rep.failed} failed</Badge>}
            </div>
            {[...rep.errors, ...rep.notes].slice(0, 4).map((m) => <p key={m} className="mt-1 text-muted-foreground">{m}</p>)}
          </div>
        ))}
        {error && <Alert tone="error">{error}</Alert>}
      </CardContent>
    </Card>
  );
}

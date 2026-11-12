"use client";

import { useState } from "react";
import { Save } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import type { SourcesConfig } from "@/lib/types-ext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, LoadingBlock, Spinner } from "@/components/ui/feedback";
import { Field, Input } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { AtsEditor, RssEditor, TelegramEditor } from "./source-editors";
import { TelegramConnect } from "./telegram-connect";
import { SmtpSettings } from "./smtp-settings";

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle>{description && <CardDescription>{description}</CardDescription>}</CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export function SourcesSettings() {
  const req = useAsync(() => api.sources());
  const [draft, setDraft] = useState<SourcesConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  if (req.loading && !req.data) return <LoadingBlock />;
  if (!req.data) return <Alert tone="error">{req.error}</Alert>;
  const cfg = draft ?? req.data.config;
  const update = (fn: (c: SourcesConfig) => SourcesConfig) => { setDraft(fn(cfg)); setMsg(null); };

  async function save() {
    setSaving(true);
    try {
      const clean = { ...cfg, rss: { ...cfg.rss, feeds: cfg.rss.feeds.filter((f) => f.url.trim()).map((f) => ({ name: f.name.trim() || "Feed", url: f.url.trim() })) } };
      req.setData(await api.saveSources(clean));
      setDraft(null);
      setMsg({ tone: "success", text: "Sources saved." });
    } catch (e) {
      setMsg({ tone: "error", text: e instanceof Error ? e.message : "Save failed" });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <Alert tone="info" title="Where jobs come from">
        Only sources with an official feed or public API are used: Google Alerts RSS, public Telegram channels, and company career boards (Lever, Greenhouse). Sites that forbid automated access (JobStreet, LinkedIn…) are not scraped.
      </Alert>
      <Section title="Google Alerts / RSS feeds"><RssEditor cfg={cfg} update={update} /></Section>
      <Section title="Telegram channels">
        <div className="space-y-6">
          <TelegramEditor cfg={cfg} update={update} connected={req.data.telegram_connected} />
          <div className="border-t pt-4"><TelegramConnect connected={req.data.telegram_connected} onChange={() => void req.reload()} /></div>
        </div>
      </Section>
      <Section title="Company career boards"><AtsEditor cfg={cfg} update={update} /></Section>
      <Section title="Checking frequency">
        <Field label="Check sources every (hours)" hint="Between the daily 08:00 run, sources are checked again at this interval (only while the agent is active).">
          <Input type="number" min={1} max={24} className="max-w-32" value={cfg.fetch_interval_hours}
            onChange={(e) => update((c) => ({ ...c, fetch_interval_hours: Number(e.target.value) }))} />
        </Field>
      </Section>
      <div className="flex items-center justify-end gap-3">
        {msg && <span className={`text-sm ${msg.tone === "error" ? "text-destructive" : "text-success"}`}>{msg.text}</span>}
        <Button disabled={!draft || saving} onClick={save}>{saving ? <Spinner /> : <Save />} Save sources</Button>
      </div>
      <Section title="Email applications (your mailbox)" description="Lets the agent apply automatically to listings that ask for applications by email.">
        <SmtpSettings key={JSON.stringify(req.data.smtp)} status={req.data.smtp} onSaved={() => void req.reload()} />
      </Section>
    </div>
  );
}

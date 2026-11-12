"use client";

import { Plus, Trash2 } from "lucide-react";
import type { SourcesConfig } from "@/lib/types-ext";
import { Field, Input, Select, Switch } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { ChipListEditor } from "@/components/settings/list-editor";

type Update = (fn: (c: SourcesConfig) => SourcesConfig) => void;

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return <div className="flex items-center gap-3"><Switch checked={checked} label={label} onChange={onChange} /><span className="text-sm font-medium">{label}</span></div>;
}

export function RssEditor({ cfg, update }: { cfg: SourcesConfig; update: Update }) {
  const feeds = cfg.rss.feeds;
  const setFeeds = (f: typeof feeds) => update((c) => ({ ...c, rss: { ...c.rss, feeds: f } }));
  return (
    <div className="space-y-3">
      <Toggle checked={cfg.rss.enabled} label="Use RSS feeds" onChange={(v) => update((c) => ({ ...c, rss: { ...c.rss, enabled: v } }))} />
      <ol className="list-decimal space-y-0.5 pl-5 text-xs text-muted-foreground">
        <li>Open <a className="underline" href="https://www.google.com/alerts" target="_blank" rel="noreferrer">google.com/alerts</a> and type e.g. <code>&quot;lowongan admin marketplace&quot; jakarta</code>.</li>
        <li>Show options → <strong>Deliver to: RSS feed</strong> → Create Alert.</li>
        <li>Click the RSS icon next to the alert, copy the URL and paste it below. One alert per position works best.</li>
      </ol>
      {feeds.map((f, i) => (
        <div key={i} className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,2.5fr)_auto]">
          <Input placeholder="Name (e.g. Admin Marketplace)" value={f.name} onChange={(e) => setFeeds(feeds.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))} />
          <Input placeholder="https://www.google.com/alerts/feeds/..." value={f.url} onChange={(e) => setFeeds(feeds.map((x, j) => (j === i ? { ...x, url: e.target.value } : x)))} />
          <Button variant="ghost" size="icon" aria-label="Remove feed" onClick={() => setFeeds(feeds.filter((_, j) => j !== i))}><Trash2 /></Button>
        </div>
      ))}
      <Button variant="outline" size="sm" onClick={() => setFeeds([...feeds, { name: "", url: "" }])}><Plus /> Add feed</Button>
    </div>
  );
}

export function TelegramEditor({ cfg, update, connected }: { cfg: SourcesConfig; update: Update; connected: boolean }) {
  const tg = cfg.telegram;
  const set = (patch: Partial<typeof tg>) => update((c) => ({ ...c, telegram: { ...c.telegram, ...patch } }));
  return (
    <div className="space-y-3">
      <Toggle checked={tg.enabled} label="Read Telegram job channels" onChange={(v) => set({ enabled: v })} />
      <Field label="Public channels" hint="Use the @username or t.me link of public job channels you trust. Inactive channels are reported, not skipped silently.">
        <ChipListEditor values={tg.channels} onChange={(v) => set({ channels: v })} placeholder="@channelname or https://t.me/channelname" />
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Read method">
          <Select value={tg.method} onChange={(e) => set({ method: e.target.value as "api" | "preview" })}>
            <option value="api" disabled={!connected}>Telegram API (your account){connected ? "" : " – connect below first"}</option>
            <option value="preview">Public web preview (t.me/s/…)</option>
          </Select>
        </Field>
        <Field label="Messages per channel"><Input type="number" min={10} max={500} value={tg.messages_per_channel} onChange={(e) => set({ messages_per_channel: Number(e.target.value) })} /></Field>
      </div>
    </div>
  );
}

export function AtsEditor({ cfg, update }: { cfg: SourcesConfig; update: Update }) {
  const ats = cfg.ats;
  const set = (patch: Partial<typeof ats>) => update((c) => ({ ...c, ats: { ...c.ats, ...patch } }));
  return (
    <div className="space-y-3">
      <Toggle checked={ats.enabled} label="Read company career boards" onChange={(v) => set({ enabled: v })} />
      <p className="text-xs text-muted-foreground">
        Public job-board APIs. The token is the company part of the careers URL: <code>jobs.lever.co/<strong>ninjavan</strong></code>,{" "}
        <code>job-boards.greenhouse.io/<strong>xendit</strong></code>. Only jobs in Indonesia / your locations are kept. These forms support full auto-apply.
      </p>
      <Field label="Lever companies"><ChipListEditor values={ats.lever} onChange={(v) => set({ lever: v })} placeholder="e.g. ninjavan" /></Field>
      <Field label="Greenhouse companies"><ChipListEditor values={ats.greenhouse} onChange={(v) => set({ greenhouse: v })} placeholder="e.g. xendit" /></Field>
    </div>
  );
}

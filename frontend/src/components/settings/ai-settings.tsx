"use client";

import { useState } from "react";
import { KeyRound } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, LoadingBlock, Spinner } from "@/components/ui/feedback";
import { Field, Input } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { errText, MsgText, type Msg } from "./check-group";

export function AISettings() {
  const req = useAsync(() => api.getAI());
  const [baseUrl, setBaseUrl] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<Msg>(null);

  if (req.loading && !req.data) return <LoadingBlock />;
  if (!req.data) return <Alert tone="error">{req.error}</Alert>;
  const cfg = req.data;

  async function save(clear: boolean) {
    setBusy(true);
    setMsg(null);
    try {
      const r = await api.saveAI({
        base_url: (baseUrl ?? cfg.base_url ?? "").trim() || null,
        model: (model ?? cfg.model ?? "").trim() || null,
        ...(apiKey ? { api_key: apiKey } : {}),
        ...(clear ? { clear_api_key: true } : {}),
      });
      req.setData(r);
      setApiKey("");
      setBaseUrl(null);
      setModel(null);
      setMsg({ tone: "success", text: "AI configuration saved." });
    } catch (e) {
      setMsg({ tone: "error", text: errText(e) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI provider</CardTitle>
        <CardDescription>
          OpenAI-compatible endpoint (e.g. a Claude-compatible gateway), used from Phase 3. Keys entered here are encrypted at rest and never returned in full.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          Status: {cfg.configured ? <Badge variant="success">configured</Badge> : <Badge variant="outline">not configured</Badge>}
          {cfg.api_key_masked && <span className="text-muted-foreground">key {cfg.api_key_masked} (from {cfg.api_key_source})</span>}
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Base URL"><Input value={baseUrl ?? cfg.base_url ?? ""} placeholder="https://api.example.com/v1" onChange={(e) => setBaseUrl(e.target.value)} /></Field>
          <Field label="Model"><Input value={model ?? cfg.model ?? ""} onChange={(e) => setModel(e.target.value)} /></Field>
          <Field label="API key" hint="Leave blank to keep the current key." className="sm:col-span-2">
            <Input type="password" autoComplete="off" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          </Field>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2">
          <MsgText msg={msg} />
          {cfg.api_key_source === "dashboard" && <Button variant="outline" disabled={busy} onClick={() => save(true)}>Remove stored key</Button>}
          <Button disabled={busy} onClick={() => save(false)}>{busy ? <Spinner /> : <KeyRound />} Save AI settings</Button>
        </div>
      </CardContent>
    </Card>
  );
}

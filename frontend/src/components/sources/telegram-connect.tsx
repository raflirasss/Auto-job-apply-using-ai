"use client";

import { useState } from "react";
import { Link2, Unlink } from "lucide-react";
import { api } from "@/lib/api";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Field, Input } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function TelegramConnect({ connected, onChange }: { connected: boolean; onChange: () => void }) {
  const [step, setStep] = useState<"form" | "code">("form");
  const [apiId, setApiId] = useState("");
  const [apiHash, setApiHash] = useState("");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(fn: () => Promise<unknown>, next?: () => void) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      next?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  if (connected) {
    return (
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <Badge variant="success">Telegram connected</Badge>
        <Button variant="outline" size="sm" disabled={busy} onClick={() => run(() => api.telegramDisconnect(), onChange)}><Unlink /> Disconnect</Button>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Optional, recommended. Get <strong>api_id</strong> and <strong>api_hash</strong> at <a className="underline" href="https://my.telegram.org" target="_blank" rel="noreferrer">my.telegram.org</a> → API development tools.
        The app only reads the channels listed above; it never posts, joins or messages. The session is stored encrypted on this computer.
      </p>
      {step === "form" ? (
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="api_id"><Input inputMode="numeric" value={apiId} onChange={(e) => setApiId(e.target.value)} /></Field>
          <Field label="api_hash"><Input type="password" autoComplete="off" value={apiHash} onChange={(e) => setApiHash(e.target.value)} /></Field>
          <Field label="Phone (+62…)"><Input value={phone} placeholder="+62812…" onChange={(e) => setPhone(e.target.value)} /></Field>
          <div className="sm:col-span-3">
            <Button size="sm" disabled={busy || !apiId || !apiHash || !phone}
              onClick={() => run(() => api.telegramSendCode(Number(apiId), apiHash.trim(), phone.replace(/[\s-]/g, "")), () => setStep("code"))}>
              {busy ? <Spinner /> : <Link2 />} Send login code
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Code from Telegram"><Input inputMode="numeric" value={code} onChange={(e) => setCode(e.target.value)} /></Field>
          <Field label="2-step password (if set)"><Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
          <div className="flex items-end gap-2">
            <Button size="sm" disabled={busy || !code} onClick={() => run(() => api.telegramVerify(code, password), () => { setStep("form"); setCode(""); setPassword(""); onChange(); })}>
              {busy ? <Spinner /> : <Link2 />} Connect
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setStep("form")}>Back</Button>
          </div>
        </div>
      )}
      {error && <Alert tone="error">{error}</Alert>}
    </div>
  );
}

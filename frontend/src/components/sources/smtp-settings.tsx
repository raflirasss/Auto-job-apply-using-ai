"use client";

import { useState } from "react";
import { MailCheck, Save } from "lucide-react";
import { api } from "@/lib/api";
import type { SmtpStatus } from "@/lib/types-ext";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Field, Input, Switch } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function SmtpSettings({ status, onSaved }: { status: SmtpStatus; onSaved: () => void }) {
  const [host, setHost] = useState(status.host ?? "smtp.gmail.com");
  const [port, setPort] = useState(status.port ?? 465);
  const [ssl, setSsl] = useState(status.use_ssl ?? true);
  const [username, setUsername] = useState(status.username ?? "");
  const [fromName, setFromName] = useState(status.from_name ?? "");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState<"save" | "test" | null>(null);
  const [msg, setMsg] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  async function run(kind: "save" | "test") {
    setBusy(kind);
    setMsg(null);
    try {
      if (kind === "save") {
        await api.saveSmtp({ host, port, use_ssl: ssl, username, from_name: fromName || null, ...(password ? { password } : {}) });
        setPassword("");
        onSaved();
        setMsg({ tone: "success", text: "Saved." });
      } else {
        await api.testSmtp();
        setMsg({ tone: "success", text: "Login to the mail server succeeded (nothing was sent)." });
      }
    } catch (e) {
      setMsg({ tone: "error", text: e instanceof Error ? e.message : "Failed" });
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Many listings (especially on Telegram) say &quot;send your CV to hrd@…&quot;. The agent then emails your tailored CV + cover letter from your own mailbox.
        For Gmail, create an <a className="underline" href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer">App Password</a> (requires 2-Step Verification) and use it here, not your normal password.
      </p>
      <div className="flex items-center gap-2 text-sm">Status: {status.password_set && status.username ? <Badge variant="success">configured</Badge> : <Badge variant="outline">not configured</Badge>}</div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Your email address"><Input type="email" value={username} placeholder="you@gmail.com" onChange={(e) => setUsername(e.target.value)} /></Field>
        <Field label="Sender name"><Input value={fromName} onChange={(e) => setFromName(e.target.value)} /></Field>
        <Field label="App password" hint={status.password_set ? "Leave blank to keep the saved password." : undefined}>
          <Input type="password" autoComplete="off" value={password} onChange={(e) => setPassword(e.target.value)} />
        </Field>
        <div className="grid grid-cols-[1fr_6rem] gap-2">
          <Field label="SMTP server"><Input value={host} onChange={(e) => setHost(e.target.value)} /></Field>
          <Field label="Port"><Input type="number" value={port} onChange={(e) => setPort(Number(e.target.value))} /></Field>
        </div>
      </div>
      <div className="flex items-center gap-3"><Switch checked={ssl} label="SSL" onChange={setSsl} /><span className="text-sm">SSL (port 465). Turn off for STARTTLS (port 587).</span></div>
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" disabled={busy !== null || !username} onClick={() => run("save")}>{busy === "save" ? <Spinner /> : <Save />} Save</Button>
        <Button size="sm" variant="outline" disabled={busy !== null || !status.password_set} onClick={() => run("test")}>{busy === "test" ? <Spinner /> : <MailCheck />} Test login</Button>
      </div>
      {msg && <Alert tone={msg.tone}>{msg.text}</Alert>}
    </div>
  );
}

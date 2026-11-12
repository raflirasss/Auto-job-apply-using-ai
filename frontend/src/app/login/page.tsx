"use client";

import { useState } from "react";
import { Briefcase, Lock } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/form";
import { Alert, Spinner } from "@/components/ui/feedback";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.login(password);
      // Full reload on auth change so the proxy sees the new session cookie and no stale client state remains.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <div className="mb-2 rounded-xl bg-primary p-2.5 text-primary-foreground">
            <Briefcase className="size-5" />
          </div>
          <CardTitle className="text-lg">AI Job Hunter</CardTitle>
          <CardDescription>Sign in to your dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="password">Dashboard password</Label>
              <Input id="password" type="password" autoComplete="current-password" autoFocus required value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {error && <Alert tone="error">{error}</Alert>}
            <Button type="submit" className="w-full" disabled={busy || !password}>
              {busy ? <Spinner /> : <Lock />} Sign in
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}

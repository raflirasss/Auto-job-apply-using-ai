"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { RefreshCw, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import type { Job } from "@/lib/types";
import { Alert, EmptyState, LoadingBlock, PageHeader, Spinner } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { AnalysisList } from "./analysis-list";
import { AnalysisDetail } from "./analysis-detail";

export function AnalysisView() {
  const jobs = useAsync(() => api.jobs(500));
  const router = useRouter();
  const params = useSearchParams();
  const selectedId = Number(params.get("job")) || null;
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const list = jobs.data?.jobs ?? [];
  const selected = list.find((j) => j.id === selectedId) ?? null;

  const { setData } = jobs;
  const replaceJob = useCallback(
    (updated: Job) => setData((d) => (d ? { ...d, jobs: d.jobs.map((j) => (j.id === updated.id ? updated : j)) } : d)),
    [setData],
  );
  const errorText = (e: unknown) => (e instanceof Error ? e.message : "Analysis failed");

  async function runAll(reanalyze: boolean) {
    setBusy(reanalyze ? "re" : "all");
    setMessage(null);
    try {
      const r = await api.analyzeAll(reanalyze);
      setMessage({ tone: "success", text: `Analysed ${r.analyzed} job(s).` });
      await jobs.reload();
    } catch (e) {
      setMessage({ tone: "error", text: errorText(e) });
    } finally {
      setBusy(null);
    }
  }

  async function runOne(id: number) {
    setBusy(`job-${id}`);
    setMessage(null);
    try {
      replaceJob((await api.analyzeJob(id)).job);
    } catch (e) {
      setMessage({ tone: "error", text: errorText(e) });
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeader
        title="AI Analysis"
        description="Deterministic match scores and hard filters. The AI can explain a result but never changes it."
        actions={<>
          <Button variant="outline" disabled={busy !== null || !list.length} onClick={() => runAll(true)}>
            {busy === "re" ? <Spinner /> : <RefreshCw />} Re-analyse all
          </Button>
          <Button disabled={busy !== null || !list.length} onClick={() => runAll(false)}>
            {busy === "all" ? <Spinner /> : <Sparkles />} Analyse new
          </Button>
        </>}
      />
      {message && <Alert tone={message.tone} className="mb-6">{message.text}</Alert>}
      {jobs.error && <Alert tone="error">{jobs.error}</Alert>}
      {jobs.loading && !jobs.data && <LoadingBlock />}
      {jobs.data && !list.length && (
        <EmptyState icon={Sparkles} title="Nothing to analyse" description="Enable sources and check them on the Job Discovery page first.">
          <Button asChild variant="outline"><Link href="/jobs">Go to Job Discovery</Link></Button>
        </EmptyState>
      )}
      {list.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
          <AnalysisList jobs={list} selectedId={selectedId} onSelect={(id) => router.replace(`/analysis?job=${id}`, { scroll: false })} />
          <div>
            {selected ? (
              <AnalysisDetail job={selected} busy={busy !== null} onAnalyze={() => runOne(selected.id)} onUpdated={replaceJob} />
            ) : (
              <EmptyState icon={Sparkles} title="Select a job" description="Pick a listing on the left to see its score breakdown." />
            )}
          </div>
        </div>
      )}
    </>
  );
}

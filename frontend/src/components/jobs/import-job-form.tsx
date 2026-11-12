"use client";

import { useState } from "react";
import { Import } from "lucide-react";
import { api } from "@/lib/api";
import type { JobImportResult, ManualJobIn, WorkArrangement, EmploymentType } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Field, Input, Select, Textarea } from "@/components/ui/form";
import { Button } from "@/components/ui/button";

const EMPTY = {
  job_url: "", title: "", company: "", location: "", work_arrangement: "", employment_type: "",
  salary_min: "", salary_max: "", salary_period: "monthly", salary_disclosed: false, description: "",
};

export function ImportJobForm({ onImported, onCancel }: { onImported: (r: JobImportResult) => void; onCancel: () => void }) {
  const [f, setF] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const set = (k: keyof typeof EMPTY, v: string | boolean) => setF((prev) => ({ ...prev, [k]: v }));
  const orNull = (v: string) => (v.trim() ? v.trim() : null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const body: ManualJobIn = {
      job_url: f.job_url.trim(),
      title: f.title.trim(),
      company: orNull(f.company),
      location: orNull(f.location),
      work_arrangement: (f.work_arrangement || null) as WorkArrangement | null,
      employment_type: (f.employment_type || null) as EmploymentType | null,
      salary_min: f.salary_disclosed && f.salary_min ? Number(f.salary_min) : null,
      salary_max: f.salary_disclosed && f.salary_max ? Number(f.salary_max) : null,
      salary_period: f.salary_period as ManualJobIn["salary_period"],
      salary_disclosed: f.salary_disclosed,
      description: orNull(f.description),
    };
    try {
      onImported(await api.importJob(body));
      setF(EMPTY);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Add a listing manually</CardTitle>
        <CardDescription>
          Copy the facts from a listing you opened yourself. Leave unknown fields empty. If the listing shows no salary, leave the box unticked: an undisclosed salary is never treated as meeting the minimum.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
          <Field label="Listing URL" className="sm:col-span-2">
            <Input required type="url" placeholder="https://company.com/careers/..." value={f.job_url} onChange={(e) => set("job_url", e.target.value)} />
          </Field>
          <Field label="Job title"><Input required value={f.title} onChange={(e) => set("title", e.target.value)} /></Field>
          <Field label="Company"><Input value={f.company} onChange={(e) => set("company", e.target.value)} /></Field>
          <Field label="Location"><Input value={f.location} placeholder="e.g. Jakarta Selatan" onChange={(e) => set("location", e.target.value)} /></Field>
          <Field label="Work arrangement">
            <Select value={f.work_arrangement} onChange={(e) => set("work_arrangement", e.target.value)}>
              <option value="">Unknown</option><option value="onsite">Onsite</option><option value="hybrid">Hybrid</option><option value="remote">Remote</option>
            </Select>
          </Field>
          <Field label="Employment type">
            <Select value={f.employment_type} onChange={(e) => set("employment_type", e.target.value)}>
              <option value="">Unknown</option><option value="full_time">Full time</option><option value="contract">Contract</option>
              <option value="part_time">Part time</option><option value="internship">Internship</option>
              <option value="freelance">Freelance</option><option value="temporary">Temporary</option>
            </Select>
          </Field>
          <label className="flex items-center gap-2 self-end pb-2 text-sm">
            <input type="checkbox" checked={f.salary_disclosed} onChange={(e) => set("salary_disclosed", e.target.checked)} /> Salary shown in listing
          </label>
          {f.salary_disclosed && (
            <div className="grid gap-4 sm:col-span-2 sm:grid-cols-3">
              <Field label="Salary min (IDR)"><Input type="number" min={0} value={f.salary_min} onChange={(e) => set("salary_min", e.target.value)} /></Field>
              <Field label="Salary max (IDR)"><Input type="number" min={0} value={f.salary_max} onChange={(e) => set("salary_max", e.target.value)} /></Field>
              <Field label="Period" hint="Converted to monthly">
                <Select value={f.salary_period} onChange={(e) => set("salary_period", e.target.value)}>
                  <option value="monthly">Monthly</option><option value="annual">Annual</option><option value="weekly">Weekly</option><option value="daily">Daily</option>
                </Select>
              </Field>
            </div>
          )}
          <Field label="Job description" hint="Paste the full text; Phase 3 matching uses it." className="sm:col-span-2">
            <Textarea rows={6} value={f.description} onChange={(e) => set("description", e.target.value)} />
          </Field>
          {error && <Alert tone="error" className="sm:col-span-2">{error}</Alert>}
          <div className="flex justify-end gap-2 sm:col-span-2">
            <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
            <Button type="submit" disabled={busy}>{busy ? <Spinner /> : <Import />} Import listing</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

"use client";

import { Plus } from "lucide-react";
import type { CandidateProfileData, Certification, Project } from "@/lib/types";
import { Field, Input, Textarea } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { ChipListEditor } from "./list-editor";
import { orNull, type Update } from "./profile-basic";
import { RemoveButton } from "./profile-history";

export function CertProjectSection({ data, update }: { data: CandidateProfileData; update: Update }) {
  const setCert = (i: number, patch: Partial<Certification>) =>
    update((d) => ({ ...d, certifications: d.certifications.map((c, j) => (j === i ? { ...c, ...patch } : c)) }));
  const setProj = (i: number, patch: Partial<Project>) =>
    update((d) => ({ ...d, projects: d.projects.map((p, j) => (j === i ? { ...p, ...patch } : p)) }));
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <p className="text-sm font-medium">Certifications</p>
        {data.certifications.length === 0 && <p className="text-xs text-muted-foreground">None listed in CV.</p>}
        {data.certifications.map((c, i) => (
          <div key={i} className="grid gap-3 rounded-lg border p-4 sm:grid-cols-4">
            <Field label="Name" className="sm:col-span-2"><Input value={c.name} onChange={(e) => setCert(i, { name: e.target.value })} /></Field>
            <Field label="Issuer"><Input value={c.issuer ?? ""} onChange={(e) => setCert(i, { issuer: orNull(e.target.value) })} /></Field>
            <Field label="Date"><Input value={c.date ?? ""} placeholder="YYYY-MM" onChange={(e) => setCert(i, { date: orNull(e.target.value) })} /></Field>
            <Field label="Credential URL" className="sm:col-span-3"><Input value={c.credential_url ?? ""} onChange={(e) => setCert(i, { credential_url: orNull(e.target.value) })} /></Field>
            <div className="flex justify-end self-end">
              <RemoveButton label="Remove certification" onClick={() => update((d) => ({ ...d, certifications: d.certifications.filter((_, j) => j !== i) }))} />
            </div>
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" onClick={() => update((d) => ({ ...d, certifications: [...d.certifications, { name: "", issuer: null, date: null, credential_url: null }] }))}>
          <Plus /> Add certification
        </Button>
      </div>
      <div className="space-y-3">
        <p className="text-sm font-medium">Projects</p>
        {data.projects.length === 0 && <p className="text-xs text-muted-foreground">None listed in CV.</p>}
        {data.projects.map((p, i) => (
          <div key={i} className="grid gap-3 rounded-lg border p-4 sm:grid-cols-2">
            <Field label="Name"><Input value={p.name} onChange={(e) => setProj(i, { name: e.target.value })} /></Field>
            <Field label="URL"><Input value={p.url ?? ""} onChange={(e) => setProj(i, { url: orNull(e.target.value) })} /></Field>
            <Field label="Description" className="sm:col-span-2"><Textarea value={p.description ?? ""} onChange={(e) => setProj(i, { description: orNull(e.target.value) })} /></Field>
            <Field label="Technologies" className="sm:col-span-2"><ChipListEditor values={p.technologies} onChange={(v) => setProj(i, { technologies: v })} /></Field>
            <div className="flex justify-end sm:col-span-2">
              <RemoveButton label="Remove project" onClick={() => update((d) => ({ ...d, projects: d.projects.filter((_, j) => j !== i) }))} />
            </div>
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" onClick={() => update((d) => ({ ...d, projects: [...d.projects, { name: "", description: null, technologies: [], url: null }] }))}>
          <Plus /> Add project
        </Button>
      </div>
    </div>
  );
}

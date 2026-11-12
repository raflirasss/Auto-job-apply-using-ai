"use client";

import { Plus, Trash2 } from "lucide-react";
import type { CandidateProfileData, Education, WorkExperience } from "@/lib/types";
import { Field, Input, Select } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { LinesEditor } from "./list-editor";
import { orNull, type Update } from "./profile-basic";

export function RemoveButton({ onClick, label }: { onClick: () => void; label: string }) {
  return <Button type="button" variant="ghost" size="icon" aria-label={label} onClick={onClick}><Trash2 /></Button>;
}

const numOrNull = (v: string) => (v === "" ? null : Number(v));

export function EducationSection({ data, update }: { data: CandidateProfileData; update: Update }) {
  const setAt = (i: number, patch: Partial<Education>) =>
    update((d) => ({ ...d, education: d.education.map((e, j) => (j === i ? { ...e, ...patch } : e)) }));
  const blank: Education = { institution: "", degree: null, field_of_study: null, gpa: null, gpa_scale: null, location: null, start_date: null, end_date: null, is_expected: false };
  return (
    <div className="space-y-4">
      {data.education.map((e, i) => (
        <div key={i} className="grid gap-3 rounded-lg border p-4 sm:grid-cols-6">
          <Field label="Institution" className="sm:col-span-3"><Input value={e.institution} onChange={(ev) => setAt(i, { institution: ev.target.value })} /></Field>
          <Field label="Degree" className="sm:col-span-3"><Input value={e.degree ?? ""} onChange={(ev) => setAt(i, { degree: orNull(ev.target.value) })} /></Field>
          <Field label="Field of study" className="sm:col-span-2"><Input value={e.field_of_study ?? ""} onChange={(ev) => setAt(i, { field_of_study: orNull(ev.target.value) })} /></Field>
          <Field label="GPA"><Input type="number" step="0.01" value={e.gpa ?? ""} onChange={(ev) => setAt(i, { gpa: numOrNull(ev.target.value) })} /></Field>
          <Field label="Scale"><Input type="number" step="0.01" value={e.gpa_scale ?? ""} onChange={(ev) => setAt(i, { gpa_scale: numOrNull(ev.target.value) })} /></Field>
          <Field label="Start"><Input value={e.start_date ?? ""} placeholder="YYYY-MM" onChange={(ev) => setAt(i, { start_date: orNull(ev.target.value) })} /></Field>
          <Field label="End"><Input value={e.end_date ?? ""} placeholder="YYYY-MM" onChange={(ev) => setAt(i, { end_date: orNull(ev.target.value) })} /></Field>
          <Field label="Location" className="sm:col-span-3"><Input value={e.location ?? ""} onChange={(ev) => setAt(i, { location: orNull(ev.target.value) })} /></Field>
          <label className="flex items-center gap-2 self-end text-sm sm:col-span-2">
            <input type="checkbox" checked={e.is_expected} onChange={(ev) => setAt(i, { is_expected: ev.target.checked })} /> Not yet graduated
          </label>
          <div className="flex justify-end self-end">
            <RemoveButton label="Remove education" onClick={() => update((d) => ({ ...d, education: d.education.filter((_, j) => j !== i) }))} />
          </div>
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={() => update((d) => ({ ...d, education: [...d.education, blank] }))}>
        <Plus /> Add education
      </Button>
    </div>
  );
}

const EMPLOYMENT = ["", "full_time", "part_time", "contract", "freelance", "internship"];

export function ExperienceSection({ data, update }: { data: CandidateProfileData; update: Update }) {
  const setAt = (i: number, patch: Partial<WorkExperience>) =>
    update((d) => ({ ...d, experience: d.experience.map((e, j) => (j === i ? { ...e, ...patch } : e)) }));
  const blank: WorkExperience = { company: "", title: null, location: null, start_date: null, end_date: null, employment_type: null, responsibilities: [] };
  return (
    <div className="space-y-4">
      {data.experience.map((e, i) => (
        <div key={i} className="grid gap-3 rounded-lg border p-4 sm:grid-cols-6">
          <Field label="Company" className="sm:col-span-3"><Input value={e.company} onChange={(ev) => setAt(i, { company: ev.target.value })} /></Field>
          <Field label="Job title" className="sm:col-span-3"><Input value={e.title ?? ""} onChange={(ev) => setAt(i, { title: orNull(ev.target.value) })} /></Field>
          <Field label="Location" className="sm:col-span-2"><Input value={e.location ?? ""} onChange={(ev) => setAt(i, { location: orNull(ev.target.value) })} /></Field>
          <Field label="Start"><Input value={e.start_date ?? ""} placeholder="YYYY or YYYY-MM" onChange={(ev) => setAt(i, { start_date: orNull(ev.target.value) })} /></Field>
          <Field label="End"><Input value={e.end_date ?? ""} placeholder="YYYY-MM / present" onChange={(ev) => setAt(i, { end_date: orNull(ev.target.value) })} /></Field>
          <Field label="Employment type" className="sm:col-span-2">
            <Select value={e.employment_type ?? ""} onChange={(ev) => setAt(i, { employment_type: orNull(ev.target.value) })}>
              {EMPLOYMENT.map((t) => <option key={t} value={t}>{t ? t.replace("_", " ") : "Not answered"}</option>)}
            </Select>
          </Field>
          <Field label="Responsibilities (one per line)" className="sm:col-span-6">
            <LinesEditor values={e.responsibilities} onChange={(v) => setAt(i, { responsibilities: v })} rows={Math.max(3, e.responsibilities.length)} />
          </Field>
          <div className="flex justify-end sm:col-span-6">
            <RemoveButton label="Remove experience" onClick={() => update((d) => ({ ...d, experience: d.experience.filter((_, j) => j !== i) }))} />
          </div>
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={() => update((d) => ({ ...d, experience: [...d.experience, blank] }))}>
        <Plus /> Add experience
      </Button>
    </div>
  );
}

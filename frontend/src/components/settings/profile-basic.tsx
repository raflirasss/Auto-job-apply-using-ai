"use client";

import type { CandidateProfileData } from "@/lib/types";
import { Field, Input, Select, Textarea } from "@/components/ui/form";
import { ChipListEditor } from "./list-editor";

export type Update = (fn: (d: CandidateProfileData) => CandidateProfileData) => void;
export const orNull = (v: string) => (v.trim() === "" ? null : v);

export function PersonalSection({ data, update }: { data: CandidateProfileData; update: Update }) {
  const p = data.personal;
  const set = (k: "full_name" | "email" | "phone" | "location", v: string) =>
    update((d) => ({ ...d, personal: { ...d.personal, [k]: orNull(v) } }));
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field label="Full name"><Input value={p.full_name ?? ""} onChange={(e) => set("full_name", e.target.value)} /></Field>
      <Field label="Email"><Input type="email" value={p.email ?? ""} onChange={(e) => set("email", e.target.value)} /></Field>
      <Field label="Phone"><Input value={p.phone ?? ""} onChange={(e) => set("phone", e.target.value)} /></Field>
      <Field label="Current domicile" hint="Application forms commonly require this.">
        <Input value={p.location ?? ""} placeholder="e.g. Jakarta Timur" onChange={(e) => set("location", e.target.value)} />
      </Field>
      <Field label="Websites / portfolio" className="sm:col-span-2">
        <ChipListEditor values={p.websites} onChange={(v) => update((d) => ({ ...d, personal: { ...d.personal, websites: v } }))} placeholder="Add URL" />
      </Field>
      <Field label="Professional summary" className="sm:col-span-2">
        <Textarea rows={4} value={data.summary ?? ""} onChange={(e) => update((d) => ({ ...d, summary: orNull(e.target.value) }))} />
      </Field>
    </div>
  );
}

const boolValue = (v: boolean | null) => (v === null ? "" : v ? "yes" : "no");
const parseBool = (v: string) => (v === "" ? null : v === "yes");

export function FactsSection({ data, update }: { data: CandidateProfileData; update: Update }) {
  const f = data.application_facts;
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) =>
    update((d) => ({ ...d, application_facts: { ...d.application_facts, [k]: v } }));
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field label="Expected monthly salary (IDR)" hint="Only entered on forms that explicitly ask for it.">
        <Input type="number" min={0} step={100000} value={f.expected_salary_monthly_idr ?? ""}
          onChange={(e) => set("expected_salary_monthly_idr", e.target.value === "" ? null : Number(e.target.value))} />
      </Field>
      <Field label="Availability / start date">
        <Input value={f.availability_date ?? ""} placeholder="immediately or YYYY-MM-DD" onChange={(e) => set("availability_date", orNull(e.target.value))} />
      </Field>
      <Field label="Notice period">
        <Input value={f.notice_period ?? ""} placeholder="e.g. none, 1 month" onChange={(e) => set("notice_period", orNull(e.target.value))} />
      </Field>
      <Field label="Legally allowed to work in Indonesia">
        <Select value={boolValue(f.has_work_authorization_indonesia)} onChange={(e) => set("has_work_authorization_indonesia", parseBool(e.target.value))}>
          <option value="">Not answered</option><option value="yes">Yes</option><option value="no">No</option>
        </Select>
      </Field>
      <Field label="Willing to relocate">
        <Select value={boolValue(f.willing_to_relocate)} onChange={(e) => set("willing_to_relocate", parseBool(e.target.value))}>
          <option value="">Not answered</option><option value="yes">Yes</option><option value="no">No</option>
        </Select>
      </Field>
    </div>
  );
}

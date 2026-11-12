"use client";

import { Plus } from "lucide-react";
import type { CandidateProfileData, CategoryEvidence } from "@/lib/types";
import { Field, Input } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChipListEditor, LinesEditor } from "./list-editor";
import type { Update } from "./profile-basic";
import { RemoveButton } from "./profile-history";

export function SkillsSection({ data, update }: { data: CandidateProfileData; update: Update }) {
  return (
    <div className="space-y-4">
      {data.skills.map((g, i) => (
        <div key={i} className="space-y-2 rounded-lg border p-4">
          <div className="flex items-center gap-2">
            <Input className="max-w-xs font-medium" value={g.category}
              onChange={(e) => update((d) => ({ ...d, skills: d.skills.map((s, j) => (j === i ? { ...s, category: e.target.value } : s)) }))} />
            <RemoveButton label="Remove skill group" onClick={() => update((d) => ({ ...d, skills: d.skills.filter((_, j) => j !== i) }))} />
          </div>
          <ChipListEditor values={g.skills} placeholder="Add skill"
            onChange={(v) => update((d) => ({ ...d, skills: d.skills.map((s, j) => (j === i ? { ...s, skills: v } : s)) }))} />
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={() => update((d) => ({ ...d, skills: [...d.skills, { category: "New group", skills: [] }] }))}>
        <Plus /> Add skill group
      </Button>
      <Field label="Soft skills">
        <ChipListEditor values={data.soft_skills} onChange={(v) => update((d) => ({ ...d, soft_skills: v }))} />
      </Field>
      <Field label="Languages" hint="Format: Language (Level)">
        <ChipListEditor
          values={data.languages.map((l) => (l.proficiency ? `${l.name} (${l.proficiency})` : l.name))}
          onChange={(v) => update((d) => ({
            ...d,
            languages: v.map((s) => {
              const m = s.match(/^(.+?)\s*(?:\((.+)\))?$/);
              return { name: (m?.[1] ?? s).trim(), proficiency: m?.[2]?.trim() ?? null };
            }),
          }))}
        />
      </Field>
      <Field label="Achievements (one per line)">
        <LinesEditor values={data.achievements} onChange={(v) => update((d) => ({ ...d, achievements: v }))} rows={2} />
      </Field>
    </div>
  );
}

export function CategoriesSection({ data, update, evidence }: { data: CandidateProfileData; update: Update; evidence: CategoryEvidence[] }) {
  const toggle = (cat: string) =>
    update((d) => ({
      ...d,
      target_job_categories: d.target_job_categories.includes(cat)
        ? d.target_job_categories.filter((c) => c !== cat)
        : [...d.target_job_categories, cat],
    }));
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Categories are suggested only when the saved profile contains supporting evidence. Unsupported categories cannot be selected; add real experience or skills first.
      </p>
      <div className="grid gap-2 sm:grid-cols-2">
        {evidence.map((c) => {
          const selected = data.target_job_categories.includes(c.category);
          const disabled = !c.supported && !selected;
          return (
            <label key={c.category} className={`flex items-start gap-3 rounded-lg border p-3 ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"} ${selected ? "border-primary bg-accent/50" : ""}`}>
              <input type="checkbox" className="mt-1" checked={selected} disabled={disabled} onChange={() => toggle(c.category)} />
              <div className="space-y-1">
                <p className="text-sm font-medium">
                  {c.category}{" "}
                  {c.supported ? <Badge variant="success">supported</Badge> : <Badge variant="outline">insufficient evidence</Badge>}
                </p>
                <p className="text-xs text-muted-foreground">{c.evidence.length ? `Evidence: ${c.evidence.join(", ")}` : "No evidence in profile"}</p>
              </div>
            </label>
          );
        })}
      </div>
    </div>
  );
}

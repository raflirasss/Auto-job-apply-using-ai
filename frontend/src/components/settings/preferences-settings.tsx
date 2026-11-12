"use client";

import { useState } from "react";
import { Save } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import type { EmploymentType, Preferences, WorkArrangement } from "@/lib/types";
import { formatIDR } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, LoadingBlock, Spinner } from "@/components/ui/feedback";
import { Field, Input, Switch } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { ChipListEditor } from "./list-editor";
import { CheckGroup, errText, MsgText, type Msg } from "./check-group";

const ARRANGEMENTS: WorkArrangement[] = ["onsite", "hybrid", "remote"];
const EMPLOYMENT: EmploymentType[] = ["full_time", "contract", "part_time", "internship", "freelance", "temporary"];

function Toggle({ checked, label, onChange }: { checked: boolean; label: string; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center gap-3">
      <Switch checked={checked} label={label} onChange={onChange} />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function PreferencesSettings() {
  const req = useAsync(() => api.getPreferences());
  const [draft, setDraft] = useState<Preferences | null>(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<Msg>(null);
  const p = draft ?? req.data;

  if (req.loading && !req.data) return <LoadingBlock />;
  if (req.error || !p) return <Alert tone="error" title="Could not load preferences">{req.error}</Alert>;

  const set = <K extends keyof Preferences>(k: K, v: Preferences[K]) => {
    setDraft({ ...p, [k]: v });
    setMsg(null);
  };
  const num = (k: keyof Preferences) => (e: React.ChangeEvent<HTMLInputElement>) => set(k, Number(e.target.value) as never);

  async function save() {
    if (!p) return;
    setSaving(true);
    try {
      req.setData(await api.savePreferences(p));
      setDraft(null);
      setMsg({ tone: "success", text: "Preferences saved." });
    } catch (e) {
      setMsg({ tone: "error", text: errText(e) });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Location & work arrangement</CardTitle>
          <CardDescription>Jobs outside these locations are rejected by the hard filter.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Field label="Accepted locations"><ChipListEditor values={p.location} onChange={(v) => set("location", v)} placeholder="Add city / area" /></Field>
          <Toggle checked={p.allow_remote} label="Allow fully remote positions"
            onChange={(v) => setDraft({ ...p, allow_remote: v, work_arrangement: v ? p.work_arrangement : p.work_arrangement.filter((w) => w !== "remote") })} />
          <Field label="Work arrangement">
            <CheckGroup options={ARRANGEMENTS} values={p.work_arrangement} onChange={(v) => set("work_arrangement", v)} disabled={(o) => o === "remote" && !p.allow_remote} />
          </Field>
          <Field label="Employment types"><CheckGroup options={EMPLOYMENT} values={p.employment_types} onChange={(v) => set("employment_types", v)} /></Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Salary</CardTitle>
          <CardDescription>Monthly IDR. Annual/weekly salaries are normalised to monthly. Undisclosed salaries never count as meeting the minimum.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <Field label="Minimum monthly salary (IDR)" hint={formatIDR(p.minimum_salary)}>
            <Input type="number" min={0} step={100000} value={p.minimum_salary} onChange={num("minimum_salary")} />
          </Field>
          <Toggle checked={p.allow_undisclosed_salary_review} label="Send undisclosed-salary jobs to review queue" onChange={(v) => set("allow_undisclosed_salary_review", v)} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Matching & applications</CardTitle></CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <Field label="Auto-apply threshold (score)" hint="At or above this score and passing all hard filters: eligible for auto-apply.">
            <Input type="number" min={0} max={100} value={p.minimum_match_score} onChange={num("minimum_match_score")} />
          </Field>
          <Field label="Review threshold (score)" hint="Between this and the auto-apply threshold: review queue. Below: skipped.">
            <Input type="number" min={0} max={100} value={p.review_threshold} onChange={num("review_threshold")} />
          </Field>
          <Field label="Daily application limit"><Input type="number" min={0} max={100} value={p.daily_application_limit} onChange={num("daily_application_limit")} /></Field>
          <Field label="Lookback (days)"><Input type="number" min={1} max={31} value={p.lookback_days} onChange={num("lookback_days")} /></Field>
          <Toggle checked={p.auto_apply} label="Auto-apply (takes effect from Phase 5)" onChange={(v) => set("auto_apply", v)} />
          <Toggle checked={p.avoid_duplicates} label="Avoid duplicate applications" onChange={(v) => set("avoid_duplicates", v)} />
        </CardContent>
      </Card>

      <div className="flex items-center justify-end gap-3">
        <MsgText msg={msg} />
        <Button disabled={!draft || saving} onClick={save}>{saving ? <Spinner /> : <Save />} Save preferences</Button>
      </div>
    </div>
  );
}

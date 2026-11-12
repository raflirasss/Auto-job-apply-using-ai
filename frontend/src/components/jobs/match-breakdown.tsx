import { AlertTriangle, Ban, Check, X } from "lucide-react";
import type { MatchResult } from "@/lib/types";
import { formatDateTime, formatIDR } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const LABELS: Record<keyof MatchResult["components"], string> = {
  skills: "Technical skills",
  experience: "Work experience",
  title: "Job title relevance",
  education: "Education",
  location: "Location & arrangement",
  salary: "Salary",
};

function Bar({ value }: { value: number }) {
  const color = value >= 85 ? "bg-success" : value >= 60 ? "bg-warning" : "bg-destructive";
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${Math.max(2, value)}%` }} />
    </div>
  );
}

function ChipList({ items, tone, empty }: { items: string[]; tone: "success" | "destructive" | "outline"; empty: string }) {
  if (!items.length) return <p className="text-xs text-muted-foreground">{empty}</p>;
  return <div className="flex flex-wrap gap-1.5">{items.map((s) => <Badge key={s} variant={tone}>{s}</Badge>)}</div>;
}

export function MatchBreakdown({ result }: { result: MatchResult }) {
  return (
    <div className="space-y-6">
      {result.hard_filter_failures.length > 0 && (
        <div className="space-y-1.5 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm">
          <p className="flex items-center gap-2 font-medium text-destructive"><Ban className="size-4" /> Rejected by hard filters</p>
          <ul className="list-disc space-y-0.5 pl-5">{result.hard_filter_failures.map((f) => <li key={f.code}>{f.reason}</li>)}</ul>
        </div>
      )}

      <div className="space-y-3">
        <p className="text-sm font-medium">Score breakdown</p>
        {(Object.keys(LABELS) as (keyof MatchResult["components"])[]).map((key) => {
          const c = result.components[key];
          return (
            <div key={key} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>{LABELS[key]} <span className="text-xs text-muted-foreground">({Math.round(c.weight * 100)}%)</span></span>
                <span className="tabular-nums">{c.score.toFixed(0)} → {(c.score * c.weight).toFixed(1)} pts</span>
              </div>
              <Bar value={c.score} />
              <p className="text-xs text-muted-foreground">{c.note}</p>
            </div>
          );
        })}
        <div className="flex justify-between border-t pt-2 text-sm font-semibold"><span>Total</span><span className="tabular-nums">{result.score.toFixed(1)} / 100</span></div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <p className="flex items-center gap-1.5 text-sm font-medium"><Check className="size-4 text-success" /> Matching skills</p>
          <ChipList items={result.matching_skills} tone="success" empty="None detected." />
        </div>
        <div className="space-y-2">
          <p className="flex items-center gap-1.5 text-sm font-medium"><X className="size-4 text-destructive" /> Missing skills</p>
          <ChipList items={result.missing_skills} tone="destructive" empty="None." />
          {result.mandatory_skills.length > 0 && <p className="text-xs text-muted-foreground">Mandatory in listing: {result.mandatory_skills.join(", ")}</p>}
        </div>
      </div>

      <div className="space-y-1.5">
        <p className="text-sm font-medium">Relevant experience</p>
        {result.relevant_experience.length ? (
          <ul className="list-disc space-y-0.5 pl-5 text-sm">{result.relevant_experience.map((e) => <li key={e}>{e}</li>)}</ul>
        ) : <p className="text-xs text-muted-foreground">No past role matched the listing&apos;s skills.</p>}
      </div>

      {result.concerns.length > 0 && (
        <div className="space-y-1.5 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm">
          <p className="flex items-center gap-2 font-medium"><AlertTriangle className="size-4 text-warning" /> Concerns</p>
          <ul className="list-disc space-y-0.5 pl-5">{result.concerns.map((c) => <li key={c}>{c}</li>)}</ul>
        </div>
      )}

      <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
        <div><dt className="text-xs text-muted-foreground">Salary</dt><dd>{result.salary.disclosed ? `${formatIDR(result.salary.min_monthly)} – ${formatIDR(result.salary.max_monthly)} / month` : "Not disclosed"} (min. {formatIDR(result.salary.minimum_required)})</dd></div>
        <div><dt className="text-xs text-muted-foreground">Location</dt><dd>{result.location ?? "Not provided"}</dd></div>
        <div><dt className="text-xs text-muted-foreground">Work arrangement</dt><dd>{result.work_arrangement ?? "Not stated"}{result.work_arrangement_inferred && " (inferred from description)"}</dd></div>
        <div><dt className="text-xs text-muted-foreground">Requirements detected</dt><dd>Education: {result.requirements.education_level}; experience: {result.requirements.min_years ? `${result.requirements.min_years}+ yrs` : "not stated"}{result.requirements.fresh_graduate_ok && "; fresh graduates welcome"}</dd></div>
      </dl>
      <p className="text-xs text-muted-foreground">Engine v{result.engine_version} · analysed {formatDateTime(result.analyzed_at)}</p>
    </div>
  );
}

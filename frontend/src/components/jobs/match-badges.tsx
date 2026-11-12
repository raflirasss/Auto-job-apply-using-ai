import type { ApplicationStatus, Recommendation } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

const REC: Record<Recommendation, { label: string; variant: "success" | "warning" | "outline" | "destructive" }> = {
  auto_apply_eligible: { label: "Auto-apply eligible", variant: "success" },
  review: { label: "Review queue", variant: "warning" },
  skip: { label: "Skip", variant: "outline" },
  reject: { label: "Rejected by filter", variant: "destructive" },
};

export function RecommendationBadge({ value }: { value: Recommendation }) {
  const r = REC[value];
  return <Badge variant={r.variant}>{r.label}</Badge>;
}

export function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <Badge variant="outline">Not analysed</Badge>;
  const variant = score >= 85 ? "success" : score >= 70 ? "warning" : "outline";
  return <Badge variant={variant} className="tabular-nums">Score {score.toFixed(1)}</Badge>;
}

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  discovered: "Discovered",
  analyzed: "Analyzed",
  qualified: "Qualified",
  ready_to_apply: "Ready to apply",
  applied: "Applied",
  pending_action: "Pending action",
  interview: "Interview",
  assessment: "Assessment",
  rejected: "Rejected",
  accepted: "Accepted",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  const variant = status === "rejected" || status === "failed" ? "destructive"
    : status === "applied" || status === "interview" || status === "accepted" ? "success"
    : status === "qualified" ? "default" : "outline";
  return <Badge variant={variant}>{STATUS_LABELS[status]}</Badge>;
}

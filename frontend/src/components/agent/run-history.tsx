import { History } from "lucide-react";
import type { AgentRunItem } from "@/lib/types-ext";
import { formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/feedback";
import { Badge } from "@/components/ui/badge";

const STATUS: Record<AgentRunItem["status"], "success" | "destructive" | "outline" | "default"> = {
  succeeded: "success", failed: "destructive", cancelled: "outline", running: "default",
};

function summaryText(s: Record<string, unknown> | null): string {
  if (!s) return "";
  const n = (k: string) => (typeof s[k] === "number" ? (s[k] as number) : 0);
  return `analysed ${n("analyzed")} · documents ${n("documents_generated")} · auto-applied ${n("auto_applied")} · waiting for you ${n("awaiting_manual_apply")}`;
}

export function RunHistory({ runs }: { runs: AgentRunItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Execution history</CardTitle>
        <CardDescription>Scheduled and manual runs, including retries.</CardDescription>
      </CardHeader>
      <CardContent>
        {runs.length === 0 ? (
          <EmptyState icon={History} title="No runs yet" description="Click Run now, or start the agent to run daily." />
        ) : (
          <ul className="divide-y">
            {runs.map((r) => (
              <li key={r.id} className="space-y-1 py-2.5 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">#{r.id}</span>
                  <Badge variant={STATUS[r.status]}>{r.status}</Badge>
                  <Badge variant="outline">{r.trigger}{r.attempt > 1 ? ` · retry ${r.attempt - 1}` : ""}</Badge>
                  <span className="ml-auto text-xs text-muted-foreground">{r.started_at ? formatDateTime(r.started_at) : ""}</span>
                </div>
                {r.summary && <p className="text-xs text-muted-foreground">{summaryText(r.summary)}</p>}
                {Array.isArray(r.summary?.notes) && (r.summary!.notes as string[]).length > 0 && (
                  <ul className="list-disc pl-5 text-xs">{(r.summary!.notes as string[]).map((n) => <li key={n}>{n}</li>)}</ul>
                )}
                {r.error && <p className="text-xs text-destructive">{r.error}</p>}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

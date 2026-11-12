"use client";

import { useCallback } from "react";
import { Activity, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import { formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, EmptyState, LoadingBlock, PageHeader } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AgentControls } from "@/components/agent/agent-controls";
import { RunHistory } from "@/components/agent/run-history";

export default function AgentPage() {
  const events = useAsync(() => api.events(200));
  const status = useAsync(() => api.agentStatus());
  const history = useAsync(() => api.agentRuns(30));
  const { reload: reloadStatus } = status;
  const { reload: reloadEvents } = events;
  const { reload: reloadHistory } = history;
  const refresh = useCallback(() => {
    void reloadStatus();
    void reloadEvents();
    void reloadHistory();
  }, [reloadStatus, reloadEvents, reloadHistory]);

  return (
    <>
      <PageHeader
        title="Agent Control"
        description="Start, pause and monitor the job hunting agent."
        actions={<Button variant="outline" size="sm" onClick={refresh}><RefreshCw /> Refresh</Button>}
      />
      <div className="space-y-6">
        {status.error && <Alert tone="error">{status.error}</Alert>}
        {status.data ? <AgentControls status={status.data} onChange={refresh} /> : !status.error && <LoadingBlock />}
        {history.data && <RunHistory runs={history.data.runs} />}

        <Card>
          <CardHeader>
            <CardTitle>Execution log</CardTitle>
            <CardDescription>Events stored by the backend. Personal data and secrets are excluded.</CardDescription>
          </CardHeader>
          <CardContent>
            {events.error && <Alert tone="error">{events.error}</Alert>}
            {events.loading && !events.data && <LoadingBlock />}
            {events.data?.events.length === 0 && <EmptyState icon={Activity} title="No events" description="Nothing has been logged yet." />}
            {events.data && events.data.events.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-xs text-muted-foreground">
                    <tr><th className="py-2 pr-4 font-medium">Time</th><th className="py-2 pr-4 font-medium">Category</th><th className="py-2 font-medium">Message</th></tr>
                  </thead>
                  <tbody className="divide-y">
                    {events.data.events.map((e) => (
                      <tr key={e.id}>
                        <td className="whitespace-nowrap py-2 pr-4 text-muted-foreground">{formatDateTime(e.created_at)}</td>
                        <td className="py-2 pr-4"><Badge variant={e.level === "error" ? "destructive" : "outline"}>{e.category}</Badge></td>
                        <td className="py-2">{e.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

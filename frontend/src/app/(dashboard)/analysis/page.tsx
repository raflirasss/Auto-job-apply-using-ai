import { Suspense } from "react";
import { LoadingBlock } from "@/components/ui/feedback";
import { AnalysisView } from "@/components/jobs/analysis-view";

export default function AnalysisPage() {
  return (
    <Suspense fallback={<LoadingBlock />}>
      <AnalysisView />
    </Suspense>
  );
}

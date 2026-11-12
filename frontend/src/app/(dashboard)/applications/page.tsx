import { Suspense } from "react";
import { LoadingBlock } from "@/components/ui/feedback";
import { Tracker } from "@/components/applications/tracker";

export default function ApplicationsPage() {
  return (
    <Suspense fallback={<LoadingBlock />}>
      <Tracker />
    </Suspense>
  );
}

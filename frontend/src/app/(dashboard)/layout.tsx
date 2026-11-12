import { Suspense } from "react";
import { AppShell } from "@/components/app-shell";
import { LoadingBlock } from "@/components/ui/feedback";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<LoadingBlock />}>
      <AppShell>{children}</AppShell>
    </Suspense>
  );
}

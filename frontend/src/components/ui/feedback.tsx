import * as React from "react";
import { AlertTriangle, CheckCircle2, Info, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

type Tone = "info" | "success" | "warning" | "error";

const toneStyles: Record<Tone, string> = {
  info: "border-primary/30 bg-accent text-accent-foreground",
  success: "border-success/30 bg-success/10 text-success",
  warning: "border-warning/40 bg-warning/10 text-foreground",
  error: "border-destructive/30 bg-destructive/10 text-destructive",
};
const toneIcon = { info: Info, success: CheckCircle2, warning: AlertTriangle, error: XCircle };

export function Alert({ tone = "info", title, children, className }: { tone?: Tone; title?: string; children?: React.ReactNode; className?: string }) {
  const Icon = toneIcon[tone];
  return (
    <div role={tone === "error" ? "alert" : "status"} className={cn("flex gap-3 rounded-lg border p-3 text-sm animate-fade-in", toneStyles[tone], className)}>
      <Icon className="mt-0.5 size-4 shrink-0" />
      <div className="space-y-1">
        {title && <p className="font-medium">{title}</p>}
        {children && <div className="text-foreground/80">{children}</div>}
      </div>
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("size-4 animate-spin", className)} aria-label="Loading" />;
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 p-8 text-sm text-muted-foreground">
      <Spinner /> {label}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, children }: { icon: React.ElementType; title: string; description: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed p-10 text-center animate-fade-in">
      <div className="rounded-full bg-muted p-3">
        <Icon className="size-5 text-muted-foreground" />
      </div>
      <div className="space-y-1">
        <p className="font-medium">{title}</p>
        <p className="mx-auto max-w-md text-sm text-muted-foreground">{description}</p>
      </div>
      {children}
    </div>
  );
}

export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}

"use client";

import { CheckCircle2, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/feedback";

export function SaveBar({
  dirty,
  saving,
  message,
  confirmed,
  onSave,
}: {
  dirty: boolean;
  saving: "save" | "confirm" | null;
  message: { tone: "success" | "error"; text: string } | null;
  confirmed: boolean;
  onSave: (confirm: boolean) => void;
}) {
  return (
    <div className="fixed inset-x-0 bottom-0 z-20 border-t bg-background/90 backdrop-blur md:left-60">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-8">
        <div className="text-sm">
          {message ? (
            <span className={message.tone === "error" ? "text-destructive" : "text-success"}>{message.text}</span>
          ) : (
            <span className="text-muted-foreground">{dirty ? "Unsaved changes" : "All changes saved"}</span>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" disabled={!dirty || saving !== null} onClick={() => onSave(false)}>
            {saving === "save" ? <Spinner /> : <Save />} Save
          </Button>
          <Button disabled={saving !== null || (!dirty && confirmed)} onClick={() => onSave(true)} title="Confirms that all data is accurate">
            {saving === "confirm" ? <Spinner /> : <CheckCircle2 />} Save &amp; confirm
          </Button>
        </div>
      </div>
    </div>
  );
}

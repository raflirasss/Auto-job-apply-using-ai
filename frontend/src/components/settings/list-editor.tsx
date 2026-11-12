"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";
import { Input } from "@/components/ui/form";
import { Button } from "@/components/ui/button";

/** Editable list of short strings rendered as removable chips. */
export function ChipListEditor({ values, onChange, placeholder }: { values: string[]; onChange: (v: string[]) => void; placeholder?: string }) {
  const [draft, setDraft] = useState("");
  function add() {
    const v = draft.trim();
    if (v && !values.some((x) => x.toLowerCase() === v.toLowerCase())) onChange([...values, v]);
    setDraft("");
  }
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {values.map((v) => (
          <span key={v} className="inline-flex items-center gap-1 rounded-full bg-accent px-2.5 py-0.5 text-xs text-accent-foreground">
            {v}
            <button type="button" aria-label={`Remove ${v}`} className="cursor-pointer opacity-60 hover:opacity-100" onClick={() => onChange(values.filter((x) => x !== v))}>
              <X className="size-3" />
            </button>
          </span>
        ))}
        {values.length === 0 && <span className="text-xs text-muted-foreground">None</span>}
      </div>
      <div className="flex gap-2">
        <Input
          value={draft}
          placeholder={placeholder ?? "Add item"}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              add();
            }
          }}
        />
        <Button type="button" variant="outline" size="icon" aria-label="Add" onClick={add}>
          <Plus />
        </Button>
      </div>
    </div>
  );
}

/** Multi-line text where each line is one list item (e.g. responsibilities). */
export function LinesEditor({ values, onChange, rows = 4 }: { values: string[]; onChange: (v: string[]) => void; rows?: number }) {
  return (
    <textarea
      className="min-h-20 w-full rounded-md border border-input bg-card px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      rows={rows}
      value={values.join("\n")}
      onChange={(e) => onChange(e.target.value.split("\n"))}
      onBlur={() => onChange(values.map((v) => v.trim()).filter(Boolean))}
    />
  );
}

"use client";

export function CheckGroup<T extends string>({
  options,
  values,
  onChange,
  disabled,
}: {
  options: T[];
  values: T[];
  onChange: (v: T[]) => void;
  disabled?: (o: T) => boolean;
}) {
  const toggle = (v: T) => (values.includes(v) ? values.filter((x) => x !== v) : [...values, v]);
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => (
        <label key={o} className={`flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm ${disabled?.(o) ? "opacity-50" : "cursor-pointer"}`}>
          <input type="checkbox" checked={values.includes(o)} disabled={disabled?.(o)} onChange={() => onChange(toggle(o))} />
          {o.replace("_", " ")}
        </label>
      ))}
    </div>
  );
}

export type Msg = { tone: "success" | "error"; text: string } | null;

export function MsgText({ msg }: { msg: Msg }) {
  if (!msg) return null;
  return <span className={`text-sm ${msg.tone === "error" ? "text-destructive" : "text-success"}`}>{msg.text}</span>;
}

export const errText = (e: unknown) => (e instanceof Error ? e.message : "Save failed");

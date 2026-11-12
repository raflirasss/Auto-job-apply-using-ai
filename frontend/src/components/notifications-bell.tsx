"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell } from "lucide-react";
import { api } from "@/lib/api";
import type { NotificationItem } from "@/lib/types-ext";
import { formatDateTime } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const POLL_MS = 60_000;

export function NotificationsBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    const load = () => api.notifications().then((r) => {
      if (alive) { setItems(r.notifications); setUnread(r.unread); }
    }).catch(() => undefined);
    void load();
    const t = setInterval(load, POLL_MS);
    return () => { alive = false; clearInterval(t); };
  }, []);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && unread) {
      await api.markNotificationsRead().catch(() => undefined);
      setUnread(0);
    }
  }

  return (
    <div className="relative" ref={ref}>
      <Button variant="ghost" size="icon" aria-label={`Notifications${unread ? ` (${unread} unread)` : ""}`} onClick={toggle}>
        <Bell />
        {unread > 0 && <span className="absolute right-1 top-1 flex size-4 items-center justify-center rounded-full bg-destructive text-[10px] text-white">{unread > 9 ? "9+" : unread}</span>}
      </Button>
      {open && (
        <div className="absolute bottom-11 left-0 z-50 w-80 rounded-xl border bg-card p-2 shadow-xl animate-fade-in">
          <p className="px-2 py-1 text-xs font-medium text-muted-foreground">Notifications</p>
          {items.length === 0 ? <p className="p-3 text-sm text-muted-foreground">Nothing yet.</p> : (
            <ul className="max-h-96 overflow-y-auto">
              {items.map((n) => {
                const body = (
                  <div className="rounded-md p-2 text-sm hover:bg-muted">
                    <p className="font-medium">{n.title}</p>
                    <p className="line-clamp-3 text-xs text-muted-foreground">{n.body}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">{formatDateTime(n.created_at)}</p>
                  </div>
                );
                return <li key={n.id}>{n.link ? <Link href={n.link} onClick={() => setOpen(false)}>{body}</Link> : body}</li>;
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

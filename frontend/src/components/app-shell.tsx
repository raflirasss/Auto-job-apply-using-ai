"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import {
  Bot,
  Briefcase,
  FileText,
  KanbanSquare,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Search,
  Settings,
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { NotificationsBell } from "@/components/notifications-bell";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/jobs", label: "Job Discovery", icon: Search },
  { href: "/applications", label: "Applications", icon: KanbanSquare },
  { href: "/analysis", label: "AI Analysis", icon: Sparkles },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/agent", label: "Agent Control", icon: Bot },
  { href: "/settings", label: "Settings", icon: Settings },
];

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  // eslint-disable-next-line react-hooks/set-state-in-effect -- hydration guard for theme icon
  useEffect(() => setMounted(true), []);
  const dark = mounted && resolvedTheme === "dark";
  return (
    <Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={() => setTheme(dark ? "light" : "dark")}>
      {dark ? <Sun /> : <Moon />}
    </Button>
  );
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-0.5">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              active ? "bg-accent font-medium text-accent-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  async function logout() {
    await api.logout().catch(() => undefined);
    // Full reload on auth change to drop all cached client state (including the preserved Activity routes).
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/login";
  }

  const brand = (
    <div className="flex items-center gap-2 px-3 py-1">
      <div className="rounded-lg bg-primary p-1.5 text-primary-foreground">
        <Briefcase className="size-4" />
      </div>
      <span className="font-semibold tracking-tight">AI Job Hunter</span>
    </div>
  );

  const footer = (
    <div className="mt-auto flex items-center justify-between border-t pt-3">
      <div className="flex items-center"><ThemeToggle /><NotificationsBell /></div>
      <Button variant="ghost" size="sm" onClick={logout}>
        <LogOut /> Sign out
      </Button>
    </div>
  );

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col gap-6 border-r bg-card p-3 md:flex">
        {brand}
        <NavLinks />
        {footer}
      </aside>

      {open && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 flex w-64 flex-col gap-6 bg-card p-3 shadow-xl animate-fade-in">
            <div className="flex items-center justify-between">
              {brand}
              <Button variant="ghost" size="icon" aria-label="Close menu" onClick={() => setOpen(false)}>
                <X />
              </Button>
            </div>
            <NavLinks onNavigate={() => setOpen(false)} />
            {footer}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b bg-background/80 px-4 backdrop-blur md:hidden">
          <Button variant="ghost" size="icon" aria-label="Open menu" onClick={() => setOpen(true)}>
            <Menu />
          </Button>
          {brand}
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}

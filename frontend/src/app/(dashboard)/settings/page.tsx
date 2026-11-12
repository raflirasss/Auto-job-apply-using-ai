"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/ui/feedback";
import { ProfileSettings } from "@/components/settings/profile-settings";
import { PreferencesSettings } from "@/components/settings/preferences-settings";
import { SystemSettings } from "@/components/settings/system-settings";
import { SourcesSettings } from "@/components/sources/sources-settings";

const TABS = [
  { id: "profile", label: "Candidate profile" },
  { id: "preferences", label: "Job preferences" },
  { id: "sources", label: "Sources & email" },
  { id: "system", label: "AI & scheduler" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function SettingsPage() {
  const [tab, setTab] = useState<TabId>("profile");
  return (
    <>
      <PageHeader title="Settings" description="Candidate profile, job preferences and system configuration." />
      <div role="tablist" className="mb-6 inline-flex rounded-lg border bg-muted p-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "cursor-pointer rounded-md px-3 py-1.5 text-sm transition-colors",
              tab === t.id ? "bg-card font-medium shadow-sm" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "profile" && <ProfileSettings />}
      {tab === "preferences" && <PreferencesSettings />}
      {tab === "sources" && <SourcesSettings />}
      {tab === "system" && <SystemSettings />}
    </>
  );
}

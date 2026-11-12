"use client";

import { useState } from "react";
import { FileUp } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import type { CandidateProfileData, CVImportResult } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, EmptyState, LoadingBlock } from "@/components/ui/feedback";
import { Badge } from "@/components/ui/badge";
import { CVUpload } from "./cv-upload";
import { FactsSection, PersonalSection } from "./profile-basic";
import { EducationSection, ExperienceSection } from "./profile-history";
import { CategoriesSection, SkillsSection } from "./profile-skills";
import { CertProjectSection } from "./profile-extras";
import { SaveBar } from "./save-bar";

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle>{description && <CardDescription>{description}</CardDescription>}</CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export function ProfileSettings() {
  const profileReq = useAsync(() => api.getProfile());
  const categoriesReq = useAsync(() => api.categories());
  const [draft, setDraft] = useState<CandidateProfileData | null>(null);
  const [saving, setSaving] = useState<"save" | "confirm" | null>(null);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const profile = profileReq.data?.profile ?? null;
  const data = draft ?? profile?.data ?? null;

  const update = (fn: (d: CandidateProfileData) => CandidateProfileData) => {
    if (!data) return;
    setDraft(fn(data));
    setMessage(null);
  };

  const onImported = (r: CVImportResult) => {
    profileReq.setData({ profile: r.profile });
    setDraft(null);
    void categoriesReq.reload();
  };

  async function save(confirm: boolean) {
    if (!data) return;
    setSaving(confirm ? "confirm" : "save");
    setMessage(null);
    try {
      const r = await api.saveProfile(data, confirm);
      profileReq.setData({ profile: r.profile });
      setDraft(null);
      void categoriesReq.reload();
      setMessage({ tone: "success", text: confirm ? "Profile confirmed." : `Saved as version ${r.profile.version}.` });
    } catch (err) {
      setMessage({ tone: "error", text: err instanceof Error ? err.message : "Save failed" });
    } finally {
      setSaving(null);
    }
  }

  if (profileReq.loading && !profileReq.data) return <LoadingBlock />;
  if (profileReq.error) return <Alert tone="error" title="Could not load profile">{profileReq.error}</Alert>;

  const missing = profile?.data.missing_information ?? [];
  const critical = missing.filter((m) => m.critical);

  return (
    <div className="space-y-6 pb-24">
      <Section title="CV import" description="The original CV is stored unchanged. Extraction is deterministic: nothing is invented, and unknown facts become questions.">
        {!profile ? (
          <EmptyState icon={FileUp} title="No CV imported yet" description="Upload your CV (text-based PDF or DOCX). A draft profile will be extracted for review.">
            <CVUpload hasProfile={false} onImported={onImported} />
          </EmptyState>
        ) : (
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="text-sm">
              Version {profile.version} · updated {formatDateTime(profile.updated_at)}{" "}
              {profile.is_confirmed ? <Badge variant="success">Confirmed</Badge> : <Badge variant="warning">Draft, needs review</Badge>}
            </p>
            <CVUpload hasProfile onImported={onImported} />
          </div>
        )}
      </Section>

      {profile && data && (
        <>
          {missing.length > 0 && (
            <Alert tone={critical.length ? "warning" : "info"} title={`${missing.length} open question(s), ${critical.length} critical`}>
              <ul className="mt-1 list-disc space-y-0.5 pl-4">
                {missing.map((m) => (
                  <li key={m.field}>{m.critical && <strong>Required: </strong>}{m.question}</li>
                ))}
              </ul>
              <p className="mt-2 text-xs">Answer them in the fields below and save. The list is recalculated from saved data.</p>
            </Alert>
          )}
          <Section title="Personal information"><PersonalSection data={data} update={update} /></Section>
          <Section title="Application facts" description="Used to answer common form questions. Left empty unless you provide them.">
            <FactsSection data={data} update={update} />
          </Section>
          <Section title="Education"><EducationSection data={data} update={update} /></Section>
          <Section title="Work experience"><ExperienceSection data={data} update={update} /></Section>
          <Section title="Skills, languages & achievements"><SkillsSection data={data} update={update} /></Section>
          <Section title="Certifications & projects"><CertProjectSection data={data} update={update} /></Section>
          <Section title="Target job categories" description="Evidence is computed from the last saved version.">
            {categoriesReq.data ? <CategoriesSection data={data} update={update} evidence={categoriesReq.data.categories} /> : <LoadingBlock />}
          </Section>
          <SaveBar dirty={draft !== null} saving={saving} message={message} confirmed={profile.is_confirmed} onSave={save} />
        </>
      )}
    </div>
  );
}

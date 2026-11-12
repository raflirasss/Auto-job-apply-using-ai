export interface DocumentItem {
  id: number;
  application_id: number | null;
  kind: "resume" | "cover_letter" | "email" | "answers";
  format: "pdf" | "docx" | "txt" | "json";
  version: number;
  filename: string;
  created_at: string;
  job?: { job_id: number; title: string; company: string | null } | null;
}

export interface GenerateResult {
  application_id: number;
  version: number;
  language: "en" | "id";
  listing_language: "en" | "id";
  template: string;
  keywords_used: string[];
  missing_answers: string[];
  documents: DocumentItem[];
}

export interface ApplyAttemptItem {
  id: number;
  application_id: number;
  mode: "assisted" | "auto";
  outcome: "running" | "submitted" | "awaiting_user" | "stopped" | "failed";
  stop_reason: string | null;
  detail: string | null;
  fields_filled: string[];
  fields_unresolved: string[];
  has_screenshot: boolean;
  started_at: string;
  finished_at: string | null;
}

export type ApplyMode = "assisted" | "auto" | "email";

export interface ApplyStatus {
  allowed_modes: ApplyMode[];
  policy_note: string;
  apply_email: string | null;
  blocked_reason: Record<ApplyMode, string | null>;
  has_documents: boolean;
  browser_busy: boolean;
  attempts: ApplyAttemptItem[];
}

export interface AgentRunItem {
  id: number;
  trigger: string;
  status: "running" | "succeeded" | "failed" | "cancelled";
  attempt: number;
  started_at: string | null;
  finished_at: string | null;
  summary: Record<string, unknown> | null;
  error: string | null;
}

export interface AgentStatus {
  scheduler_running: boolean;
  enabled: boolean;
  paused: boolean;
  run_time: string;
  timezone: string;
  next_run_time: string | null;
  active_run: AgentRunItem | null;
  last_run: AgentRunItem | null;
}

export interface RssFeed { name: string; url: string }

export interface SourcesConfig {
  rss: { enabled: boolean; feeds: RssFeed[] };
  telegram: { enabled: boolean; method: "api" | "preview"; channels: string[]; messages_per_channel: number; api_id: number | null };
  ats: { enabled: boolean; lever: string[]; greenhouse: string[] };
  fetch_interval_hours: number;
}

export interface SourceReport { fetched: number; created: number; updated: number; failed: number; errors: string[]; notes: string[] }

export interface SmtpStatus {
  host?: string;
  port?: number;
  use_ssl?: boolean;
  username?: string;
  from_name?: string | null;
  password_set: boolean;
}

export interface SourcesStatus {
  config: SourcesConfig;
  telegram_connected: boolean;
  smtp: SmtpStatus;
  discovery_running: boolean;
  last_report: Record<string, SourceReport>;
}

export interface NotificationItem {
  id: number;
  level: "info" | "success" | "warning" | "error";
  title: string;
  body: string;
  link: string | null;
  read: boolean;
  created_at: string;
}

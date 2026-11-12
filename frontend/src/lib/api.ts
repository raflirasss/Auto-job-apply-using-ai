import type {
  AIConfig,
  CandidateProfile,
  CandidateProfileData,
  CategoryEvidence,
  CVFile,
  CVImportResult,
  Overview,
  Preferences,
  SchedulerConfig,
  AgentEvent,
  JobsResponse,
  ManualJobIn,
  JobImportResult,
  Job,
  ApplicationStatus,
} from "./types";
import type {
  AgentRunItem, AgentStatus, ApplyMode, ApplyStatus, DocumentItem, GenerateResult, NotificationItem, SmtpStatus,
  SourcesConfig, SourcesStatus,
} from "./types-ext";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function detailToMessage(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: (string | number)[]; msg?: string }) =>
        `${(d.loc ?? []).filter((p) => p !== "body").join(".")}: ${d.msg ?? "invalid"}`)
      .join("; ");
  }
  return "Request failed";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { credentials: "same-origin", cache: "no-store", ...init });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth/")) {
    // Session expired: non-component code, so hard navigation is the only option here.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/login";
  }
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    let isJson = false;
    try {
      message = detailToMessage((await res.json()).detail);
      isJson = true;
    } catch {
      /* non-JSON error body */
    }
    // FastAPI always answers with JSON. A non-JSON 5xx comes from the Next.js proxy: the backend is not reachable.
    if (!isJson && res.status >= 500) {
      message = "The backend server is not running or not reachable (port 8000). Restart the app with start.ps1.";
    }
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  login: (password: string) => request<{ ok: boolean }>("/api/auth/login", json("POST", { password })),
  logout: () => request<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
  me: () => request<{ authenticated: boolean }>("/api/auth/me"),

  overview: () => request<Overview>("/api/dashboard/overview"),
  events: (limit = 100, runId?: number) =>
    request<{ events: AgentEvent[] }>(`/api/agent/events?limit=${limit}${runId ? `&run_id=${runId}` : ""}`),
  agentStatus: () => request<AgentStatus>("/api/agent/status"),
  agentAction: (action: "start" | "pause" | "resume") => request<AgentStatus>(`/api/agent/${action}`, { method: "POST" }),
  agentRunNow: () => request<{ run_id: number }>("/api/agent/run", { method: "POST" }),
  agentRuns: (limit = 30) => request<{ runs: AgentRunItem[] }>(`/api/agent/runs?limit=${limit}`),
  notifications: () => request<{ unread: number; notifications: NotificationItem[] }>("/api/agent/notifications"),
  markNotificationsRead: () => request<{ ok: boolean }>("/api/agent/notifications/read", { method: "POST" }),

  sources: () => request<SourcesStatus>("/api/sources"),
  saveSources: (cfg: SourcesConfig) => request<SourcesStatus>("/api/sources", json("PUT", cfg)),
  runDiscovery: () => request<{ started: boolean }>("/api/sources/run", { method: "POST" }),
  saveSmtp: (body: { host: string; port: number; use_ssl: boolean; username: string; from_name: string | null; password?: string }) =>
    request<SmtpStatus>("/api/sources/smtp", json("PUT", body)),
  testSmtp: () => request<{ ok: boolean }>("/api/sources/smtp/test", { method: "POST" }),
  telegramSendCode: (api_id: number, api_hash: string, phone: string) =>
    request<{ sent: boolean }>("/api/sources/telegram/send-code", json("POST", { api_id, api_hash, phone })),
  telegramVerify: (code: string, password?: string) =>
    request<{ connected: boolean }>("/api/sources/telegram/verify", json("POST", { code, password: password || null })),
  telegramDisconnect: () => request<{ connected: boolean }>("/api/sources/telegram/disconnect", { method: "POST" }),

  documents: () => request<{ documents: DocumentItem[] }>("/api/documents"),
  generateDocuments: (jobId: number, template?: string, language?: "en" | "id") =>
    request<GenerateResult>(`/api/jobs/${jobId}/documents`, json("POST", { template: template ?? null, language: language ?? null })),
  templates: () => request<{ templates: { key: string; name: string }[] }>("/api/documents/templates"),
  applyStatus: (jobId: number) => request<ApplyStatus>(`/api/jobs/${jobId}/apply/status`),
  apply: (jobId: number, mode: ApplyMode) =>
    request<{ started: boolean; mode: string; note: string }>(`/api/jobs/${jobId}/apply`, json("POST", { mode })),

  jobs: (limit = 200) => request<JobsResponse>(`/api/jobs?limit=${limit}`),
  importJob: (body: ManualJobIn) => request<JobImportResult>("/api/jobs/import", json("POST", body)),
  job: (id: number) => request<{ job: Job }>(`/api/jobs/${id}`),
  analyzeJob: (id: number, withAI = false) => request<{ job: Job }>(`/api/jobs/${id}/analyze`, json("POST", { with_ai: withAI })),
  analyzeAll: (reanalyze = false) =>
    request<{ analyzed: number; by_recommendation: Record<string, number> }>("/api/jobs/analyze", json("POST", { reanalyze })),
  setApplicationStatus: (id: number, status: ApplicationStatus, note?: string, confirmation?: string) =>
    request<{ job: Job }>(`/api/jobs/${id}/application/status`, json("PUT", { status, note: note ?? null, confirmation: confirmation ?? null })),

  getProfile: () => request<{ profile: CandidateProfile | null }>("/api/candidate/profile"),
  saveProfile: (data: CandidateProfileData, confirm: boolean) =>
    request<{ profile: CandidateProfile }>("/api/candidate/profile", json("PUT", { data, confirm })),
  categories: () => request<{ categories: CategoryEvidence[] }>("/api/candidate/profile/categories"),
  uploadCV: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<CVImportResult>("/api/candidate/cv", { method: "POST", body: form });
  },
  listCVs: () => request<{ files: CVFile[] }>("/api/candidate/cv"),

  getPreferences: () => request<Preferences>("/api/settings/preferences"),
  savePreferences: (p: Preferences) => request<Preferences>("/api/settings/preferences", json("PUT", p)),
  getScheduler: () => request<SchedulerConfig>("/api/settings/scheduler"),
  saveScheduler: (s: SchedulerConfig) => request<SchedulerConfig>("/api/settings/scheduler", json("PUT", s)),
  getAI: () => request<AIConfig>("/api/settings/ai"),
  saveAI: (body: { base_url: string | null; model: string | null; api_key?: string; clear_api_key?: boolean }) =>
    request<AIConfig>("/api/settings/ai", json("PUT", body)),
};

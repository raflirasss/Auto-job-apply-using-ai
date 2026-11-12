export interface PersonalInfo {
  full_name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  websites: string[];
}

export interface Education {
  institution: string;
  degree: string | null;
  field_of_study: string | null;
  gpa: number | null;
  gpa_scale: number | null;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  is_expected: boolean;
}

export interface WorkExperience {
  company: string;
  title: string | null;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  employment_type: string | null;
  responsibilities: string[];
}

export interface SkillGroup { category: string; skills: string[] }
export interface Language { name: string; proficiency: string | null }
export interface Certification { name: string; issuer: string | null; date: string | null; credential_url: string | null }
export interface Project { name: string; description: string | null; technologies: string[]; url: string | null }
export interface MissingInfo { field: string; question: string; critical: boolean }

export interface ApplicationFacts {
  expected_salary_monthly_idr: number | null;
  notice_period: string | null;
  availability_date: string | null;
  willing_to_relocate: boolean | null;
  has_work_authorization_indonesia: boolean | null;
}

export interface CandidateProfileData {
  schema_version: 1;
  personal: PersonalInfo;
  summary: string | null;
  education: Education[];
  experience: WorkExperience[];
  skills: SkillGroup[];
  soft_skills: string[];
  languages: Language[];
  certifications: Certification[];
  projects: Project[];
  achievements: string[];
  target_job_categories: string[];
  application_facts: ApplicationFacts;
  missing_information: MissingInfo[];
}

export interface CandidateProfile {
  id: number;
  version: number;
  is_confirmed: boolean;
  source_cv_id: number | null;
  data: CandidateProfileData;
  updated_at: string;
}

export interface CVFile {
  id: number;
  original_filename: string;
  sha256: string;
  mime_type: string;
  size_bytes: number;
  page_count: number | null;
  uploaded_at: string;
}

export interface CVImportResult {
  cv_file: CVFile;
  profile: CandidateProfile;
  duplicate_file: boolean;
  extraction_warnings: string[];
}

export interface CategoryEvidence { category: string; evidence: string[]; supported: boolean; selected: boolean }

export type WorkArrangement = "onsite" | "hybrid" | "remote";
export type EmploymentType = "full_time" | "part_time" | "contract" | "internship" | "freelance" | "temporary";

export interface Preferences {
  job_sources: string[];
  location: string[];
  work_arrangement: WorkArrangement[];
  employment_types: EmploymentType[];
  minimum_salary: number;
  salary_currency: "IDR";
  salary_period: "monthly";
  allow_undisclosed_salary_review: boolean;
  search_frequency: "daily";
  lookback_days: number;
  minimum_match_score: number;
  review_threshold: number;
  auto_apply: boolean;
  daily_application_limit: number;
  avoid_duplicates: boolean;
  allow_remote: boolean;
}

export interface SchedulerConfig {
  enabled: boolean;
  run_time: string;
  timezone: "Asia/Jakarta";
  max_retries: number;
  paused: boolean;
}

export interface AIConfig {
  base_url: string | null;
  model: string | null;
  api_key_masked: string | null;
  api_key_source: "environment" | "dashboard" | "none";
  configured: boolean;
}

export interface Job {
  id: number;
  source: string;
  external_id: string;
  canonical_url: string;
  title: string;
  company: string | null;
  location: string | null;
  work_arrangement: WorkArrangement | null;
  employment_type: EmploymentType | null;
  salary_min_monthly: number | null;
  salary_max_monthly: number | null;
  salary_currency: string | null;
  salary_disclosed: boolean;
  description: string | null;
  application_url: string | null;
  apply_email: string | null;
  source_note: string | null;
  posted_at: string | null;
  discovered_at: string;
  is_available: boolean;
  match_score: number | null;
  match_details: MatchResult | null;
  application: JobApplication | null;
}

export type ApplicationStatus =
  | "discovered" | "analyzed" | "qualified" | "ready_to_apply" | "applied" | "pending_action"
  | "interview" | "assessment" | "rejected" | "accepted" | "failed";

export interface JobApplication {
  id: number;
  status: ApplicationStatus;
  applied_at: string | null;
  submission_confirmation: string | null;
  notes: string | null;
  pending_action: string | null;
  error_details: string | null;
}

export type Recommendation = "auto_apply_eligible" | "review" | "skip" | "reject";

export interface MatchComponent { score: number; weight: number; note: string }

export interface MatchResult {
  engine_version: string;
  score: number;
  components: Record<"skills" | "experience" | "title" | "education" | "location" | "salary", MatchComponent>;
  matching_skills: string[];
  missing_skills: string[];
  mandatory_skills: string[];
  relevant_experience: string[];
  concerns: string[];
  hard_filter_failures: { code: string; reason: string }[];
  passed_hard_filters: boolean;
  salary: { disclosed: boolean; min_monthly: number | null; max_monthly: number | null; minimum_required: number };
  location: string | null;
  work_arrangement: string | null;
  work_arrangement_inferred: boolean;
  requirements: { min_years: number | null; education_level: string; fresh_graduate_ok: boolean };
  recommendation: Recommendation;
  suggested_status: string;
  analyzed_at: string;
  ai_explanation: string | null;
  ai_error: string | null;
  ai_model?: string;
}

export interface JobsResponse { jobs: Job[] }

export interface ManualJobIn {
  job_url: string;
  title: string;
  company: string | null;
  location: string | null;
  work_arrangement: WorkArrangement | null;
  employment_type: EmploymentType | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_period: "monthly" | "annual" | "weekly" | "daily";
  salary_disclosed: boolean;
  description: string | null;
}

export interface JobImportResult { job: Job; duplicate: boolean; note: string }

export interface AgentEvent { id: number; level: string; category: string; message: string; created_at: string }

export interface Overview {
  jobs_discovered: number;
  qualified: number;
  applications_submitted: number;
  pending: number;
  interviews: number;
  rejections: number;
  filtered_out: number;
  success_rate: number | null;
  status_counts: Record<string, number>;
  recent_activity: AgentEvent[];
}

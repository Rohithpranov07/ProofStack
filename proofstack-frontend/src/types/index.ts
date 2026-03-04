/* ---- Shared sub-types (mirrors backend Pydantic models) ---- */

export interface SkillItem {
  name: string;
  years: number;
}

export interface ProjectItem {
  name: string;
}

export interface ExperienceItem {
  company: string;
  start_date: string;
  end_date: string;
}

export interface ResumeStructured {
  skills: SkillItem[];
  projects: ProjectItem[];
  experience: ExperienceItem[];
}

export interface LinkedInStructured {
  profile_url?: string;
  headline?: string;
  skills?: string[];
  experience?: ExperienceItem[];
}

/* ---- Consent ---- */

export interface ConsentPayload {
  consent_version: string;
  consent_given: boolean;
  recruiter_confirmation?: boolean;
}

/* ---- API Payload ---- */

export interface AnalysisPayload {
  username: string;
  role_level: string;
  resume_data: ResumeStructured;
  linkedin_data?: LinkedInStructured;
  leetcode_username: string;
  resume_text?: string;
  consent: ConsentPayload;
  recruiter_mode?: boolean;
}

/* ---- Report types ---- */

export interface ComponentScores {
  github_score: number;
  profile_score: number;
  leetcode_score: number;
  redflag_severity: number;
}

export interface PSTReport {
  username: string;
  role_level: string;
  pst_score: number;
  trust_level: string;
  component_scores: ComponentScores;
  explanation?: Record<string, unknown>;
}

export interface RedFlag {
  flag: string;
  severity: string;
  reason: string;
}

export interface RedFlagResult {
  username: string;
  raw_flags: {
    flags: RedFlag[];
    total_flags: number;
    risk_level: string;
  };
  severity_score: number;
  explanation: Record<string, unknown>;
}

export interface EngineResult {
  raw_metrics: Record<string, unknown>;
  normalized_score: number;
  explanation: Record<string, unknown>;
}

export interface FullAnalysisResult {
  username: string;
  role_level: string;
  github: EngineResult;
  profile_consistency: EngineResult;
  leetcode: EngineResult;
  redflags: RedFlagResult;
  pst_report: PSTReport;
}

export interface JobStatusResponse {
  job_id: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  result?: FullAnalysisResult | null;
}

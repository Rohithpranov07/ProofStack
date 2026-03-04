/* ─── Dashboard Response Types ─── */

export interface CommitTimelinePoint {
  date: string;
  count: number;
}

export interface DifficultyBar {
  label: string;
  value: number;
}

export interface TrendPoint {
  month: string;
  submissions: number;
}

export interface DashboardCharts {
  commit_timeline: CommitTimelinePoint[];
  leetcode_difficulty: DifficultyBar[];
  leetcode_trend: TrendPoint[];
}

export interface GitHubEngine {
  normalized_score: number;
  consistency: number;
  entropy_label: string;
  commit_count: number;
  repo_count: number;
  burst_detected: boolean;
  engine_failed: boolean;
  failure_reason: string | null;
  rate_limited: boolean;
}

export interface AdvancedGitHubEngine {
  anomaly_score: number;
  loc_anomaly_ratio: number;
  interval_cv: number;
  empty_commit_ratio: number;
  repetitive_message_ratio: number;
  engine_failed: boolean;
}

export interface ProfileEngine {
  normalized_score: number;
  has_data: boolean;
  skill_ratio: number;
  project_ratio: number;
  experience_ratio: number;
  verification_items: ProfileVerificationItem[];
  skill_verified: number;
  skill_total: number;
  skill_mismatches: Array<{ skill: string; issue: string }>;
  project_verified: number;
  project_total: number;
  project_mismatches: Array<{ project: string; issue: string }>;
  experience_verified: number;
  experience_total: number;
  experience_mismatches: Array<{ company: string; claimed_start?: string; earliest_github?: string; issue: string }>;
  earliest_github_repo_date: string | null;
  linkedin_profile_verified: boolean;
  linkedin_skill_mismatch: string[];
  linkedin_experience_mismatch: string[];
  multi_contributor_repos: number;
  engine_failed: boolean;
  failure_reason: string | null;
}

export interface ProfileVerificationItem {
  data_point: string;
  source_a: string;
  source_b: string;
  confidence: number;
}

export interface LeetCodeEngine {
  normalized_score: number;
  total_solved: number;
  easy: number;
  medium: number;
  hard: number;
  acceptance_rate: number;
  ranking: number;
  archetype: string;
  engine_failed: boolean;
  failure_reason: string | null;
}

export interface ProductMindsetComponent {
  value: number;
  max: number;
}

export interface ProductMindsetRepoDetail {
  repo: string;
  has_problem_statement: boolean;
  has_impact_metrics: boolean;
  has_deployment: boolean;
  is_tutorial_clone: boolean;
  is_recent: boolean;
}

export interface ProductMindsetEngine {
  normalized_score: number;
  has_data: boolean;
  problem_detection: number;
  impact_metrics: number;
  deployment_evidence: number;
  originality: number;
  maintenance_recency: number;
  repos_analyzed: number;
  problem_hits: number;
  metric_hits: number;
  deploy_hits: number;
  tutorial_hits: number;
  recent_repos: number;
  components: Record<string, ProductMindsetComponent>;
  repo_details: ProductMindsetRepoDetail[];
  engine_failed: boolean;
  failure_reason: string | null;
}

export interface DFTopRepo {
  name: string;
  stars: number;
  description: string;
  language: string;
  tags: string[];
  forks: number;
  url: string;
  created_at?: string;
}

export interface DFStackOverflowDetail {
  searched: string;
  reputation: number;
  found: boolean;
  user_id?: number;
  profile_url?: string;
  display_name?: string;
  answer_count: number;
  question_count: number;
  badge_count: number;
  helper_ratio: number;
  last_access_date?: number;
}

export interface DFMergedPRDetail {
  merged_count: number;
}

export interface DFStarsDetail {
  total_stars: number;
  owned_repos: number;
}

export interface DFBlogDetail {
  url: string | null;
  reachable: boolean;
}

export interface DFRecencyDetail {
  latest_push: string | null;
  github_recency_pts: number;
  so_recency_pts: number;
}

export interface DigitalFootprintEngine {
  normalized_score: number;
  has_data: boolean;
  stackoverflow_score: number;
  merged_pr_score: number;
  stars_score: number;
  blog_score: number;
  recency_score: number;
  seo_tier: string;
  // Raw detail breakdowns
  stackoverflow_detail: DFStackOverflowDetail;
  merged_pr_detail: DFMergedPRDetail;
  stars_detail: DFStarsDetail;
  blog_detail: DFBlogDetail;
  recency_detail: DFRecencyDetail;
  // Top repos and network reach
  top_repos: DFTopRepo[];
  followers: number;
  following: number;
  total_forks: number;
  bio: string | null;
  twitter_username: string | null;
  public_repos_count: number;
  engine_failed: boolean;
  failure_reason: string | null;
}

export interface ATSStuffingDetail {
  repeated_keywords: string[];
  comma_list_detected: boolean;
  tfidf_spike_count: number;
  phantom_skills: string[];
}

export interface ATSCareerDetail {
  gap_months: number;
  overlaps: number;
  rapid_promotions: number;
  avg_tenure_months: number;
}

export interface ATSComponentDetail {
  value: number;
  max: number;
}

export interface ATSWarning {
  source: string;
  message: string;
  severity: string;
}

export interface ATSIntelligenceEngine {
  normalized_score: number;
  has_data: boolean;
  structure_score: number;
  parse_score: number;
  skill_authenticity_score: number;
  role_alignment_score: number;
  career_consistency_score: number;
  keyword_stuffing_risk: string;
  recruiter_readability: string;
  cross_validation_penalty: number;
  readability_score: number;
  // Structure sub-metrics
  section_completeness: number;
  bullet_quality: number;
  metric_density: number;
  formatting_safety: number;
  // Skill sub-metrics
  skill_overlap_ratio: number;
  inflation_detected: boolean;
  buzzword_density: number;
  // Detail breakdowns
  stuffing_detail: ATSStuffingDetail;
  career_detail: ATSCareerDetail;
  // Explanation
  components: Record<string, string>;
  warnings: ATSWarning[];
  headline: string;
  engine_failed: boolean;
  failure_reason: string | null;
}

export interface RedFlagEngine {
  severity_score: number;
  risk_level: string;
  total_flags: number;
  flags: RedFlagItem[];
  engine_failed: boolean;
}

export interface RedFlagItem {
  flag: string;
  severity: string;
  reason: string;
}

export interface DashboardEngines {
  github: GitHubEngine;
  advanced_github: AdvancedGitHubEngine;
  profile: ProfileEngine;
  leetcode: LeetCodeEngine;
  product_mindset: ProductMindsetEngine;
  digital_footprint: DigitalFootprintEngine;
  ats_intelligence: ATSIntelligenceEngine;
  redflag: RedFlagEngine;
}

export interface DashboardRecommendation {
  summary: string;
  strengths: string[];
  concerns: string[];
  flag_details: string[];
  confidence: string;
}

export interface EscalationInfo {
  cap_applied: string | null;
  escalation_reasons: string[];
  anomaly_score: number;
  confidence_reduction_pct: number;
}

export interface DashboardResponse {
  job_id: string;
  run_id: string;
  username: string;
  role_level: string;
  trust_score: number;
  trust_band: string;
  escalation: EscalationInfo;
  engines: DashboardEngines;
  charts: DashboardCharts;
  recommendation: DashboardRecommendation;
}

/* ─── Risk badge severity ─── */
export type RiskSeverity = "HIGH" | "MEDIUM" | "LOW";

export function getRiskBadge(severityScore: number): {
  label: string;
  color: string;
  bgColor: string;
} {
  if (severityScore >= 85) {
    return { label: "HIGH RISK", color: "#D93025", bgColor: "rgba(217, 48, 37, 0.1)" };
  }
  if (severityScore >= 70) {
    return { label: "MODERATE RISK", color: "#F9AB00", bgColor: "rgba(249, 171, 0, 0.1)" };
  }
  if (severityScore >= 40) {
    return { label: "SOME RISK", color: "#F9AB00", bgColor: "rgba(249, 171, 0, 0.1)" };
  }
  return { label: "LOW RISK", color: "#1E8E3E", bgColor: "rgba(30, 142, 62, 0.1)" };
}

export function getTrustBadge(trustBand: string): {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
} {
  switch (trustBand) {
    case "Highly Verified":
      return { label: "Highly Verified", color: "#1E8E3E", bgColor: "#e8f5e9", borderColor: "#c8e6c9" };
    case "Strong":
      return { label: "Strong", color: "#1E8E3E", bgColor: "#f0fdf4", borderColor: "#bbf7d0" };
    case "Moderate":
      return { label: "Moderate", color: "#F9AB00", bgColor: "#fffde7", borderColor: "#fff9c4" };
    case "Weak":
      return { label: "Weak", color: "#D93025", bgColor: "#fef2f2", borderColor: "#fecaca" };
    default:
      return { label: "High Risk", color: "#D93025", bgColor: "#fef2f2", borderColor: "#fecaca" };
  }
}

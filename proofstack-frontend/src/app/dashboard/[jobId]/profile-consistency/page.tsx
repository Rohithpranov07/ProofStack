"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import { useDashboard } from "@/lib/useDashboard";
import DetailLayout from "@/components/dashboard/DetailLayout";
import DashboardSkeleton from "@/components/dashboard/DashboardSkeleton";
import DashboardError from "@/components/dashboard/DashboardError";

type Section = "identity" | "skills" | "employment";

export default function ProfileConsistencyPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;
  const { data, loading, error, refetch } = useDashboard(jobId);
  const [activeSection, setActiveSection] = useState<Section>("identity");

  if (loading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error ?? "No data"} onRetry={refetch} />;

  const { profile } = data.engines;
  const items = profile.verification_items ?? [];
  const overallScore = profile.normalized_score;

  /* ── derived data ─────────────────────────────────── */
  const skillRatio = profile.skill_ratio ?? 0;
  const projectRatio = profile.project_ratio ?? 0;
  const experienceRatio = profile.experience_ratio ?? 0;

  const skillVerified = profile.skill_verified ?? 0;
  const skillTotal = profile.skill_total ?? 0;
  const projectVerified = profile.project_verified ?? 0;
  const projectTotal = profile.project_total ?? 0;
  const expVerified = profile.experience_verified ?? 0;
  const expTotal = profile.experience_total ?? 0;

  const skillMismatches = profile.skill_mismatches ?? [];
  const projectMismatches = profile.project_mismatches ?? [];
  const experienceMismatches = profile.experience_mismatches ?? [];
  const linkedinVerified = profile.linkedin_profile_verified ?? false;
  const linkedinSkillMismatch = profile.linkedin_skill_mismatch ?? [];
  const linkedinExpMismatch = profile.linkedin_experience_mismatch ?? [];
  const multiContribRepos = profile.multi_contributor_repos ?? 0;
  const earliestGithub = profile.earliest_github_repo_date ?? null;

  /* ── score badge colour ────────────────────────── */
  const scoreBand = overallScore >= 80 ? "HIGH" : overallScore >= 50 ? "MODERATE" : "LOW";
  const scoreColor = scoreBand === "HIGH" ? "#34A853" : scoreBand === "MODERATE" ? "#1A73E8" : "#EA4335";
  const scoreBg = scoreBand === "HIGH" ? "rgba(52,168,83,0.08)" : scoreBand === "MODERATE" ? "rgba(26,115,232,0.08)" : "rgba(234,67,53,0.08)";
  const badgeLabel = scoreBand === "HIGH" ? "Strong Match" : scoreBand === "MODERATE" ? "Partial Match" : "Weak Match";

  return (
    <DetailLayout jobId={jobId} title="Profile Consistency" badgeLabel={scoreBand === "HIGH" ? "Authentic" : scoreBand === "MODERATE" ? "Moderate" : "Alert"} badgeColor={scoreColor}>
      <div className="grid grid-cols-4 gap-6">
        {/* ────── Left sidebar ────── */}
        <div className="col-span-4 lg:col-span-1 space-y-5">
          {/* Score card */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-3">
              Consistency Score
            </p>
            <div className="flex items-baseline gap-1">
              <span className="text-5xl font-black" style={{ color: scoreColor }}>{overallScore.toFixed(1)}</span>
              <span className="text-2xl font-bold" style={{ color: scoreColor, opacity: 0.5 }}>%</span>
            </div>
            <div className="mt-3 h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div className="h-2.5 rounded-full transition-all duration-700" style={{ width: `${overallScore}%`, background: `linear-gradient(90deg, ${scoreColor}, ${scoreColor}bb)` }} />
            </div>
            <div className="mt-3 flex items-center gap-2">
              <span
                className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide"
                style={{ background: scoreBg, color: scoreColor }}
              >
                {badgeLabel}
              </span>
            </div>
            <p className="mt-3 text-[13px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Cross-referencing {skillTotal} skills, {projectTotal} project{projectTotal !== 1 ? "s" : ""}, and {expTotal} experience{expTotal !== 1 ? "s" : ""} against digital profiles.
            </p>
          </div>

          {/* Stats grid */}
          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm grid grid-cols-2 gap-3">
            <StatMini label="Skills" verified={skillVerified} total={skillTotal} color="#1A73E8" />
            <StatMini label="Projects" verified={projectVerified} total={projectTotal} color="#34A853" />
            <StatMini label="Experience" verified={expVerified} total={expTotal} color="#F9AB00" />
            <StatMini label="Collab Repos" verified={multiContribRepos} total={multiContribRepos} color="#A142F4" isCount />
          </div>

          {/* Navigation card */}
          <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <h3 className="font-bold text-xs text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3">Sections</h3>
            <div className="space-y-1">
              <NavButton icon="grid_view" label="Identity Matrix" active={activeSection === "identity"} onClick={() => setActiveSection("identity")} />
              <NavButton icon="verified" label="Skill Validation" active={activeSection === "skills"} onClick={() => setActiveSection("skills")} />
              <NavButton icon="work_history" label="Employment History" active={activeSection === "employment"} onClick={() => setActiveSection("employment")} />
            </div>
          </div>
        </div>

        {/* ────── Right content (single card at a time) ────── */}
        <div className="col-span-4 lg:col-span-3 flex items-start justify-center">
          <div className="w-full max-w-4xl">

          {/* ═══ SECTION 1: Identity Verification Matrix ═══ */}
          {activeSection === "identity" && (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden animate-in fade-in duration-300">
              <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[18px] text-[#1A73E8]">grid_view</span>
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900 dark:text-white" style={{ fontFamily: "'Google Sans', sans-serif" }}>Identity Verification Matrix</h2>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500">Cross-platform data point comparison</p>
                  </div>
                </div>
                <span className="text-[10px] text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-800 px-2.5 py-1 rounded-full">Last synced: recently</span>
              </div>
              <table className="w-full">
                <thead className="bg-slate-50/80 dark:bg-slate-800/50">
                  <tr>
                    <th className="px-5 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-left">Data Point</th>
                    <th className="px-5 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-left">Source A (Resume)</th>
                    <th className="px-5 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-left">Source B (Digital)</th>
                    <th className="px-5 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-left">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {items.length === 0 && (
                    <tr><td colSpan={4} className="px-6 py-8 text-center text-sm text-slate-400">No verification data available.</td></tr>
                  )}
                  {items.map((item, idx) => {
                    const conf = item.confidence;
                    const confColor = conf >= 80 ? "#34A853" : conf >= 50 ? "#F9AB00" : "#EA4335";
                    const confBg = conf >= 80 ? "rgba(52,168,83,0.08)" : conf >= 50 ? "rgba(249,171,0,0.08)" : "rgba(234,67,53,0.08)";
                    const confIcon = conf >= 80 ? "check_circle" : conf >= 50 ? "warning" : "cancel";
                    return (
                      <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-[16px]" style={{ color: confColor }}>{confIcon}</span>
                            <span className="text-sm font-semibold text-slate-900 dark:text-white">{item.data_point}</span>
                          </div>
                        </td>
                        <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-400">{item.source_a}</td>
                        <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-400">{item.source_b}</td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2.5">
                            <div className="h-2 w-20 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                              <div className="h-2 rounded-full transition-all duration-500" style={{ width: `${conf}%`, backgroundColor: confColor }} />
                            </div>
                            <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ color: confColor, background: confBg }}>
                              {conf}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* ═══ SECTION 2: Skill Validation ═══ */}
          {activeSection === "skills" && (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6 animate-in fade-in duration-300">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-8 h-8 rounded-lg bg-green-50 dark:bg-green-900/30 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px] text-[#34A853]">verified</span>
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white" style={{ fontFamily: "'Google Sans', sans-serif" }}>Skill Validation</h2>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500">Resume claims vs verified digital evidence</p>
                </div>
              </div>

              {/* Overall bars */}
              <div className="space-y-4 mb-6">
                <SkillBar label="Technical Skills" verified={skillVerified} total={skillTotal} ratio={skillRatio} color="#1A73E8" icon="code" />
                <SkillBar label="Projects" verified={projectVerified} total={projectTotal} ratio={projectRatio} color="#34A853" icon="folder_open" />
                <SkillBar label="Experience" verified={expVerified} total={expTotal} ratio={experienceRatio} color="#F9AB00" icon="work" />
              </div>

              {/* Mismatched skills detail */}
              {skillMismatches.length > 0 && (
                <div className="mt-4 p-4 bg-amber-50/60 dark:bg-amber-900/10 border border-amber-200/50 dark:border-amber-800/30 rounded-lg">
                  <div className="flex items-center gap-2 mb-2.5">
                    <span className="material-symbols-outlined text-[16px] text-amber-600 dark:text-amber-400">info</span>
                    <span className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wide">Unverified Skills</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {skillMismatches.map((m, i) => (
                      <span key={i} className="px-2.5 py-1 text-[11px] font-medium rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border border-amber-200/50 dark:border-amber-800/30">
                        {typeof m === "string" ? m : m.skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Missing projects detail */}
              {projectMismatches.length > 0 && (
                <div className="mt-3 p-4 bg-red-50/60 dark:bg-red-900/10 border border-red-200/50 dark:border-red-800/30 rounded-lg">
                  <div className="flex items-center gap-2 mb-2.5">
                    <span className="material-symbols-outlined text-[16px] text-red-500">folder_off</span>
                    <span className="text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wide">Projects Not Found on GitHub</span>
                  </div>
                  <div className="space-y-2">
                    {projectMismatches.map((m, i) => (
                      <div key={i} className="flex items-start gap-2 text-[12px] text-red-700 dark:text-red-400">
                        <span className="material-symbols-outlined text-[14px] mt-0.5">close</span>
                        <div>
                          <span className="font-semibold">{m.project}</span>
                          <span className="text-red-500/70 dark:text-red-500/50 ml-1">— {m.issue}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* LinkedIn cross-check */}
              {(linkedinVerified || linkedinSkillMismatch.length > 0) && (
                <div className="mt-4 p-4 bg-blue-50/60 dark:bg-blue-900/10 border border-blue-200/50 dark:border-blue-800/30 rounded-lg">
                  <div className="flex items-center gap-2 mb-2.5">
                    <span className="material-symbols-outlined text-[16px] text-[#1A73E8]">link</span>
                    <span className="text-xs font-bold text-[#1A73E8] uppercase tracking-wide">LinkedIn Cross-Reference</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 mb-2">
                    <span className="material-symbols-outlined text-[16px] text-[#34A853]">check_circle</span>
                    Profile verified via LinkedIn API
                  </div>
                  {linkedinSkillMismatch.length > 0 && (
                    <div className="mt-2">
                      <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1.5">Skills on LinkedIn but not on resume:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {linkedinSkillMismatch.map((s, i) => (
                          <span key={i} className="px-2.5 py-1 text-[11px] font-medium rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-200/50 dark:border-blue-800/30">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ═══ SECTION 3: Employment History ═══ */}
          {activeSection === "employment" && (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6 animate-in fade-in duration-300">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px] text-amber-600">work_history</span>
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white" style={{ fontFamily: "'Google Sans', sans-serif" }}>Employment History Cross-Reference</h2>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500">Timeline verification against GitHub activity since {earliestGithub ?? "N/A"}</p>
                </div>
              </div>

              {/* Summary stat */}
              <div className="flex items-center gap-4 mb-5 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-[#34A853]">timeline</span>
                  <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                    {expVerified} of {expTotal} positions verified
                  </span>
                </div>
                <div className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-2 rounded-full transition-all duration-500" style={{ width: `${experienceRatio * 100}%`, background: experienceRatio >= 0.7 ? "#34A853" : experienceRatio >= 0.4 ? "#F9AB00" : "#EA4335" }} />
                </div>
                <span className="text-xs font-bold" style={{ color: experienceRatio >= 0.7 ? "#34A853" : experienceRatio >= 0.4 ? "#F9AB00" : "#EA4335" }}>
                  {Math.round(experienceRatio * 100)}%
                </span>
              </div>

              {/* Verified entries */}
              <div className="space-y-3">
                {expVerified > 0 && (
                  <TimelineEntry
                    title={`${expVerified} Position${expVerified > 1 ? "s" : ""} Verified`}
                    status="VERIFIED"
                    icon="check_circle"
                    iconColor="#34A853"
                    description={`Employment timeline is consistent with GitHub activity dating back to ${earliestGithub ?? "N/A"}. ${expVerified > 1 ? "Multiple roles" : "The role"} fall${expVerified > 1 ? "" : "s"} within the active coding period.`}
                  />
                )}

                {experienceMismatches.length > 0 && experienceMismatches.map((m, idx) => (
                  <TimelineEntry
                    key={idx}
                    title={m.company}
                    status="UNVERIFIED"
                    icon="help_outline"
                    iconColor="#F9AB00"
                    description={m.issue}
                    meta={m.claimed_start ? `Claimed start: ${m.claimed_start} · Earliest GitHub: ${m.earliest_github}` : undefined}
                  />
                ))}

                {linkedinExpMismatch.length > 0 && (
                  <TimelineEntry
                    title="LinkedIn Experience Discrepancy"
                    status="INFO"
                    icon="info"
                    iconColor="#1A73E8"
                    description={`The following companies appear on LinkedIn but not on the resume: ${linkedinExpMismatch.join(", ")}`}
                  />
                )}

                {multiContribRepos > 0 && (
                  <TimelineEntry
                    title="Team Collaboration Detected"
                    status="SIGNAL"
                    icon="group"
                    iconColor="#A142F4"
                    description={`${multiContribRepos} repositor${multiContribRepos > 1 ? "ies" : "y"} with multiple contributors detected, indicating real team collaboration experience.`}
                  />
                )}

                {earliestGithub && (
                  <TimelineEntry
                    title="GitHub Activity Origin"
                    status="INFO"
                    icon="flag"
                    iconColor="#1A73E8"
                    description={`Earliest public repository created on ${earliestGithub}. All experience entries are validated against this anchor point.`}
                  />
                )}
              </div>
            </div>
          )}

          </div>
        </div>
      </div>
    </DetailLayout>
  );
}

/* ── Helper components ───────────────────────────────── */

function StatMini({ label, verified, total, color, isCount = false }: { label: string; verified: number; total: number; color: string; isCount?: boolean }) {
  return (
    <div className="text-center p-2">
      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 block mb-1">{label}</span>
      <span className="text-lg font-black tabular-nums" style={{ color }}>
        {isCount ? verified : `${verified}/${total}`}
      </span>
    </div>
  );
}

function NavButton({ icon, label, active = false, onClick }: { icon: string; label: string; active?: boolean; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
        active
          ? "bg-[#1A73E8]/10 dark:bg-[#1A73E8]/20 text-[#1A73E8] font-semibold shadow-sm"
          : "hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
      }`}
    >
      <span className="material-symbols-outlined text-lg">{icon}</span>
      {label}
    </button>
  );
}

function SkillBar({ label, verified, total, ratio, color, icon }: { label: string; verified: number; total: number; ratio: number; color: string; icon: string }) {
  const pct = Math.round(ratio * 100);
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px]" style={{ color }}>{icon}</span>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400 dark:text-slate-500">{verified} of {total}</span>
          <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ color, background: `${color}14` }}>
            {pct}%
          </span>
        </div>
      </div>
      <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-3 rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${color}, ${color}bb)`,
            boxShadow: `0 0 8px ${color}30`,
          }}
        />
      </div>
    </div>
  );
}

function TimelineEntry({ title, status, icon, iconColor, description, meta }: {
  title: string;
  status: string;
  icon: string;
  iconColor: string;
  description: string;
  meta?: string;
}) {
  const statusColors: Record<string, { bg: string; text: string }> = {
    VERIFIED: { bg: "rgba(52,168,83,0.08)", text: "#34A853" },
    UNVERIFIED: { bg: "rgba(249,171,0,0.08)", text: "#F9AB00" },
    INFO: { bg: "rgba(26,115,232,0.08)", text: "#1A73E8" },
    SIGNAL: { bg: "rgba(161,66,244,0.08)", text: "#A142F4" },
  };
  const sc = statusColors[status] ?? statusColors.INFO;

  return (
    <div className="p-4 rounded-lg bg-slate-50/70 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800 hover:border-slate-200 dark:hover:border-slate-700 transition-colors">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: sc.bg }}>
          <span className="material-symbols-outlined text-[18px]" style={{ color: iconColor }}>{icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-semibold text-sm text-slate-900 dark:text-white">{title}</span>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full" style={{ color: sc.text, background: sc.bg }}>
              {status}
            </span>
          </div>
          {meta && <p className="text-[11px] text-slate-400 dark:text-slate-500 font-mono mb-1">{meta}</p>}
          <p className="text-[13px] text-slate-600 dark:text-slate-400 leading-relaxed">{description}</p>
        </div>
      </div>
    </div>
  );
}

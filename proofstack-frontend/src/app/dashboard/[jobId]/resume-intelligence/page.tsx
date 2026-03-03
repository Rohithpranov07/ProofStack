"use client";

import { useParams } from "next/navigation";
import { useDashboard } from "@/lib/useDashboard";
import DetailLayout from "@/components/dashboard/DetailLayout";
import DashboardSkeleton from "@/components/dashboard/DashboardSkeleton";
import DashboardError from "@/components/dashboard/DashboardError";
import type { ATSIntelligenceEngine as ATSEngine } from "@/types/dashboard";

/* ── Helpers ── */

function stuffingRiskBadge(risk: string): { label: string; color: string; bg: string } {
  switch (risk) {
    case "none":
    case "low":
      return { label: "Low Risk", color: "#1E8E3E", bg: "#e8f5e9" };
    case "moderate":
      return { label: "Moderate Risk", color: "#F9AB00", bg: "#fff8e1" };
    case "high":
      return { label: "High Risk", color: "#D93025", bg: "#fce8e6" };
    case "critical":
      return { label: "Critical", color: "#D93025", bg: "#fce8e6" };
    default:
      return { label: "Unknown", color: "#5F6368", bg: "#f1f3f4" };
  }
}

function readabilityBadge(label: string): { color: string; bg: string } {
  switch (label) {
    case "Excellent":
      return { color: "#1E8E3E", bg: "#e8f5e9" };
    case "Good":
      return { color: "#1A73E8", bg: "#e8f0fe" };
    case "Dense":
      return { color: "#F9AB00", bg: "#fff8e1" };
    case "Overloaded":
      return { color: "#D93025", bg: "#fce8e6" };
    default:
      return { color: "#5F6368", bg: "#f1f3f4" };
  }
}

function generateNarrative(ats: ATSEngine): string[] {
  const paragraphs: string[] = [];

  // Overall assessment
  const score = ats.normalized_score;
  const level = score >= 80 ? "excellent" : score >= 60 ? "strong" : score >= 40 ? "moderate" : "concerning";
  paragraphs.push(
    `This resume achieved an overall ATS Intelligence Score of **${score.toFixed(1)}/100**, indicating ${level} quality for automated tracking system compatibility and recruiter readability.`
  );

  // Structure assessment
  const structureLabel =
    ats.structure_score >= 80 ? "well-structured" :
    ats.structure_score >= 60 ? "adequately structured" :
    ats.structure_score >= 40 ? "partially structured" : "poorly structured";
  paragraphs.push(
    `The resume is **${structureLabel}** with a section completeness of ${(ats.section_completeness * 100).toFixed(0)}%, bullet quality at ${(ats.bullet_quality * 100).toFixed(0)}%, and metric density of ${(ats.metric_density * 100).toFixed(0)}%. Formatting safety is ${(ats.formatting_safety * 100).toFixed(0)}% — ${ats.formatting_safety >= 0.8 ? "safe for ATS parsing" : "may cause issues with some ATS systems"}.`
  );

  // Skill authenticity
  if (ats.inflation_detected) {
    paragraphs.push(
      `**Skill inflation detected** with a buzzword density of ${ats.buzzword_density.toFixed(2)}%. The skill overlap ratio with GitHub evidence is **${(ats.skill_overlap_ratio * 100).toFixed(0)}%**, suggesting some claimed skills lack verifiable backing.`
    );
  } else if (ats.skill_overlap_ratio > 0) {
    paragraphs.push(
      `Skills appear authentic with a **${(ats.skill_overlap_ratio * 100).toFixed(0)}%** overlap ratio against GitHub evidence. Buzzword density is within acceptable range at ${ats.buzzword_density.toFixed(2)}%.`
    );
  }

  // Cross-validation
  if (ats.cross_validation_penalty > 0) {
    paragraphs.push(
      `A cross-validation penalty of **${ats.cross_validation_penalty.toFixed(1)} points** was applied based on discrepancies between resume claims and other engine verification results.`
    );
  }

  return paragraphs;
}

/* ── Score Ring Component ── */
function ScoreRing({ score, size = 100, label }: { score: number; size?: number; label: string }) {
  const r = (size - 10) / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 70 ? "#1E8E3E" : score >= 45 ? "#F9AB00" : "#D93025";

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90 absolute inset-0">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#f1f3f4" strokeWidth="6" />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-700"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-xl font-bold text-slate-900">
          {score.toFixed(0)}
        </span>
      </div>
      <span className="text-[11px] font-medium text-slate-500">{label}</span>
    </div>
  );
}

export default function ResumeIntelligencePage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;
  const { data, loading, error, refetch } = useDashboard(jobId);

  if (loading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error ?? "No data"} onRetry={refetch} />;

  const ats = data.engines.ats_intelligence;
  const stuffBadge = stuffingRiskBadge(ats.keyword_stuffing_risk);
  const readBadge = readabilityBadge(ats.recruiter_readability);
  const narrativeParagraphs = generateNarrative(ats);

  // Score breakdown bars
  const scoreBreakdown = [
    { label: "Structure Quality", score: ats.structure_score, weight: "25%" },
    { label: "Skill Authenticity", score: ats.skill_authenticity_score, weight: "25%" },
    { label: "Role Alignment", score: ats.role_alignment_score, weight: "15%" },
    { label: "Career Consistency", score: ats.career_consistency_score, weight: "15%" },
    { label: "ATS Parse Quality", score: ats.parse_score, weight: "10%" },
    { label: "Readability", score: ats.readability_score, weight: "10%" },
  ];

  // Structure breakdown
  const structureMetrics = [
    { label: "Section Completeness", value: ats.section_completeness },
    { label: "Bullet Quality", value: ats.bullet_quality },
    { label: "Metric Density", value: ats.metric_density },
    { label: "Formatting Safety", value: ats.formatting_safety },
  ];

  // Career detail
  const career = ats.career_detail || {};
  const careerItems = [
    { label: "Career Gap", value: `${career.gap_months ?? 0} months`, warn: (career.gap_months ?? 0) > 6 },
    { label: "Overlapping Roles", value: `${career.overlaps ?? 0}`, warn: (career.overlaps ?? 0) > 0 },
    { label: "Rapid Promotions", value: `${career.rapid_promotions ?? 0}`, warn: (career.rapid_promotions ?? 0) > 2 },
    { label: "Average Tenure", value: `${(career.avg_tenure_months ?? 0).toFixed(0)} months`, warn: (career.avg_tenure_months ?? 0) < 12 },
  ];

  return (
    <DetailLayout jobId={jobId} title="Resume Intelligence" badgeLabel="ATS Engine" badgeColor="#0D9488">
      {/* Hero */}
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500 mb-2">
            Dashboard <span className="material-symbols-outlined text-sm align-middle">chevron_right</span> Analysis Report
          </p>
          <h1 className="text-4xl font-black leading-tight tracking-tight text-slate-900 flex items-center gap-3">
            {data.username}
            <span
              className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border"
              style={{ background: stuffBadge.bg, color: stuffBadge.color, borderColor: `${stuffBadge.color}30` }}
            >
              <span className="material-symbols-outlined text-sm filled">
                {ats.keyword_stuffing_risk === "none" || ats.keyword_stuffing_risk === "low" ? "verified" : "warning"}
              </span>
              {stuffBadge.label}
            </span>
          </h1>
          <p className="text-slate-500 text-lg font-medium mt-1">ATS Resume Intelligence Report</p>
        </div>
      </div>

      {/* Top-level scores */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10">
        <div className="rounded-xl p-6 bg-white border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">ATS Score</p>
          <p className="text-4xl font-bold text-slate-900">{ats.normalized_score.toFixed(0)}</p>
          <p className="text-xs text-slate-400 mt-1">out of 100</p>
        </div>
        <div className="rounded-xl p-6 bg-white border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Structure</p>
          <p className="text-4xl font-bold text-slate-900">{ats.structure_score.toFixed(0)}</p>
          <p className="text-xs text-slate-400 mt-1">Quality</p>
        </div>
        <div className="rounded-xl p-6 bg-white border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Readability</p>
          <p className="text-4xl font-bold" style={{ color: readBadge.color }}>{ats.recruiter_readability}</p>
          <p className="text-xs text-slate-400 mt-1">Recruiter Friendly</p>
        </div>
        <div className="rounded-xl p-6 bg-white border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Skill Auth</p>
          <p className="text-4xl font-bold text-slate-900">{ats.skill_authenticity_score.toFixed(0)}</p>
          <p className="text-xs text-slate-400 mt-1">Verified Match</p>
        </div>
        <div className="rounded-xl p-6 bg-white border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Penalty</p>
          <p className="text-4xl font-bold text-red-600">-{ats.cross_validation_penalty.toFixed(0)}</p>
          <p className="text-xs text-slate-400 mt-1">Cross-Validation</p>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Left Column */}
        <div className="col-span-12 lg:col-span-7 space-y-8">
          {/* Score Breakdown */}
          <div className="bg-white rounded-xl p-8 border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-6">Score Breakdown</h2>
            <div className="space-y-4">
              {scoreBreakdown.map((item) => {
                const barColor = item.score >= 70 ? "bg-green-500" : item.score >= 45 ? "bg-amber-500" : "bg-red-500";
                return (
                  <div key={item.label}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-slate-700">{item.label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">Weight: {item.weight}</span>
                        <span className="text-sm font-bold text-slate-900">{item.score.toFixed(1)}</span>
                      </div>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full">
                      <div
                        className={`h-2 rounded-full transition-all duration-500 ${barColor}`}
                        style={{ width: `${item.score}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Narrative Evaluation */}
          <div className="bg-white rounded-xl p-8 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-[#0D9488]">psychology</span>
              <h2 className="text-lg font-bold text-slate-900">Narrative Evaluation</h2>
            </div>
            <div className="text-slate-600 leading-relaxed text-base space-y-4">
              {narrativeParagraphs.map((para, idx) => (
                <p
                  key={idx}
                  dangerouslySetInnerHTML={{
                    __html: para.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"),
                  }}
                />
              ))}
            </div>
          </div>

          {/* Structure Analysis */}
          <div className="bg-white rounded-xl p-8 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <span className="material-symbols-outlined text-[#1A73E8]">architecture</span>
              <h2 className="text-lg font-bold text-slate-900">Structure Analysis</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {structureMetrics.map((m) => (
                <div key={m.label} className="text-center p-4 bg-slate-50 rounded-lg">
                  <p className="text-3xl font-bold text-slate-900">{(m.value * 100).toFixed(0)}%</p>
                  <p className="text-xs text-slate-500 mt-1">{m.label}</p>
                </div>
              ))}
            </div>
          </div>

      {/* Warnings */}
      {ats.warnings && ats.warnings.length > 0 && (
        <div className="bg-white rounded-xl p-8 border border-slate-200 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-amber-500">warning</span>
            <h2 className="text-lg font-bold text-slate-900">Warnings &amp; Recommendations</h2>
          </div>
          <ul className="space-y-2">
            {ats.warnings.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <span className={`material-symbols-outlined text-base mt-0.5 ${
                  w.severity === "HIGH" ? "text-red-400" : "text-amber-400"
                }`}>circle</span>
                <span>
                  <span className="font-medium text-slate-700">{w.source}:</span>{" "}
                  {w.message}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
        </div>

        {/* Right Column */}
        <div className="col-span-12 lg:col-span-5 space-y-6">
          {/* Score Rings */}
          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 mb-4 text-center">Sub-Score Overview</h3>
            <div className="grid grid-cols-3 gap-4">
              <ScoreRing score={ats.structure_score} size={80} label="Structure" />
              <ScoreRing score={ats.skill_authenticity_score} size={80} label="Skills" />
              <ScoreRing score={ats.role_alignment_score} size={80} label="Role Fit" />
              <ScoreRing score={ats.career_consistency_score} size={80} label="Career" />
              <ScoreRing score={ats.parse_score} size={80} label="Parse" />
              <ScoreRing score={ats.readability_score} size={80} label="Readability" />
            </div>
          </div>

          {/* Keyword Stuffing */}
          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-900">Keyword Stuffing Analysis</h3>
              <span
                className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase"
                style={{ background: stuffBadge.bg, color: stuffBadge.color }}
              >
                {stuffBadge.label}
              </span>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Comma-list detected</span>
                <span className={`text-sm font-bold ${ats.stuffing_detail?.comma_list_detected ? "text-red-600" : "text-green-600"}`}>
                  {ats.stuffing_detail?.comma_list_detected ? "Yes" : "No"}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">TF-IDF Spikes</span>
                <span className="text-sm font-bold text-slate-900">{ats.stuffing_detail?.tfidf_spike_count ?? 0}</span>
              </div>
              {ats.stuffing_detail?.repeated_keywords?.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-slate-500 block mb-1.5">Repeated Keywords</span>
                  <div className="flex flex-wrap gap-1.5">
                    {ats.stuffing_detail.repeated_keywords.slice(0, 10).map((kw) => (
                      <span
                        key={kw}
                        className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-[10px] font-bold uppercase"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {ats.stuffing_detail?.phantom_skills?.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-slate-500 block mb-1.5">Phantom Skills (claimed but unverified)</span>
                  <div className="flex flex-wrap gap-1.5">
                    {ats.stuffing_detail.phantom_skills.slice(0, 10).map((s) => (
                      <span
                        key={s}
                        className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-[10px] font-bold uppercase"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Career Consistency */}
          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 mb-4">Career Consistency</h3>
            <div className="space-y-3">
              {careerItems.map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded flex items-center justify-center ${item.warn ? "bg-amber-50" : "bg-slate-100"}`}>
                    <span className={`material-symbols-outlined text-lg ${item.warn ? "text-amber-600" : "text-slate-500"}`}>
                      {item.warn ? "warning" : "check_circle"}
                    </span>
                  </div>
                  <span className="flex-1 text-sm font-medium text-slate-700">{item.label}</span>
                  <span className={`text-sm font-bold ${item.warn ? "text-amber-600" : "text-slate-900"}`}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Skill Authentication */}
          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 mb-4">Skill Authentication</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">GitHub Overlap</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-2 bg-slate-100 rounded-full">
                    <div
                      className="h-2 bg-[#1A73E8] rounded-full"
                      style={{ width: `${ats.skill_overlap_ratio * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-slate-900">{(ats.skill_overlap_ratio * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Buzzword Density</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-2 bg-slate-100 rounded-full">
                    <div
                      className={`h-2 rounded-full ${ats.buzzword_density > 1.5 ? "bg-amber-500" : "bg-green-500"}`}
                      style={{ width: `${Math.min(ats.buzzword_density / 3 * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-slate-900">{ats.buzzword_density.toFixed(2)}%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Inflation Detected</span>
                <span className={`text-sm font-bold ${ats.inflation_detected ? "text-red-600" : "text-green-600"}`}>
                  {ats.inflation_detected ? "Yes" : "No"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DetailLayout>
  );
}

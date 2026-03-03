"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getSharedDashboard, getDashboardPdfUrl } from "@/lib/api";
import type { DashboardResponse } from "@/types/dashboard";
import { getTrustBadge } from "@/types/dashboard";
import {
  TrustScoreHero,
  RiskPanel,
  CodeAuthenticityCard,
  ProfileConsistencyCard,
  ProblemSolvingCard,
  ProductMindsetCard,
  DigitalFootprintCard,
  ResumeIntelligenceCard,
  FinalRecommendationCard,
  DashboardSkeleton,
  DashboardError,
} from "@/components/dashboard";

export default function SharedDashboardPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSharedDashboard(token)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error ?? "Share link not found or expired"} />;

  const badge = getTrustBadge(data.trust_band);
  const initials = data.username
    .split(/[\s_-]/)
    .map((s) => s[0]?.toUpperCase() ?? "")
    .slice(0, 2)
    .join("");

  // Shared job id for linking (read-only, no detail links)
  const jobId = data.job_id;

  return (
    <div className="min-h-screen dash-bg flex flex-col">
      {/* Read-only header */}
      <header className="bg-white border-b border-[#DADCE0] sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#1A73E8] text-3xl">shield_person</span>
              <span className="font-bold text-xl text-gray-800 tracking-tight" style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}>
                ProofStack
              </span>
            </div>
            <div className="h-6 w-px bg-[#DADCE0] mx-2" />
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-[#1A73E8]/10 flex items-center justify-center text-[#1A73E8] font-bold text-sm">
                {initials}
              </div>
              <div>
                <h1 className="font-medium text-sm text-gray-900 leading-tight" style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}>
                  {data.username}
                </h1>
                <p className="text-xs text-gray-500 leading-tight">
                  {data.role_level.charAt(0).toUpperCase() + data.role_level.slice(1)} Level Engineer
                </p>
              </div>
              <span
                className="text-[10px] font-bold px-2 py-0.5 rounded-sm uppercase tracking-wider ml-2"
                style={{ background: badge.bgColor, color: badge.color, border: `1px solid ${badge.borderColor}` }}
              >
                {badge.label}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-full text-xs font-semibold border border-amber-200">
              <span className="material-symbols-outlined text-sm">visibility</span>
              Shared View (Read-only)
            </span>
            <button
              onClick={() => window.open(getDashboardPdfUrl(jobId), "_blank")}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[#1A73E8] text-white hover:bg-[#1557b0] rounded-full shadow-sm transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
              Export PDF
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-[1600px] mx-auto w-full p-6">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
            <TrustScoreHero score={data.trust_score} trustBand={data.trust_band} engines={data.engines} escalation={data.escalation} />
            <RiskPanel redflag={data.engines.redflag} />
            <ProblemSolvingCard leetcode={data.engines.leetcode} difficulty={data.charts.leetcode_difficulty} jobId={jobId} />
          </div>
          <div className="col-span-12 lg:col-span-8 flex flex-col gap-6">
            <CodeAuthenticityCard github={data.engines.github} commitTimeline={data.charts.commit_timeline} jobId={jobId} />
            <ProfileConsistencyCard profile={data.engines.profile} jobId={jobId} />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <ProductMindsetCard product={data.engines.product_mindset} jobId={jobId} />
              <DigitalFootprintCard footprint={data.engines.digital_footprint} jobId={jobId} />
              <ResumeIntelligenceCard ats={data.engines.ats_intelligence} jobId={jobId} />
            </div>
            <FinalRecommendationCard recommendation={data.recommendation} username={data.username} />
          </div>
        </div>
      </main>

      <footer className="border-t border-[#DADCE0] py-6 mt-auto">
        <div className="max-w-[1600px] mx-auto px-6 flex items-center justify-between">
          <p className="text-xs text-gray-400">&copy; {new Date().getFullYear()} ProofStack &mdash; Recruiter Intelligence Platform</p>
          <p className="text-xs text-gray-400">Shared Report &bull; Read Only</p>
        </div>
      </footer>
    </div>
  );
}

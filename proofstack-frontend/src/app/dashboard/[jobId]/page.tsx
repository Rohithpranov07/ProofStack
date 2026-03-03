"use client";

import { useParams } from "next/navigation";
import { useDashboard } from "@/lib/useDashboard";
import { getDashboardPdfUrl, createShareLink } from "@/lib/api";
import {
  HeaderBar,
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

export default function DashboardPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;
  const { data, loading, error, refetch } = useDashboard(jobId);

  if (loading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error ?? "No data found"} onRetry={refetch} />;

  const handleExportPdf = () => {
    window.open(getDashboardPdfUrl(jobId), "_blank");
  };

  const handleShare = async () => {
    try {
      const { share_url } = await createShareLink(jobId);
      const fullUrl = `${window.location.origin}${share_url}`;
      if (navigator.share) {
        await navigator.share({ title: `ProofStack — ${data.username}`, url: fullUrl });
      } else {
        await navigator.clipboard.writeText(fullUrl);
      }
    } catch {
      await navigator.clipboard.writeText(window.location.href);
    }
  };

  const handleRerun = () => {
    // Navigate back to analyze with pre-filled data
    window.location.href = "/analyze";
  };

  return (
    <div className="min-h-screen dash-bg flex flex-col">
      <HeaderBar data={data} onExportPdf={handleExportPdf} onRerun={handleRerun} onShare={handleShare} />

      <main className="flex-1 max-w-[1600px] mx-auto w-full p-6">
        <div className="grid grid-cols-12 gap-6">
          {/* ─── Left Column ─── */}
          <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
            <TrustScoreHero
              score={data.trust_score}
              trustBand={data.trust_band}
              engines={data.engines}
              escalation={data.escalation}
            />

            <RiskPanel redflag={data.engines.redflag} />

            <ProblemSolvingCard
              leetcode={data.engines.leetcode}
              difficulty={data.charts.leetcode_difficulty}
              jobId={jobId}
            />
          </div>

          {/* ─── Right Column ─── */}
          <div className="col-span-12 lg:col-span-8 flex flex-col gap-6">
            <CodeAuthenticityCard
              github={data.engines.github}
              commitTimeline={data.charts.commit_timeline}
              jobId={jobId}
            />

            <ProfileConsistencyCard
              profile={data.engines.profile}
              jobId={jobId}
            />

            {/* 3-column sub-grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <ProductMindsetCard
                product={data.engines.product_mindset}
                jobId={jobId}
              />
              <DigitalFootprintCard
                footprint={data.engines.digital_footprint}
                jobId={jobId}
              />
              <ResumeIntelligenceCard
                ats={data.engines.ats_intelligence}
                jobId={jobId}
              />
            </div>

            <FinalRecommendationCard
              recommendation={data.recommendation}
              username={data.username}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#DADCE0] py-6 mt-auto">
        <div className="max-w-[1600px] mx-auto px-6 flex items-center justify-between">
          <p className="text-xs text-gray-400">
            &copy; {new Date().getFullYear()} ProofStack &mdash; Recruiter Intelligence Platform
          </p>
          <p className="text-xs text-gray-400">
            Job ID: <span className="font-mono">{data.job_id}</span> &bull; Run: <span className="font-mono">{data.run_id}</span>
          </p>
        </div>
      </footer>
    </div>
  );
}

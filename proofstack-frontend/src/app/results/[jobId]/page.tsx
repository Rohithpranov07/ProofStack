"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { getJobStatus } from "@/lib/api";
import type { FullAnalysisResult } from "@/types";
import TrustScoreCard from "@/components/TrustScoreCard";
import BreakdownChart from "@/components/BreakdownChart";
import RedFlagList from "@/components/RedFlagList";
import RecruiterSummary from "@/components/RecruiterSummary";
import EngineDetailCard from "@/components/EngineDetailCard";

export default function ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router = useRouter();
  const [data, setData] = useState<FullAnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) return;

    const fetchResult = async () => {
      try {
        const res = await getJobStatus(jobId);

        if (res.status === "PENDING" || res.status === "RUNNING") {
          router.replace(`/analysis/${jobId}`);
          return;
        }

        if (res.status === "FAILED") {
          setError("Analysis failed. Please re-run.");
          setLoading(false);
          return;
        }

        if (res.status === "COMPLETED" && res.result) {
          setData(res.result);
        } else {
          setError("Analysis result not available.");
        }
      } catch {
        setError("Failed to load analysis result.");
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [jobId, router]);

  /* ---- Loading ---- */
  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-2 w-2 animate-pulse rounded-full bg-accent-primary" />
      </div>
    );
  }

  /* ---- Error ---- */
  if (error || !data) {
    return (
      <div className="mx-auto max-w-[700px] py-20">
        <div className="rounded-2xl border border-accent-red/20 bg-bg-card p-10 text-center">
          <h2 className="text-xl font-semibold">
            {error || "Analysis result not available."}
          </h2>
          <button
            type="button"
            onClick={() => router.push("/analyze")}
            className="mt-6 rounded-xl bg-accent-primary px-6 py-3 text-sm font-semibold text-white transition-all duration-200 hover:scale-[1.03] hover:opacity-90"
          >
            Back to Analyze
          </button>
        </div>
      </div>
    );
  }

  /* ---- Data ready ---- */
  const { pst_report, redflags, github, profile_consistency, leetcode } = data;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="mx-auto max-w-[1200px] space-y-16 py-20"
    >
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-center"
      >
        <p className="text-sm font-medium uppercase tracking-widest text-text-muted">
          Trust Report
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          {data.username}
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Role: {data.role_level.charAt(0).toUpperCase() + data.role_level.slice(1)} Level
        </p>
      </motion.div>

      {/* Section 1 — PST Score */}
      <TrustScoreCard
        pstScore={pst_report.pst_score}
        trustLevel={pst_report.trust_level}
      />

      {/* Section 2 — Score Breakdown */}
      <BreakdownChart componentScores={pst_report.component_scores} />

      {/* Section 3 — Detailed Engine Analysis */}
      <section>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="mb-6 text-lg font-semibold"
        >
          Detailed Engine Analysis
        </motion.h2>
        <div className="grid gap-6 lg:grid-cols-2">
          <EngineDetailCard
            title="GitHub Analysis"
            icon="🐙"
            score={github.normalized_score}
            metrics={github.raw_metrics}
            explanation={github.explanation}
            delay={0.1}
          />
          <EngineDetailCard
            title="Profile Consistency"
            icon="🔗"
            score={profile_consistency.normalized_score}
            metrics={profile_consistency.raw_metrics}
            explanation={profile_consistency.explanation}
            delay={0.2}
          />
          <EngineDetailCard
            title="LeetCode Analysis"
            icon="💻"
            score={leetcode.normalized_score}
            metrics={leetcode.raw_metrics}
            explanation={leetcode.explanation}
            delay={0.3}
          />
          <EngineDetailCard
            title="Red Flag Severity"
            icon="🚩"
            score={Math.max(0, 100 - redflags.severity_score)}
            metrics={{
              total_flags: redflags.raw_flags?.total_flags ?? 0,
              risk_level: redflags.raw_flags?.risk_level ?? "LOW",
              severity_score: redflags.severity_score,
            }}
            explanation={redflags.explanation}
            delay={0.4}
          />
        </div>
      </section>

      {/* Section 4 — Red Flags */}
      <RedFlagList
        redFlags={{
          flags: redflags.raw_flags?.flags ?? [],
          risk_level: redflags.raw_flags?.risk_level ?? "LOW RISK",
        }}
      />

      {/* Section 5 — Recruiter Summary */}
      <RecruiterSummary
        trustLevel={pst_report.trust_level}
        pstScore={pst_report.pst_score}
      />

      {/* Analyze Another */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.6 }}
        className="flex justify-center"
      >
        <button
          type="button"
          onClick={() => router.push("/analyze")}
          className="rounded-xl border border-border-subtle px-8 py-3 text-sm font-medium text-text-muted transition-all duration-200 hover:border-text-muted hover:text-text-primary"
        >
          ← Analyze Another Candidate
        </button>
      </motion.div>
    </motion.div>
  );
}

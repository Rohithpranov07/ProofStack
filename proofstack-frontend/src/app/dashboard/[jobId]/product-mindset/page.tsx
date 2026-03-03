"use client";

import { useParams } from "next/navigation";
import { useDashboard } from "@/lib/useDashboard";
import DetailLayout from "@/components/dashboard/DetailLayout";
import DashboardSkeleton from "@/components/dashboard/DashboardSkeleton";
import DashboardError from "@/components/dashboard/DashboardError";
import type { ProductMindsetEngine as PMEngine } from "@/types/dashboard";

const INDICATORS = [
  { key: "problem_detection", label: "Problem Statement Detection" },
  { key: "impact_metrics", label: "Impact Metrics Clarity" },
  { key: "deployment_evidence", label: "Deployment Evidence" },
  { key: "originality", label: "Originality Score" },
  { key: "maintenance_recency", label: "Maintenance Recency" },
] as const;

/* ── Qualitative insight generation from scores ── */

interface InsightItem {
  label: "Strength" | "Opportunity" | "Neutral";
  title: string;
  description: string;
}

function generateInsights(pm: PMEngine): InsightItem[] {
  const items: InsightItem[] = [];
  const total = pm.repos_analyzed || 1;

  // Problem detection
  if (pm.problem_detection >= 0.5) {
    items.push({
      label: "Strength",
      title: "Clear Problem Framing",
      description: `${pm.problem_hits} of ${total} repositories articulate clear problem statements in their READMEs.`,
    });
  } else if (pm.problem_detection > 0) {
    items.push({
      label: "Opportunity",
      title: "Problem Framing",
      description: `Only ${pm.problem_hits} of ${total} repositories contain problem statements. Strengthening project purpose descriptions would improve clarity.`,
    });
  } else {
    items.push({
      label: "Opportunity",
      title: "Problem Framing Missing",
      description: "No repositories articulate a clear problem statement. Adding 'why' framing to READMEs would demonstrate product thinking.",
    });
  }

  // Impact metrics
  if (pm.impact_metrics >= 0.4) {
    items.push({
      label: "Strength",
      title: "Impact Awareness",
      description: `${pm.metric_hits} of ${total} projects include measurable impact metrics in their documentation.`,
    });
  } else if (pm.impact_metrics > 0) {
    items.push({
      label: "Neutral",
      title: "Some Impact Metrics",
      description: `${pm.metric_hits} of ${total} projects reference quantitative impact. Adding more measurable outcomes would strengthen the profile.`,
    });
  } else {
    items.push({
      label: "Opportunity",
      title: "Impact Metrics Absent",
      description: "No projects include quantitative impact data. Adding metrics like user counts or performance improvements would help.",
    });
  }

  // Deployment evidence
  if (pm.deployment_evidence >= 0.4) {
    items.push({
      label: "Strength",
      title: "Deployment Discipline",
      description: `${pm.deploy_hits} of ${total} repositories show deployment evidence (live demos, CI/CD, Docker, etc.).`,
    });
  } else if (pm.deployment_evidence > 0) {
    items.push({
      label: "Neutral",
      title: "Some Deployment Evidence",
      description: `${pm.deploy_hits} of ${total} repositories show deployment artifacts. More live deployments would strengthen the profile.`,
    });
  } else {
    items.push({
      label: "Opportunity",
      title: "No Deployment Evidence",
      description: "No repositories show deployment evidence. Adding live demos or CI/CD would demonstrate shipping capability.",
    });
  }

  // Originality
  if (pm.originality >= 0.8) {
    items.push({
      label: "Strength",
      title: "High Originality",
      description: pm.tutorial_hits === 0
        ? "All analyzed projects show original problem-solving — no tutorial clones detected."
        : `Strong originality with only ${pm.tutorial_hits} tutorial-style project(s) among ${total} repositories.`,
    });
  } else if (pm.originality >= 0.5) {
    items.push({
      label: "Neutral",
      title: "Moderate Originality",
      description: `${pm.tutorial_hits} of ${total} projects follow common boilerplate or tutorial patterns. More original projects would improve this dimension.`,
    });
  } else {
    items.push({
      label: "Opportunity",
      title: "Originality Depth",
      description: `${pm.tutorial_hits} of ${total} projects rely on common boilerplate or clone patterns. Building novel solutions would demonstrate independent thinking.`,
    });
  }

  // Maintenance recency
  if (pm.maintenance_recency >= 0.5) {
    items.push({
      label: "Strength",
      title: "Active Maintenance",
      description: `${pm.recent_repos} of ${total} repositories were updated within the last 90 days, showing consistent project upkeep.`,
    });
  } else if (pm.maintenance_recency > 0) {
    items.push({
      label: "Neutral",
      title: "Moderate Maintenance",
      description: `${pm.recent_repos} of ${total} repositories have recent activity. More frequent updates would indicate stronger commitment.`,
    });
  } else {
    items.push({
      label: "Opportunity",
      title: "Maintenance Needed",
      description: "No repositories show recent activity (last 90 days). Active maintenance signals ongoing engineering commitment.",
    });
  }

  return items;
}

function generateSummary(pm: PMEngine): string[] {
  const paragraphs: string[] = [];
  const score = pm.normalized_score;
  const total = pm.repos_analyzed || 0;

  // First paragraph: overall assessment
  if (score >= 70) {
    paragraphs.push(
      `This candidate exhibits a strong product-oriented engineering mindset across ${total} analyzed repositories, with clear evidence of purposeful software development and deployment discipline.`
    );
  } else if (score >= 40) {
    paragraphs.push(
      `This candidate shows a moderate product-oriented mindset across ${total} analyzed repositories. While some product thinking is evident, there are areas where a stronger focus on problem framing and deployment could improve the profile.`
    );
  } else {
    paragraphs.push(
      `This candidate's ${total} analyzed repositories show limited evidence of product-oriented thinking. The projects would benefit from clearer problem articulation, impact measurement, and deployment practices.`
    );
  }

  // Second paragraph: specific data-driven observations
  const observations: string[] = [];
  if (pm.problem_detection > 0) {
    observations.push(
      pm.problem_detection >= 0.5
        ? "strong problem articulation in project documentation"
        : "some problem framing in select projects"
    );
  }
  if (pm.maintenance_recency > 0) {
    observations.push(
      pm.maintenance_recency >= 0.5
        ? "consistent maintenance patterns"
        : "moderate maintenance activity"
    );
  }
  if (pm.originality >= 0.8) {
    observations.push("above-average originality indicating independent thinking in solution design");
  } else if (pm.originality < 0.5) {
    observations.push("a reliance on tutorial-style projects that could be diversified");
  }
  if (pm.deployment_evidence >= 0.4) {
    observations.push("evidence of deployment discipline");
  }

  if (observations.length > 0) {
    paragraphs.push(
      `Repository analysis reveals ${observations.join(", ")}.`
    );
  }

  return paragraphs;
}

function generateNarrative(pm: PMEngine): string {
  const score = pm.normalized_score;
  const total = pm.repos_analyzed || 0;
  const parts: string[] = [];

  // Lead sentence based on overall score tier
  if (score >= 70) {
    parts.push(`Across ${total} analyzed repositories, this engineer demonstrates strong product-oriented thinking with a mindset score of ${(score / 10).toFixed(1)}/10.`);
  } else if (score >= 50) {
    parts.push(`Analysis of ${total} repositories reveals emerging product instincts (score: ${(score / 10).toFixed(1)}/10), with tangible strengths and clear areas for growth.`);
  } else if (score >= 30) {
    parts.push(`Review of ${total} repositories indicates primarily code-focused work (score: ${(score / 10).toFixed(1)}/10), with limited but present product awareness.`);
  } else {
    parts.push(`Across ${total} repositories analyzed (score: ${(score / 10).toFixed(1)}/10), product-oriented signals are minimal — most work appears exercise-driven.`);
  }

  // Data-specific observations
  if (pm.problem_hits > 0) {
    parts.push(`${pm.problem_hits} project${pm.problem_hits > 1 ? "s" : ""} articulate clear problem statements.`);
  }
  if (pm.deploy_hits > 0) {
    parts.push(`${pm.deploy_hits} show deployment evidence.`);
  }
  if (pm.tutorial_hits > 0) {
    parts.push(`${pm.tutorial_hits} appear tutorial-derived.`);
  } else if (total > 0) {
    parts.push("No tutorial clones detected — all work appears original.");
  }
  if (pm.recent_repos > 0) {
    parts.push(`${pm.recent_repos} of ${total} repos were updated in the last 90 days.`);
  }

  return parts.join(" ");
}

export default function ProductMindsetPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;
  const { data, loading, error, refetch } = useDashboard(jobId);

  if (loading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error ?? "No data"} onRetry={refetch} />;

  const { product_mindset } = data.engines;
  const overallScore = (product_mindset.normalized_score / 10).toFixed(1);

  const summaryParagraphs = generateSummary(product_mindset);
  const insights = generateInsights(product_mindset);
  const narrative = generateNarrative(product_mindset);

  return (
    <DetailLayout jobId={jobId} title="Product Mindset" badgeLabel="Verified" badgeColor="#34a853">
      {/* Hero */}
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-2">
            <span className="material-symbols-outlined text-sm align-middle mr-1">chevron_right</span>
            Dashboard &rsaquo; Analysis Report
          </p>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
            Product Mindset
            <span className="ml-3 inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold uppercase bg-green-50 text-green-700 border border-green-200">
              <span className="material-symbols-outlined text-sm filled">verified</span>
              Verified
            </span>
          </h1>
          <p className="text-slate-500 font-medium uppercase text-xs tracking-wider mt-1">
            Product-oriented engineering assessment
          </p>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Left column */}
        <div className="col-span-12 lg:col-span-8 space-y-8">
          {/* Product Mindset Indicators */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
              <span className="material-symbols-outlined text-[#1A73E8]">analytics</span>
              <h2 className="text-base font-bold text-slate-900">Product Mindset Indicators</h2>
            </div>
            <div className="p-6 space-y-5">
              {INDICATORS.map(({ key, label }) => {
                const value = (product_mindset[key] as number) ?? 0;
                const pct = Math.round(value * 100);
                return (
                  <div key={key}>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-sm font-medium text-slate-700">{label}</span>
                      <span className="text-sm font-bold text-slate-900">{pct}%</span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-2 bg-[#1A73E8] rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Qualitative Evaluation */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
              <span className="material-symbols-outlined text-[#1A73E8]">rate_review</span>
              <h2 className="text-base font-bold text-slate-900">Qualitative Evaluation</h2>
            </div>
            <div className="p-6">
              {summaryParagraphs.map((para, idx) => (
                <p key={idx} className={`text-slate-600 leading-relaxed ${idx === 0 ? "text-lg mb-4" : "mb-6"}`}>
                  {para}
                </p>
              ))}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {insights.map((insight, idx) => (
                  <InsightCard
                    key={idx}
                    label={insight.label}
                    title={insight.title}
                    description={insight.description}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* Key Metrics Summary */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm">
            <div className="p-6 divide-y divide-slate-200">
              <div className="pb-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-medium mb-1">
                  Overall Mindset Score
                </p>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-black text-[#1A73E8]">{overallScore}</span>
                  <span className={`text-sm font-bold flex items-center gap-0.5 ${product_mindset.normalized_score >= 50 ? "text-green-600" : "text-amber-600"}`}>
                    <span className="material-symbols-outlined text-sm">
                      {product_mindset.normalized_score >= 50 ? "trending_up" : "trending_down"}
                    </span>
                    {product_mindset.normalized_score >= 50 ? "Above" : "Below"} avg
                  </span>
                </div>
              </div>
              <div className="py-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-medium mb-1">
                  Project Longevity
                </p>
                <span className="text-xl font-bold text-slate-900">
                  {product_mindset.maintenance_recency >= 0.5 ? "Active" : product_mindset.maintenance_recency > 0 ? "Moderate" : "Dormant"}
                </span>
              </div>
              <div className="py-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-medium mb-1">
                  Repos Analyzed
                </p>
                <span className="text-xl font-bold text-slate-900">{product_mindset.repos_analyzed}</span>
              </div>
              <div className="pt-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-medium mb-1">
                  Originality Index
                </p>
                <OriginalityStars value={product_mindset.originality} tutorialHits={product_mindset.tutorial_hits} total={product_mindset.repos_analyzed} />
              </div>
            </div>
          </div>

          {/* Narrative block */}
          <div className="bg-[#1A73E8]/5 border border-[#1A73E8]/20 rounded-xl p-6 relative overflow-hidden">
            <span className="material-symbols-outlined text-6xl text-[#1A73E8]/10 absolute top-2 right-2">
              format_quote
            </span>
            <div className="flex items-center gap-2 mb-3 relative z-10">
              <span className="material-symbols-outlined text-[#1A73E8]">auto_awesome</span>
              <h3 className="text-sm font-bold text-[#1A73E8]">AI-Generated Narrative</h3>
            </div>
            <p className="text-slate-700 text-sm italic leading-relaxed mb-4 relative z-10">
              &ldquo;{narrative}&rdquo;
            </p>
            <div className="flex items-center gap-3 relative z-10">
              <div className="w-10 h-10 rounded-full bg-[#1A73E8]/20 text-[#1A73E8] flex items-center justify-center text-sm font-bold">
                PS
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900">ProofStack Intelligence</p>
                <p className="text-xs text-slate-500">Automated Narrative Synthesis</p>
              </div>
            </div>
          </div>

          {/* Deep Dive CTA */}
          <div className="bg-slate-900 rounded-xl p-6 text-white">
            <h3 className="font-bold mb-2">Request Deep Dive</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Get a granular breakdown of this candidate&apos;s product thinking patterns, including
              competitive analysis and historical trends.
            </p>
            <button className="w-full py-2 bg-white text-slate-900 rounded-lg text-sm font-bold hover:bg-slate-100 transition-colors">
              Request Analysis
            </button>
          </div>
        </div>
      </div>
    </DetailLayout>
  );
}

function OriginalityStars({ value, tutorialHits, total }: { value: number; tutorialHits: number; total: number }) {
  const filledCount = Math.round(value * 5);
  const pct = Math.round(value * 100);
  const label = value >= 0.8 ? "High" : value >= 0.5 ? "Medium" : "Low";
  const labelColor = value >= 0.8 ? "text-green-600" : value >= 0.5 ? "text-amber-600" : "text-red-500";

  return (
    <div>
      <div className="flex items-center gap-1 mb-1.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            className={`material-symbols-outlined text-lg ${
              star <= filledCount ? "text-[#1A73E8] filled" : "text-slate-200"
            }`}
          >
            star
          </span>
        ))}
        <span className={`text-sm font-bold ml-1.5 ${labelColor}`}>{label}</span>
      </div>
      <div className="flex items-center gap-2 mt-1">
        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-1.5 rounded-full bg-[#1A73E8] transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-[11px] font-bold text-slate-500">{pct}%</span>
      </div>
      <p className="text-[10px] text-slate-400 mt-1">
        {tutorialHits === 0 && total > 0
          ? `All ${total} repos are original`
          : `${tutorialHits} of ${total} repos appear tutorial-derived`}
      </p>
    </div>
  );
}

function InsightCard({ label, title, description }: { label: string; title: string; description: string }) {
  const labelColor =
    label === "Strength"
      ? "text-green-600"
      : label === "Opportunity"
        ? "text-amber-600"
        : "text-slate-400";
  return (
    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
      <p className={`text-xs font-bold uppercase tracking-widest mb-1 ${labelColor}`}>{label}</p>
      <p className="text-sm font-semibold text-slate-900 mb-0.5">{title}</p>
      <p className="text-xs text-slate-500">{description}</p>
    </div>
  );
}

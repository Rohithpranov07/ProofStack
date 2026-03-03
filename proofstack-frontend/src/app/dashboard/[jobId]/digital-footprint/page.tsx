"use client";

import { useParams } from "next/navigation";
import { useDashboard } from "@/lib/useDashboard";
import DetailLayout from "@/components/dashboard/DetailLayout";
import DashboardSkeleton from "@/components/dashboard/DashboardSkeleton";
import DashboardError from "@/components/dashboard/DashboardError";
import type { DigitalFootprintEngine as DFEngine } from "@/types/dashboard";

/* ── Dynamic narrative generation ── */

function generateMaturityDescription(tier: string): string {
  switch (tier) {
    case "Authority":
      return "This profile ranks at the Authority tier, demonstrating industry-level visibility with strong community contributions, significant open-source impact, and a well-established online presence.";
    case "Visible":
      return "This profile ranks at the Visible tier, showing a strong discoverable presence with meaningful contributions across multiple developer platforms.";
    case "Active":
      return "This profile ranks at the Active tier, indicating regular contributions to the developer community with growing visibility across platforms.";
    case "Passive":
      return "This profile ranks at the Passive tier, with minimal but existing traces across developer platforms. Building more public contributions would strengthen visibility.";
    default:
      return "This profile ranks at the Ghost tier, with little to no discoverable developer footprint. Establishing presence on platforms like StackOverflow, contributing to open source, and maintaining a blog would significantly improve this score.";
  }
}

function generateNarrative(df: DFEngine): string[] {
  const paragraphs: string[] = [];
  const parts: string[] = [];

  // StackOverflow
  const so = df.stackoverflow_detail;
  if (so?.found && so.reputation > 0) {
    parts.push(
      `StackOverflow presence with ${so.reputation.toLocaleString()} reputation, ${so.answer_count} answers, and a helper ratio of ${(so.helper_ratio * 100).toFixed(0)}%`
    );
  } else {
    parts.push("no discoverable StackOverflow presence");
  }

  // Merged PRs
  const prCount = df.merged_pr_detail?.merged_count ?? 0;
  if (prCount > 0) {
    parts.push(`${prCount} merged pull request${prCount !== 1 ? "s" : ""} to external repositories`);
  }

  // Stars
  const totalStars = df.stars_detail?.total_stars ?? 0;
  if (totalStars > 0) {
    parts.push(`${totalStars.toLocaleString()} total GitHub stars across owned repositories`);
  }

  // Blog
  if (df.blog_detail?.url) {
    parts.push(
      df.blog_detail.reachable
        ? `an active blog/personal site`
        : `a blog/personal site listed though it may be unreachable`
    );
  }

  if (parts.length > 0) {
    paragraphs.push(
      `This candidate's digital footprint analysis reveals ${parts.join(", ")}.`
    );
  } else {
    paragraphs.push(
      "This candidate has minimal digital footprint across developer platforms. No significant StackOverflow activity, open-source contributions, or blog presence was detected."
    );
  }

  // Recency + SEO
  const recencyLabel = df.recency_score >= 10 ? "strong ongoing" : df.recency_score >= 5 ? "moderate" : df.recency_score > 0 ? "some" : "no recent";
  const seoLabel = df.seo_tier === "Authority" ? "industry-level" : df.seo_tier === "Visible" ? "strong" : df.seo_tier === "Active" ? "growing" : df.seo_tier === "Passive" ? "minimal" : "negligible";

  paragraphs.push(
    `The recency score of **${df.recency_score.toFixed(1)}** demonstrates ${recencyLabel} activity, while the SEO tier of **${df.seo_tier}** reflects ${seoLabel} professional visibility in the developer community.`
  );

  return paragraphs;
}

function safeBlogHostname(url: string): string {
  try {
    const full = url.startsWith("http") ? url : `https://${url}`;
    return new URL(full).hostname;
  } catch {
    return url;
  }
}

export default function DigitalFootprintPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;
  const { data, loading, error, refetch } = useDashboard(jobId);

  if (loading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error ?? "No data"} onRetry={refetch} />;

  const { digital_footprint } = data.engines;

  const metricsGrid = [
    {
      icon: "forum",
      label: "StackOverflow",
      value: digital_footprint.stackoverflow_detail?.found
        ? digital_footprint.stackoverflow_detail.reputation.toLocaleString()
        : "0",
      sub: digital_footprint.stackoverflow_detail?.found
        ? `${digital_footprint.stackoverflow_detail.answer_count} answers · ${digital_footprint.stackoverflow_detail.badge_count} badges`
        : "Reputation Score",
    },
    {
      icon: "merge_type",
      label: "Merged PRs",
      value: (digital_footprint.merged_pr_detail?.merged_count ?? 0).toString(),
      sub: "Open Source",
    },
    {
      icon: "star",
      label: "GitHub Stars",
      value: (digital_footprint.stars_detail?.total_stars ?? 0).toLocaleString(),
      sub: `Across ${digital_footprint.stars_detail?.owned_repos ?? 0} owned repos`,
    },
    {
      icon: "edit_note",
      label: "Blog Presence",
      value: digital_footprint.blog_detail?.url ? (digital_footprint.blog_detail.reachable ? "Active" : "Listed") : "None",
      sub: digital_footprint.blog_detail?.url
        ? safeBlogHostname(digital_footprint.blog_detail.url)
        : "No blog detected",
    },
  ];

  // Maturity scale — thresholds match backend _classify_seo_tier
  const maturityLevels = ["Ghost", "Passive", "Active", "Visible", "Authority"];
  const score = digital_footprint.normalized_score;
  const activeIdx = score >= 80 ? 4 : score >= 55 ? 3 : score >= 30 ? 2 : score >= 10 ? 1 : 0;

  // Top repos from actual data
  const topRepos = digital_footprint.top_repos ?? [];

  // Network metrics from actual data
  const networkMetrics = [
    { icon: "people", label: "GitHub Followers", value: (digital_footprint.followers ?? 0).toString(), color: (digital_footprint.followers ?? 0) > 0 ? "text-[#1A73E8]" : undefined },
    { icon: "fork_right", label: "Open Source Forks", value: (digital_footprint.total_forks ?? 0).toString(), color: (digital_footprint.total_forks ?? 0) > 0 ? "text-[#1A73E8]" : undefined },
    { icon: "trending_up", label: "Recency Score", value: digital_footprint.recency_score.toFixed(1), color: digital_footprint.recency_score > 0 ? "text-green-600" : undefined },
    { icon: "language", label: "SEO Tier", value: digital_footprint.seo_tier },
  ];

  const narrativeParagraphs = generateNarrative(digital_footprint);
  const maturityDescription = generateMaturityDescription(maturityLevels[activeIdx]);

  return (
    <DetailLayout jobId={jobId} title="Digital Footprint" badgeLabel="Authentic" badgeColor="#34a853">
      {/* Hero */}
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500 mb-2">
            Dashboard <span className="material-symbols-outlined text-sm align-middle">chevron_right</span> Analysis Report
          </p>
          <h1 className="text-4xl font-black leading-tight tracking-tight text-slate-900 flex items-center gap-3">
            {data.username}
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs font-bold uppercase tracking-wider border border-green-200">
              <span className="material-symbols-outlined text-sm filled">verified</span>
              Verified
            </span>
          </h1>
          <p className="text-slate-500 text-lg font-medium mt-1">Digital Footprint Analysis Report</p>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        {metricsGrid.map((m) => (
          <div key={m.label} className="rounded-xl p-6 bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-[20px] text-slate-500">{m.icon}</span>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{m.label}</span>
            </div>
            <p className="text-3xl font-bold text-slate-900">{m.value}</p>
            <p className="text-xs text-slate-400 font-medium mt-1">{m.sub}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Left */}
        <div className="col-span-12 lg:col-span-7 space-y-8">
          {/* Digital Footprint Maturity */}
          <div className="bg-white rounded-xl p-8 border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-6">Digital Footprint Maturity</h2>

            {/* Scale bar */}
            <div className="relative mb-8">
              <div className="h-2 bg-slate-100 rounded-full">
                <div
                  className="h-2 bg-[#1A73E8] rounded-full transition-all duration-500"
                  style={{ width: `${((activeIdx + 1) / maturityLevels.length) * 100}%` }}
                />
              </div>

              {/* Milestone dots */}
              <div className="flex justify-between mt-3">
                {maturityLevels.map((level, i) => (
                  <div key={level} className="flex flex-col items-center">
                    <div
                      className={`rounded-full flex items-center justify-center transition-all ${
                        i === activeIdx
                          ? "w-8 h-8 bg-[#1A73E8] text-white"
                          : i < activeIdx
                          ? "w-4 h-4 bg-[#1A73E8]"
                          : "w-4 h-4 bg-slate-200"
                      }`}
                    >
                      {i === activeIdx && (
                        <span className="material-symbols-outlined text-sm">visibility</span>
                      )}
                    </div>
                    <span
                      className={`text-xs mt-1.5 ${
                        i === activeIdx ? "font-bold text-[#1A73E8]" : "text-slate-500"
                      }`}
                    >
                      {level}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#1A73E8]/5 rounded-lg border border-[#1A73E8]/10 p-4">
              <p className="text-sm text-slate-700 leading-relaxed">
                {maturityDescription}
              </p>
            </div>
          </div>

          {/* Narrative Evaluation */}
          <div className="bg-white rounded-xl p-8 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-[#1A73E8]">psychology</span>
              <h2 className="text-lg font-bold text-slate-900">Narrative Evaluation</h2>
            </div>
            <div className="text-slate-600 leading-relaxed text-base space-y-4">
              {narrativeParagraphs.map((para, idx) => (
                <p key={idx} dangerouslySetInnerHTML={{
                  __html: para.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"),
                }} />
              ))}
            </div>
          </div>

          {/* StackOverflow Breakdown (if found) */}
          {digital_footprint.stackoverflow_detail?.found && (
            <div className="bg-white rounded-xl p-8 border border-slate-200 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-[#F48024]">forum</span>
                <h2 className="text-lg font-bold text-slate-900">StackOverflow Profile</h2>
                {digital_footprint.stackoverflow_detail.profile_url && (
                  <a
                    href={digital_footprint.stackoverflow_detail.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-auto text-xs text-[#1A73E8] font-bold hover:underline"
                  >
                    View Profile →
                  </a>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-2xl font-bold text-slate-900">
                    {digital_footprint.stackoverflow_detail.reputation.toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Reputation</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-2xl font-bold text-slate-900">{digital_footprint.stackoverflow_detail.answer_count}</p>
                  <p className="text-xs text-slate-500 mt-1">Answers</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-2xl font-bold text-slate-900">{digital_footprint.stackoverflow_detail.question_count}</p>
                  <p className="text-xs text-slate-500 mt-1">Questions</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-2xl font-bold text-slate-900">{digital_footprint.stackoverflow_detail.badge_count}</p>
                  <p className="text-xs text-slate-500 mt-1">Badges</p>
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2">
                <span className="text-xs text-slate-500">Helper Ratio:</span>
                <div className="flex-1 h-2 bg-slate-100 rounded-full">
                  <div
                    className="h-2 bg-[#F48024] rounded-full"
                    style={{ width: `${digital_footprint.stackoverflow_detail.helper_ratio * 100}%` }}
                  />
                </div>
                <span className="text-xs font-bold text-slate-700">
                  {(digital_footprint.stackoverflow_detail.helper_ratio * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Right */}
        <div className="col-span-12 lg:col-span-5 space-y-6">
          {/* Top Repositories */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200 flex justify-between items-center">
              <h3 className="font-bold text-slate-900">Top Repositories</h3>
              <a
                href={`https://github.com/${data.username}?tab=repositories`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#1A73E8] text-xs font-bold hover:underline cursor-pointer"
              >
                View All
              </a>
            </div>
            <div className="divide-y divide-slate-200">
              {topRepos.length > 0 ? (
                topRepos.map((repo) => (
                  <div key={repo.name} className="p-6 hover:bg-slate-50 transition-colors">
                    <div className="flex justify-between items-start mb-1">
                      <a
                        href={repo.url || `https://github.com/${data.username}/${repo.name}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-bold text-slate-900 hover:text-[#1A73E8] cursor-pointer"
                      >
                        {repo.name}
                      </a>
                      <div className="flex items-center gap-3">
                        {repo.created_at && (
                          <span className="text-slate-400 text-xs">
                            {new Date(repo.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
                          </span>
                        )}
                        <span className="flex items-center gap-0.5 text-slate-500 text-sm font-medium">
                          <span className="material-symbols-outlined text-sm">star</span>
                          {repo.stars}
                        </span>
                      </div>
                    </div>
                    <p className="text-slate-500 text-xs line-clamp-2 mb-2">
                      {repo.description || "No description"}
                    </p>
                    <div className="flex gap-1.5 flex-wrap">
                      {repo.tags.map((tag: string, i: number) => (
                        <span
                          key={tag}
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-tight ${
                            i === 0 ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-6 text-center text-slate-400 text-sm">
                  No public repositories found
                </div>
              )}
            </div>
          </div>

          {/* Network Reach */}
          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 mb-4">Network Reach</h3>
            <div className="space-y-3">
              {networkMetrics.map((nm) => (
                <div key={nm.label} className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-slate-100 flex items-center justify-center">
                    <span className="material-symbols-outlined text-slate-500 text-lg">{nm.icon}</span>
                  </div>
                  <span className="flex-1 text-sm font-medium text-slate-700">{nm.label}</span>
                  <span className={`text-sm font-bold ${nm.color ?? "text-slate-900"}`}>{nm.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Blog / Personal Site */}
          {digital_footprint.blog_detail?.url && (
            <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
              <h3 className="font-bold text-slate-900 mb-3">Blog / Personal Site</h3>
              <a
                href={digital_footprint.blog_detail.url.startsWith("http") ? digital_footprint.blog_detail.url : `https://${digital_footprint.blog_detail.url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#1A73E8] text-sm font-medium hover:underline break-all"
              >
                {digital_footprint.blog_detail.url}
              </a>
              <div className="flex items-center gap-1.5 mt-2">
                <span className={`w-2 h-2 rounded-full ${digital_footprint.blog_detail.reachable ? "bg-green-500" : "bg-amber-500"}`} />
                <span className="text-xs text-slate-500">
                  {digital_footprint.blog_detail.reachable ? "Site is reachable" : "Site may be unreachable"}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </DetailLayout>
  );
}

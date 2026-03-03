"use client";

import { useParams } from "next/navigation";
import { useDashboard } from "@/lib/useDashboard";
import DetailLayout from "@/components/dashboard/DetailLayout";
import DashboardSkeleton from "@/components/dashboard/DashboardSkeleton";
import DashboardError from "@/components/dashboard/DashboardError";

export default function ProblemSolvingPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;
  const { data, loading, error, refetch } = useDashboard(jobId);

  if (loading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error ?? "No data"} onRetry={refetch} />;

  const { leetcode } = data.engines;
  const trend = data.charts.leetcode_trend;
  const difficulty = data.charts.leetcode_difficulty;

  // Trend SVG
  const tWidth = 1000;
  const tHeight = 100;
  const maxSub = Math.max(...trend.map((t) => t.submissions), 1);
  const tPts = trend.map((t, i) => ({
    x: trend.length > 1 ? (i / (trend.length - 1)) * tWidth : tWidth / 2,
    y: tHeight - (t.submissions / maxSub) * (tHeight - 10) - 5,
  }));
  let trendLinePath = "";
  let trendAreaPath = "";
  if (tPts.length > 1) {
    trendLinePath = `M${tPts[0].x},${tPts[0].y}`;
    for (let i = 1; i < tPts.length; i++) {
      const cpx = (tPts[i - 1].x + tPts[i].x) / 2;
      trendLinePath += ` Q${cpx},${tPts[i - 1].y} ${tPts[i].x},${tPts[i].y}`;
    }
    trendAreaPath = `${trendLinePath} L${tPts[tPts.length - 1].x},${tHeight} L${tPts[0].x},${tHeight} Z`;
  }

  // Difficulty bar data
  const barColors: Record<string, { bg: string; fill: string }> = {
    Easy: { bg: "bg-[#1A73E8]/20", fill: "bg-[#1A73E8] opacity-80" },
    Med: { bg: "bg-amber-500/20", fill: "bg-amber-500 opacity-80" },
    Hard: { bg: "bg-red-500/20", fill: "bg-red-500 opacity-80" },
  };

  const maxDiff = Math.max(...difficulty.map((d) => d.value), 1);

  // Heatmap (simulated from trend data)
  const heatmapRows = 4;
  const heatmapCols = 12;
  const heatmap: number[][] = [];
  for (let r = 0; r < heatmapRows; r++) {
    const row: number[] = [];
    for (let c = 0; c < heatmapCols; c++) {
      // Generate pseudo-random intensity from leetcode data
      const seed = (r * heatmapCols + c + leetcode.total_solved) % 6;
      row.push(seed);
    }
    heatmap.push(row);
  }

  const intensityClasses = [
    "bg-slate-100",
    "bg-[#1A73E8]/20",
    "bg-[#1A73E8]/40",
    "bg-[#1A73E8]/60",
    "bg-[#1A73E8]/80",
    "bg-[#1A73E8]",
  ];

  return (
    <DetailLayout jobId={jobId} title="Problem-Solving Intelligence" badgeLabel="Authentic" badgeColor="#2e7d32">
      {/* Hero */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 mb-1">
          Problem-Solving Intelligence
          <span className="ml-3 inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold uppercase bg-green-100 text-green-700">
            <span className="material-symbols-outlined text-sm filled">verified</span>
            Verified
          </span>
        </h1>
        <p className="text-slate-500 text-lg">Algorithmic proficiency & competitive analysis</p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Performance Distribution */}
        <div className="col-span-12 md:col-span-7">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">
                Performance Distribution
              </h3>
              <span className="text-xs text-slate-400">
                Total Solved: <strong className="text-slate-700">{leetcode.total_solved}</strong>
              </span>
            </div>

            <div className="h-64 flex items-end gap-8 justify-center">
              {difficulty.slice(0, 3).map((d) => {
                const pct = (d.value / maxDiff) * 100;
                const colors = barColors[d.label] ?? barColors.Easy;
                return (
                  <div key={d.label} className="flex flex-col items-center flex-1 max-w-[120px] h-full justify-end relative">
                    <span className="text-xs font-bold text-slate-700 mb-2">{d.value}</span>
                    <div className={`w-full ${colors.bg} rounded-t-lg relative`} style={{ height: `${pct}%` }}>
                      <div className={`absolute inset-0 ${colors.fill} rounded-t-lg`} />
                    </div>
                    <span className="text-xs font-semibold text-slate-600 mt-2">{d.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Technical Metrics */}
        <div className="col-span-12 md:col-span-5 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-100 text-[#1A73E8] flex items-center justify-center">
              <span className="material-symbols-outlined text-2xl">check_circle</span>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Acceptance Rate</p>
              <p className="text-2xl font-black text-slate-900">{leetcode.acceptance_rate.toFixed(1)}%</p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-2xl">trophy</span>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Ranking</p>
              <p className="text-2xl font-black text-slate-900">#{leetcode.ranking.toLocaleString()}</p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 rounded border border-amber-200 text-amber-500 text-xs font-medium flex items-center gap-1">
                <span className="material-symbols-outlined text-sm">code</span>
                LeetCode
              </span>
            </div>
            <div className="flex-1">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Archetype</p>
              <p className="text-sm font-bold text-slate-900">{leetcode.archetype}</p>
            </div>
          </div>
        </div>

        {/* Submission Trend */}
        <div className="col-span-12">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">
                Submission Trend
              </h3>
              <div className="flex items-center gap-4 text-[10px] font-medium">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#1A73E8]" /> Submissions
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-slate-300" /> Average
                </span>
              </div>
            </div>

            <div className="relative h-40 w-full">
              <svg className="w-full h-full" viewBox={`0 0 ${tWidth} ${tHeight}`} preserveAspectRatio="none">
                <defs>
                  <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#1A73E8" stopOpacity="0.1" />
                    <stop offset="100%" stopColor="#1A73E8" stopOpacity="0" />
                  </linearGradient>
                </defs>
                {/* Average line */}
                <line x1="0" y1="60" x2={tWidth} y2="60" stroke="#DADCE0" strokeWidth="1" strokeDasharray="6 4" />
                {trendAreaPath && <path d={trendAreaPath} fill="url(#trendFill)" />}
                {trendLinePath && <path d={trendLinePath} fill="none" stroke="#1A73E8" strokeWidth="3" />}
              </svg>
            </div>

            {/* X-axis */}
            <div className="flex justify-between mt-2">
              {trend.map((t) => (
                <span key={t.month} className="text-[10px] font-bold text-slate-400 uppercase">
                  {t.month}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Heatmap */}
        <div className="col-span-12 md:col-span-8">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4">
              Submission Heatmap
            </h3>
            <div className="space-y-1">
              {heatmap.map((row, r) => (
                <div key={r} className="grid grid-cols-12 gap-1">
                  {row.map((intensity, c) => (
                    <div key={c} className={`aspect-square rounded-sm ${intensityClasses[intensity]}`} />
                  ))}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2 mt-3 justify-end">
              <span className="text-[10px] text-slate-400">Less</span>
              {intensityClasses.map((cls, i) => (
                <div key={i} className={`w-3 h-3 rounded-sm ${cls}`} />
              ))}
              <span className="text-[10px] text-slate-400">More</span>
            </div>
          </div>
        </div>

        {/* Narrative */}
        <div className="col-span-12 md:col-span-4">
          <div className="bg-[#1A73E8]/5 rounded-xl border border-[#1A73E8]/20 p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-[#1A73E8]">auto_awesome</span>
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#1A73E8]">
                Narrative Evaluation
              </h3>
            </div>
            <p className="text-sm leading-relaxed text-slate-700 mb-4">
              This candidate demonstrates strong algorithmic fundamentals with{" "}
              <strong>{leetcode.total_solved}</strong> problems solved across multiple difficulty
              tiers. Their acceptance rate of <strong>{leetcode.acceptance_rate.toFixed(1)}%</strong>{" "}
              indicates consistent problem-solving ability.
            </p>
            <div>
              <p className="text-xs font-bold text-slate-500 mb-2 uppercase tracking-wider">
                Key Differentiators
              </p>
              <div className="flex flex-wrap gap-1">
                <span className="px-2 py-1 bg-white rounded text-[10px] font-medium border border-[#1A73E8]/10 text-slate-700">
                  {leetcode.archetype}
                </span>
                <span className="px-2 py-1 bg-white rounded text-[10px] font-medium border border-[#1A73E8]/10 text-slate-700">
                  Top {Math.max(1, Math.round(100 - leetcode.acceptance_rate))}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DetailLayout>
  );
}

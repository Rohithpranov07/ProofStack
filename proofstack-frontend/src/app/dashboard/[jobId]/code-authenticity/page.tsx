"use client";

import { useParams } from "next/navigation";
import { useDashboard } from "@/lib/useDashboard";
import DetailLayout from "@/components/dashboard/DetailLayout";
import DashboardSkeleton from "@/components/dashboard/DashboardSkeleton";
import DashboardError from "@/components/dashboard/DashboardError";

export default function CodeAuthenticityPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;
  const { data, loading, error, refetch } = useDashboard(jobId);

  if (loading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error ?? "No data"} onRetry={refetch} />;

  const { github, advanced_github } = data.engines;
  const timeline = data.charts.commit_timeline;
  const maxCount = Math.max(...timeline.map((p) => p.count), 1);

  // SVG line path for trend
  const width = 1000;
  const height = 100;
  const pts = timeline.map((p, i) => ({
    x: timeline.length > 1 ? (i / (timeline.length - 1)) * width : width / 2,
    y: height - (p.count / maxCount) * (height - 10) - 5,
  }));
  let linePath = "";
  let areaPath = "";
  if (pts.length > 1) {
    linePath = `M${pts[0].x},${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
      const cpx = (pts[i - 1].x + pts[i].x) / 2;
      linePath += ` Q${cpx},${pts[i - 1].y} ${pts[i].x},${pts[i].y}`;
    }
    areaPath = `${linePath} L${pts[pts.length - 1].x},${height} L${pts[0].x},${height} Z`;
  }

  // Commit pattern metrics
  const metrics = [
    { metric: "Avg. Commits/Week", value: (github.commit_count / 52).toFixed(1), consistency: github.consistency, trend: "Stable" },
    { metric: "Repository Count", value: String(github.repo_count), consistency: 95, trend: "Growing" },
    { metric: "Burst Detection", value: github.burst_detected ? "Detected" : "None", consistency: github.burst_detected ? 40 : 90, trend: github.burst_detected ? "Warning" : "Stable" },
    { metric: "Entropy Level", value: github.entropy_label, consistency: github.entropy_label === "Low" ? 95 : 60, trend: github.entropy_label === "Low" ? "High" : "Moderate" },
  ];

  return (
    <DetailLayout jobId={jobId} title="Code Authenticity" badgeLabel="Authentic" badgeColor="#2e7d32">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: main content */}
        <div className="lg:col-span-8 space-y-8">
          {/* Commit Activity Timeline */}
          <div className="bg-white rounded-lg border border-[#DADCE0] shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium text-slate-900">Commit Activity Timeline</h2>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-[#1A73E8] rounded-sm" /> Human Commits
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-gray-300 rounded-sm" /> AI-Suggested
                </span>
              </div>
            </div>

            {/* Bar chart */}
            <div className="h-64 w-full bg-slate-50 border border-dashed border-gray-300 rounded-md p-4 flex items-end gap-2">
              {timeline.map((p, i) => {
                const pct = (p.count / maxCount) * 100;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                    <div
                      className="w-4 bg-[#1A73E8] rounded-t transition-all duration-300"
                      style={{ height: `${pct}%` }}
                    />
                    {i % Math.max(1, Math.floor(timeline.length / 5)) === 0 && (
                      <span className="text-[10px] text-gray-500 font-mono truncate max-w-[40px]">{p.date}</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Commit Pattern Analysis Table */}
          <div className="bg-white rounded-lg border border-[#DADCE0] shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-[#DADCE0]">
              <h2 className="text-lg font-medium text-slate-900">Commit Pattern Analysis</h2>
            </div>
            <table className="w-full">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3 text-left border-b border-[#DADCE0]">Metric</th>
                  <th className="px-6 py-3 text-left border-b border-[#DADCE0]">Value</th>
                  <th className="px-6 py-3 text-left border-b border-[#DADCE0]">Consistency Index</th>
                  <th className="px-6 py-3 text-left border-b border-[#DADCE0]">Trend</th>
                </tr>
              </thead>
              <tbody className="text-sm divide-y divide-gray-100">
                {metrics.map((m) => (
                  <tr key={m.metric} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium text-slate-900">{m.metric}</td>
                    <td className="px-6 py-4 text-slate-600 font-mono">{m.value}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-1.5">
                          <div className="bg-[#1A73E8] h-1.5 rounded-full" style={{ width: `${m.consistency}%` }} />
                        </div>
                        <span className="text-xs text-gray-500">{m.consistency}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-xs font-medium ${m.trend === "Warning" ? "text-amber-500" : "text-green-600"}`}>
                        {m.trend}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="lg:col-span-4 space-y-6">
          {/* Advanced Anomaly Detection */}
          <div className="bg-white rounded-lg border border-[#DADCE0] shadow-sm p-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-4">
              Advanced Anomaly Detection
            </h3>
            <div className="space-y-4">
              <MetricRow
                label="Anomaly Score"
                value={advanced_github.anomaly_score.toFixed(2)}
                description="Composite deviation index"
                color="text-[#1A73E8]"
                progress={(1 - advanced_github.anomaly_score) * 100}
                barColor="bg-[#1A73E8]"
              />
              <MetricRow
                label="LOC Anomaly Ratio"
                value={advanced_github.loc_anomaly_ratio.toFixed(3)}
                description="Lines-of-code deviation metric"
                color={advanced_github.loc_anomaly_ratio > 0.3 ? "text-orange-500" : "text-green-600"}
                progress={Math.min(advanced_github.loc_anomaly_ratio * 200, 100)}
                barColor={advanced_github.loc_anomaly_ratio > 0.3 ? "bg-orange-500" : "bg-green-600"}
              />
              <MetricRow
                label="Interval CV"
                value={advanced_github.interval_cv.toFixed(3)}
                description="Coefficient of variation in commit intervals"
                color="text-[#1A73E8]"
                progress={Math.min(advanced_github.interval_cv * 100, 100)}
                barColor="bg-[#1A73E8]"
              />
              <MetricRow
                label="Empty Commit Ratio"
                value={(advanced_github.empty_commit_ratio * 100).toFixed(1) + "%"}
                description="Percentage of empty or trivial commits"
                color={advanced_github.empty_commit_ratio > 0.1 ? "text-orange-500" : "text-green-600"}
                progress={advanced_github.empty_commit_ratio * 100}
                barColor={advanced_github.empty_commit_ratio > 0.1 ? "bg-orange-500" : "bg-green-600"}
              />
              <MetricRow
                label="Repetitive Message Ratio"
                value={(advanced_github.repetitive_message_ratio * 100).toFixed(1) + "%"}
                description="Copy-paste commit message detection"
                color={advanced_github.repetitive_message_ratio > 0.2 ? "text-orange-500" : "text-green-600"}
                progress={advanced_github.repetitive_message_ratio * 100}
                barColor={advanced_github.repetitive_message_ratio > 0.2 ? "bg-orange-500" : "bg-green-600"}
              />
            </div>

            {/* AI Risk Gauge */}
            <div className="mt-6 pt-4 border-t border-gray-100">
              <div className="flex flex-col items-center">
                <div className="relative w-32 h-16 overflow-hidden mb-2">
                  <div className="absolute inset-0 border-[12px] border-gray-100 rounded-full" />
                  <div
                    className="absolute inset-0 border-[12px] border-[#1A73E8] rounded-full"
                    style={{
                      clipPath: "inset(0 50% 50% 0)",
                      transform: `rotate(${Math.min(advanced_github.anomaly_score * 180, 170)}deg)`,
                      transformOrigin: "center bottom",
                    }}
                  />
                </div>
                <p className="text-sm font-medium text-slate-700">Risk of AI Synthesis</p>
                <p className="text-xs text-gray-500">
                  {advanced_github.anomaly_score < 0.2
                    ? "Negligible"
                    : advanced_github.anomaly_score < 0.5
                    ? "Low"
                    : "Elevated"}{" "}
                  ({(advanced_github.anomaly_score * 100).toFixed(0)}%)
                </p>
              </div>
            </div>
          </div>

          {/* Quick Tips */}
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
            <h4 className="text-[#1A73E8] text-xs font-bold uppercase tracking-wider mb-2">
              How to Interpret
            </h4>
            <p className="text-xs text-blue-800 leading-relaxed">
              A low anomaly score combined with high consistency and low entropy indicates genuine,
              organic coding activity. Burst detection flags sudden spikes that may warrant further
              investigation.
            </p>
          </div>
        </div>
      </div>
    </DetailLayout>
  );
}

function MetricRow({
  label,
  value,
  description,
  color,
  progress,
  barColor,
}: {
  label: string;
  value: string;
  description: string;
  color: string;
  progress: number;
  barColor: string;
}) {
  return (
    <div className="pb-4 border-b border-gray-100 last:border-b-0 last:pb-0">
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-xs font-medium text-gray-500">{label}</span>
        <span className={`text-lg font-bold ${color}`}>{value}</span>
      </div>
      <p className="text-[10px] text-gray-400 italic mb-2">{description}</p>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-2 rounded-full ${barColor}`} style={{ width: `${Math.min(progress, 100)}%` }} />
      </div>
    </div>
  );
}

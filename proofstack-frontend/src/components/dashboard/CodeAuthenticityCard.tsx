"use client";

import { memo } from "react";
import Link from "next/link";
import type { GitHubEngine, CommitTimelinePoint } from "@/types/dashboard";

interface CodeAuthenticityCardProps {
  github: GitHubEngine;
  commitTimeline: CommitTimelinePoint[];
  jobId: string;
}

function CodeAuthenticityCardInner({ github, commitTimeline, jobId }: CodeAuthenticityCardProps) {
  // Prepare chart data — normalize heights relative to max
  const maxCount = Math.max(...commitTimeline.map((p) => p.count), 1);

  // Build SVG area path
  const width = 400;
  const height = 100;
  const pts = commitTimeline.map((p, i) => ({
    x: commitTimeline.length > 1 ? (i / (commitTimeline.length - 1)) * width : width / 2,
    y: height - (p.count / maxCount) * (height - 10) - 5,
  }));

  let linePath = "";
  let areaPath = "";
  if (pts.length > 1) {
    // Smooth curve using quadratic bezier
    linePath = `M${pts[0].x},${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
      const cpx = (pts[i - 1].x + pts[i].x) / 2;
      linePath += ` Q${cpx},${pts[i - 1].y} ${pts[i].x},${pts[i].y}`;
    }
    areaPath = `${linePath} L${pts[pts.length - 1].x},${height} L${pts[0].x},${height} Z`;
  }

  // X-axis labels (first, middle, last)
  const xLabels: string[] = [];
  if (commitTimeline.length > 0) {
    xLabels.push(commitTimeline[0].date);
    if (commitTimeline.length > 2) {
      xLabels.push(commitTimeline[Math.floor(commitTimeline.length / 2)].date);
    }
    if (commitTimeline.length > 1) {
      xLabels.push(commitTimeline[commitTimeline.length - 1].date);
    }
  }

  return (
    <div className="dash-card p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#E8F0FE] rounded-lg text-[#1A73E8]">
            <span className="material-symbols-outlined text-xl">code</span>
          </div>
          <div>
            <h3
              className="text-lg font-medium text-gray-900"
              style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
            >
              Code Authenticity
            </h3>
            <p className="text-xs text-gray-500">GitHub commit analysis via advanced engine</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Consistency</div>
            <div className="text-lg font-mono font-medium text-gray-900">
              {github.consistency.toFixed(1)}%
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Entropy</div>
            <div className="text-lg font-mono font-medium text-gray-900">
              {github.entropy_label}
            </div>
          </div>
          <Link
            href={`/dashboard/${jobId}/code-authenticity`}
            className="text-xs font-medium text-[#1A73E8] hover:underline flex items-center gap-1"
          >
            View Details
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </Link>
        </div>
      </div>

      {/* Area chart */}
      <div className="relative h-48 w-full border-b border-l border-[#DADCE0]/50">
        {/* Dashed guidelines */}
        <div className="absolute inset-0 flex flex-col justify-between py-2 pointer-events-none">
          <div className="border-t border-dashed border-[#DADCE0]/30" />
          <div className="border-t border-dashed border-[#DADCE0]/30" />
          <div className="border-t border-dashed border-[#DADCE0]/30" />
        </div>

        <svg className="absolute inset-0 w-full h-full" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          <defs>
            <linearGradient id="commitFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1A73E8" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#1A73E8" stopOpacity="0" />
            </linearGradient>
          </defs>
          {areaPath && (
            <>
              <path d={areaPath} fill="url(#commitFill)" />
              <path d={linePath} fill="none" stroke="#1A73E8" strokeWidth="2" />
              {pts.map((p, i) => (
                <circle key={i} cx={p.x} cy={p.y} r="2.5" fill="#1A73E8" />
              ))}
            </>
          )}
        </svg>
      </div>

      {/* X-axis labels */}
      <div className="flex justify-between mt-2 px-1">
        {xLabels.map((label) => (
          <span key={label} className="text-[10px] text-gray-400 font-mono">
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

const CodeAuthenticityCard = memo(CodeAuthenticityCardInner);
export default CodeAuthenticityCard;

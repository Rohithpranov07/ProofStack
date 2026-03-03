"use client";

import { memo } from "react";
import Link from "next/link";
import type { DigitalFootprintEngine } from "@/types/dashboard";

interface DigitalFootprintCardProps {
  footprint: DigitalFootprintEngine;
  jobId: string;
}

const METRICS: { key: keyof DigitalFootprintEngine; label: string; format?: "score" }[] = [
  { key: "stackoverflow_score", label: "StackOverflow Score", format: "score" },
  { key: "merged_pr_score", label: "Merged PRs Score", format: "score" },
  { key: "stars_score", label: "GitHub Stars Score", format: "score" },
  { key: "blog_score", label: "Blog Presence Score", format: "score" },
  { key: "recency_score", label: "Recency Score", format: "score" },
  { key: "seo_tier", label: "SEO Tier" },
];

function DigitalFootprintCardInner({ footprint, jobId }: DigitalFootprintCardProps) {
  const hasData = footprint.has_data !== false;

  return (
    <div className="dash-card p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2 rounded-lg ${hasData ? "bg-indigo-50 text-indigo-700" : "bg-gray-50 text-gray-400"}`}>
          <span className="material-symbols-outlined text-xl">fingerprint</span>
        </div>
        <div className="flex-1 min-w-0">
          <h3
            className="text-base font-medium text-gray-900 truncate"
            style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
          >
            Digital Footprint
          </h3>
        </div>
        {hasData && (
          <Link
            href={`/dashboard/${jobId}/digital-footprint`}
            className="text-xs font-medium text-[#1A73E8] hover:underline flex items-center gap-1 shrink-0"
          >
            Details
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </Link>
        )}
      </div>

      {!hasData ? (
        /* Empty state */
        <div className="py-8 flex flex-col items-center text-center">
          <div className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center mb-3">
            <span className="material-symbols-outlined text-xl text-gray-300">public_off</span>
          </div>
          <p className="text-sm font-medium text-gray-500 mb-1">Engine Not Available</p>
          <p className="text-xs text-gray-400 max-w-[220px]">
            Digital footprint analysis was not included in this run. StackOverflow, blog, and community presence data was not evaluated.
          </p>
        </div>
      ) : (
        /* Key-value rows */
        <div className="space-y-0">
          {METRICS.map(({ key, label, format }) => {
            const raw = footprint[key];
            let display: string;
            if (format === "score" && typeof raw === "number") {
              display = raw.toFixed(1);
            } else if (typeof raw === "number") {
              display = raw.toFixed(1);
            } else {
              display = String(raw ?? "—");
            }

            const isHighlight = key === "seo_tier";

            return (
              <div
                key={key}
                className="py-2 border-b border-dashed border-[#DADCE0]/50 flex justify-between items-center last:border-b-0"
              >
                <span className="text-xs text-gray-500">{label}</span>
                <span
                  className={`text-sm font-mono ${
                    isHighlight ? "font-bold text-indigo-600" : "text-gray-900"
                  }`}
                >
                  {display}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const DigitalFootprintCard = memo(DigitalFootprintCardInner);
export default DigitalFootprintCard;
